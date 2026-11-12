"""Entrena la CNN de ojos abiertos/cerrados con recortes propios (reemplaza el notebook 04).

Lee data/ojos/**/abiertos y **/cerrados (PNG/JPG), reparte cada clase en bloques
temporales contiguos 70/15/15 (entrenamiento/validación/prueba) para que
fotogramas casi idénticos no caigan en conjuntos distintos, entrena la red de
core/ojos_cnn.py con semilla fija y guarda models/cnn_ojos.pt (el modelo
anterior se copia a cnn_ojos.prev.pt la primera vez). Escribe
resultados/cnn.md y resultados/cnn_curvas.png. Solo se guardan métricas.

Uso (desde la raíz del repositorio):
    python scripts/entrenar_cnn_ojos.py --epocas 10 --semilla 42
"""
from __future__ import annotations

import argparse
import copy
import random
import re
import shutil
import sys
import time
from pathlib import Path

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.ojos_cnn import CLASES, TAM, ClasificadorOjos, crear_cnn, preparar  # noqa: E402
from scripts.metricas import reporte  # noqa: E402

CARPETA_CLASE = {"cerrados": 0, "abiertos": 1}     # 0 = cerrado, 1 = abierto (core.ojos_cnn)
EXTENSIONES = {".png", ".jpg", ".jpeg"}
_PATRON = re.compile(r"_(\d+)_(\d+)\.[a-z]+$", re.IGNORECASE)


def _clave_orden(ruta: Path):
    """Orden temporal por el sello de tiempo del nombre; si no existe, por nombre."""
    m = _PATRON.search(ruta.name)
    return (0, int(m.group(1)), int(m.group(2)), ruta.name) if m else (1, 0, 0, ruta.name)


def cargar_recortes(datos: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Devuelve (X uint8 N×64×64, y, orden) con las clases ordenadas en el tiempo.

    `orden` es la posición temporal dentro de su clase (para particionar por bloques)."""
    xs, ys, ordenes = [], [], []
    for carpeta, clase in CARPETA_CLASE.items():
        rutas = sorted((p for d in Path(datos).rglob(carpeta) if d.is_dir()
                        for p in d.iterdir() if p.suffix.lower() in EXTENSIONES), key=_clave_orden)
        for i, ruta in enumerate(rutas):
            img = cv2.imread(str(ruta), cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue
            if img.shape != (TAM, TAM):
                img = cv2.resize(img, (TAM, TAM), interpolation=cv2.INTER_AREA)
            xs.append(img)
            ys.append(clase)
            ordenes.append(i / max(len(rutas) - 1, 1))
    if not xs:
        raise FileNotFoundError(f"No hay recortes en {datos}/**/abiertos|cerrados")
    return np.stack(xs), np.array(ys), np.array(ordenes)


def particionar_bloques(y: np.ndarray, orden: np.ndarray,
                        fracciones=(0.70, 0.15, 0.15)) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Índices (train, val, test): por clase, tramos contiguos en el tiempo."""
    a, b = fracciones[0], fracciones[0] + fracciones[1]
    out = [[], [], []]
    for clase in np.unique(y):
        idx = np.where(y == clase)[0]
        idx = idx[np.argsort(orden[idx], kind="stable")]
        n = len(idx)
        cortes = (0, int(round(n * a)), int(round(n * b)), n)
        for k in range(3):
            out[k].extend(idx[cortes[k]:cortes[k + 1]].tolist())
    return tuple(np.array(sorted(o)) for o in out)


def _jitter(x, gen):
    """Aumento leve: brillo y contraste aleatorios (sobre el tensor normalizado)."""
    import torch
    n = x.shape[0]
    contraste = 1 + 0.3 * (torch.rand(n, 1, 1, 1, generator=gen) - 0.5) * 2
    brillo = 0.2 * (torch.rand(n, 1, 1, 1, generator=gen) - 0.5) * 2
    return (x * contraste + brillo).clamp(-1, 1)


def entrenar(X, y, idx_tr, idx_va, epocas: int, semilla: int, lote: int = 32) -> tuple[dict, list[dict]]:
    """Devuelve (mejor state_dict según exactitud de validación, historial por época)."""
    import torch
    from torch import nn

    random.seed(semilla)
    np.random.seed(semilla)
    torch.manual_seed(semilla)
    gen = torch.Generator().manual_seed(semilla)
    modelo = crear_cnn()
    opt = torch.optim.Adam(modelo.parameters(), lr=1e-3)
    perdida = nn.CrossEntropyLoss()
    x_tr, y_tr = preparar(list(X[idx_tr])), torch.from_numpy(y[idx_tr]).long()
    x_va, y_va = preparar(list(X[idx_va])), torch.from_numpy(y[idx_va]).long()

    historial, mejor, mejor_estado = [], (-1.0, 0.0), None
    for ep in range(1, epocas + 1):
        modelo.train()
        perm = torch.randperm(len(x_tr), generator=gen)
        suma, aciertos = 0.0, 0
        for i in range(0, len(perm), lote):
            b = perm[i:i + lote]
            xb, yb = _jitter(x_tr[b], gen), y_tr[b]
            opt.zero_grad()
            salida = modelo(xb)
            loss = perdida(salida, yb)
            loss.backward()
            opt.step()
            suma += loss.item() * len(b)
            aciertos += int((salida.argmax(1) == yb).sum())
        modelo.eval()
        with torch.no_grad():
            sv = modelo(x_va)
            loss_va = perdida(sv, y_va).item()
            acc_va = float((sv.argmax(1) == y_va).float().mean())
        historial.append({"epoca": ep, "loss_train": suma / len(x_tr), "acc_train": aciertos / len(x_tr),
                          "loss_val": loss_va, "acc_val": acc_va})
        if (acc_va, -loss_va) > (mejor[0], -mejor[1]):
            mejor, mejor_estado = (acc_va, loss_va), copy.deepcopy(modelo.state_dict())
    return mejor_estado, historial


def guardar_modelo(estado: dict, ruta: Path, meta: dict) -> Path | None:
    """Guarda el checkpoint; la primera vez copia el modelo previo a <nombre>.prev.pt."""
    import torch
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    respaldo = None
    if ruta.exists():
        respaldo = ruta.with_name(ruta.stem + ".prev" + ruta.suffix)
        if not respaldo.exists():
            shutil.copy2(ruta, respaldo)
    torch.save({"modelo": estado, "clases": CLASES, **meta}, ruta)
    return respaldo


def medir_ms(ruta_modelo: Path, X: np.ndarray, max_n: int = 200) -> float:
    """Mediana de ms por recorte (batch de 1, CPU) con el modelo guardado."""
    clf = ClasificadorOjos(ruta_modelo)
    muestras = list(X[:max_n])
    clf.prob_cerrado(muestras[:1])                       # calentamiento
    tiempos = []
    for r in muestras:
        t0 = time.perf_counter()
        clf.prob_cerrado([r])
        tiempos.append((time.perf_counter() - t0) * 1000)
    return float(np.median(tiempos))


def escribir_md(rep: dict, historial: list[dict], tamanos: dict, ms: float, semilla: int,
                datos: str, ruta: Path) -> None:
    m = rep["matriz"]
    lineas = [
        "# CNN de ojos abiertos/cerrados", "",
        f"Recortes propios de `{datos}`, semilla {semilla}, {len(historial)} épocas, Adam (lr 1e-3), "
        "lote 32. Partición por bloques temporales contiguos de cada clase (70/15/15): "
        f"entrenamiento {tamanos['train']}, validación {tamanos['val']}, prueba {tamanos['test']}. "
        "Se guarda el modelo con mejor exactitud de validación.", "",
        f"- **Exactitud (prueba):** {rep['exactitud'] * 100:.1f} % sobre {rep['n']} recortes.",
        f"- **Tiempo de inferencia:** {ms:.2f} ms por fotograma (un recorte, CPU, mediana).", "",
        "## F1 por clase (prueba)", "", "| Clase | Precisión | Recall | F1 | Soporte |", "|---|---:|---:|---:|---:|",
    ]
    for c, nombre in enumerate(CLASES):
        r = rep["por_clase"][c]
        lineas.append(f"| {nombre} | {r['precision']:.3f} | {r['recall']:.3f} | {r['f1']:.3f} | {r['soporte']} |")
    lineas += ["", "## Matriz de confusión (filas = real, columnas = predicho)", "",
               "| | pred. cerrado | pred. abierto |", "|---|---:|---:|",
               f"| **real cerrado** | {m[0, 0]} | {m[0, 1]} |", f"| **real abierto** | {m[1, 0]} | {m[1, 1]} |", "",
               "## Última época", "",
               f"Entrenamiento: pérdida {historial[-1]['loss_train']:.4f}, exactitud {historial[-1]['acc_train']:.3f}. "
               f"Validación: pérdida {historial[-1]['loss_val']:.4f}, exactitud {historial[-1]['acc_val']:.3f}.", "",
               "## Limitaciones", "",
               "Todos los recortes provienen de una misma persona y sesión de captura; aunque la partición "
               "temporal evita fotogramas casi idénticos entre conjuntos, la exactitud no anticipa el "
               "desempeño con otros conductores, cámaras o iluminación.", ""]
    ruta.write_text("\n".join(lineas), encoding="utf-8")


def escribir_png(historial: list[dict], ruta: Path) -> None:
    ep = [h["epoca"] for h in historial]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4), constrained_layout=True)
    a1.plot(ep, [h["loss_train"] for h in historial], marker="o", label="Entrenamiento")
    a1.plot(ep, [h["loss_val"] for h in historial], marker="s", label="Validación")
    a1.set_title("Pérdida")
    a2.plot(ep, [h["acc_train"] for h in historial], marker="o", label="Entrenamiento")
    a2.plot(ep, [h["acc_val"] for h in historial], marker="s", label="Validación")
    a2.set_title("Exactitud")
    for ax in (a1, a2):
        ax.set_xlabel("Época")
        ax.grid(alpha=0.3)
        ax.legend()
    fig.savefig(ruta, dpi=150)
    plt.close(fig)


def main(argv: list[str] | None = None) -> dict:
    from core.config import CNN_OJOS_PATH
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--datos", type=Path, default=ROOT / "data" / "ojos")
    p.add_argument("--salida", type=Path, default=ROOT / "resultados")
    p.add_argument("--modelo", type=Path, default=CNN_OJOS_PATH)
    p.add_argument("--epocas", type=int, default=10)
    p.add_argument("--semilla", type=int, default=42)
    p.add_argument("--lote", type=int, default=32)
    args = p.parse_args(argv)
    if args.epocas < 1:
        p.error("--epocas debe ser >= 1")

    X, y, orden = cargar_recortes(args.datos)
    idx_tr, idx_va, idx_te = particionar_bloques(y, orden)
    if min(len(idx_tr), len(idx_va), len(idx_te)) == 0 or len(np.unique(y[idx_tr])) < 2:
        p.error("datos insuficientes: se necesitan recortes de ambas clases en cada partición")
    estado, historial = entrenar(X, y, idx_tr, idx_va, args.epocas, args.semilla, args.lote)
    respaldo = guardar_modelo(estado, args.modelo, {"epocas": args.epocas, "semilla": args.semilla})

    clf = ClasificadorOjos(args.modelo)
    pred = (clf.prob_cerrado(list(X[idx_te])) <= 0.5).astype(int)   # 1 = abierto
    rep = reporte(y[idx_te], pred)
    ms = medir_ms(args.modelo, X[idx_te])

    args.salida.mkdir(parents=True, exist_ok=True)
    tamanos = {"train": len(idx_tr), "val": len(idx_va), "test": len(idx_te)}
    escribir_md(rep, historial, tamanos, ms, args.semilla, str(args.datos.name), args.salida / "cnn.md")
    escribir_png(historial, args.salida / "cnn_curvas.png")
    print(f"Exactitud prueba {rep['exactitud']:.3f}, F1 {[round(c['f1'], 3) for c in rep['por_clase']]}, "
          f"{ms:.2f} ms/fotograma; modelo en {args.modelo}" + (f" (respaldo {respaldo.name})" if respaldo else ""))
    return {"reporte": rep, "historial": historial, "ms": ms, "tamanos": tamanos}


if __name__ == "__main__":
    main()
