"""Compara EAR y CNN para detectar ojos cerrados en un video etiquetado.

Recorre el video una sola vez: el método EAR es la decisión del motor de riesgo
(EAR bajo el umbral calibrado) y el método CNN es core.ojos_cnn.ClasificadorOjos
sobre los recortes de ambos ojos (probabilidad media de cerrado > 0.5). La
etiqueta real viene de los intervalos de tiempo en que los ojos están cerrados.
Se excluyen los fotogramas sin rostro y los de calibración. Solo se guardan
métricas, nunca fotogramas.

Uso (desde la raíz del repositorio):
    python scripts/experimentos/ear_vs_cnn.py --video data/videos/ojos_etiquetado.mp4 \
        --cerrado 10-20 --cerrado 30-35
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.metricas import reporte  # noqa: E402

INTERVALOS_DEFECTO = ["10-20", "30-35"]


def parsear_intervalos(textos: list[str]) -> list[tuple[float, float]]:
    """'10-20' -> (10.0, 20.0). Valida que inicio < fin."""
    out = []
    for s in textos:
        try:
            a, b = (float(x) for x in s.split("-"))
        except ValueError:
            raise ValueError(f"Intervalo inválido '{s}': use inicio-fin en segundos, p. ej. 10-20") from None
        if not 0 <= a < b:
            raise ValueError(f"Intervalo inválido '{s}': se exige 0 <= inicio < fin")
        out.append((a, b))
    return out


def etiquetar(t, intervalos: list[tuple[float, float]]) -> np.ndarray:
    """0 = cerrado (dentro de algún intervalo), 1 = abierto."""
    t = np.asarray(t, dtype=float)
    cerrado = np.zeros(len(t), dtype=bool)
    for a, b in intervalos:
        cerrado |= (t >= a) & (t < b)
    return np.where(cerrado, 0, 1)


def procesar_video(video: Path, clasificador, max_segundos: float | None = None) -> pd.DataFrame:
    """Una fila por fotograma: t, rostro, calibrando, ear_cerrado, prob_cnn_cerrado."""
    import cv2

    from core.landmarks import OJO_DERECHO, OJO_IZQUIERDO, DetectorRostro, recorte_ojo
    from core.riesgo import Medicion, MotorRiesgo

    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise ValueError(f"No se pudo abrir el video {video}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    detector, motor = DetectorRostro(modo="video"), MotorRiesgo()
    filas, i = [], 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            t = i / fps
            i += 1
            if max_segundos and t > max_segundos:
                break
            rostro = detector.procesar(frame, int(t * 1000))
            if rostro is None:
                e = motor.actualizar(Medicion(t=t, rostro=False))
                filas.append({"t": t, "rostro": False, "calibrando": e.calibrando,
                              "ear_cerrado": False, "prob_cnn_cerrado": np.nan})
                continue
            e = motor.actualizar(Medicion(t=t, rostro=True, ear=rostro.ear, mar=rostro.mar,
                                          pitch=rostro.pitch, yaw=rostro.yaw))
            recortes = [r for r in (recorte_ojo(frame, rostro.puntos, OJO_DERECHO),
                                    recorte_ojo(frame, rostro.puntos, OJO_IZQUIERDO)) if r is not None]
            prob = float(clasificador.prob_cerrado(recortes).mean()) if recortes else np.nan
            filas.append({"t": t, "rostro": True, "calibrando": e.calibrando,
                          "ear_cerrado": bool(e.ojos_cerrados), "prob_cnn_cerrado": prob})
    finally:
        cap.release()
        detector.cerrar()
    return pd.DataFrame(filas)


def tramos_ear(df: pd.DataFrame, min_s: float = 1.0) -> list[tuple[float, float]]:
    """Tramos continuos (>= min_s) en que el método EAR ve los ojos cerrados (para contrastar etiquetas)."""
    tramos, ini, ant = [], None, None
    for t, c in zip(df["t"], df["ear_cerrado"] & df["rostro"] & ~df["calibrando"]):
        if c and ini is None:
            ini = t
        if not c and ini is not None:
            tramos.append((ini, ant))
            ini = None
        ant = t
    if ini is not None:
        tramos.append((ini, ant))
    return [(a, b) for a, b in tramos if b - a >= min_s]


def evaluar(df: pd.DataFrame, intervalos: list[tuple[float, float]]) -> dict:
    """Métricas de EAR y CNN sobre los fotogramas con rostro y fuera de calibración."""
    util = df[df["rostro"] & ~df["calibrando"] & df["prob_cnn_cerrado"].notna()]
    y = etiquetar(util["t"], intervalos)
    pred = {"EAR": np.where(util["ear_cerrado"], 0, 1),
            "CNN": np.where(util["prob_cnn_cerrado"] > 0.5, 0, 1)}
    return {"n_total": len(df), "n_util": len(util), "n_sin_rostro": int((~df["rostro"]).sum()),
            "n_calibracion": int(df["calibrando"].sum()),
            "n_cerrado": int((y == 0).sum()), "n_abierto": int((y == 1).sum()),
            "metodos": {k: reporte(y, p) for k, p in pred.items()},
            "tramos_ear": tramos_ear(df),
            "prob_cnn_media": {"cerrado": float(util.loc[y == 0, "prob_cnn_cerrado"].mean()),
                               "abierto": float(util.loc[y == 1, "prob_cnn_cerrado"].mean())}}


def escribir_md(r: dict, video: str, intervalos, ruta: Path) -> None:
    ints = ", ".join(f"{a:g}-{b:g} s" for a, b in intervalos)
    lineas = [
        "# EAR vs CNN en un video etiquetado", "",
        f"Video: `{video}`. Ojos cerrados en: {ints}; abiertos el resto. Se evalúan "
        f"{r['n_util']} de {r['n_total']} fotogramas ({r['n_cerrado']} cerrados, {r['n_abierto']} abiertos); "
        f"excluidos: {r['n_sin_rostro']} sin rostro y {r['n_calibracion']} de calibración.", "",
        "| Método | Exactitud | F1 cerrado | F1 abierto | Recall cerrado | Precisión cerrado |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for nombre, m in r["metodos"].items():
        c, a = m["por_clase"]
        lineas.append(f"| {nombre} | {m['exactitud'] * 100:.1f} % | {c['f1']:.3f} | {a['f1']:.3f} | "
                      f"{c['recall']:.3f} | {c['precision']:.3f} |")
    lineas += ["", "## Matrices de confusión (filas = real, columnas = predicho)", ""]
    for nombre, m in r["metodos"].items():
        mm = m["matriz"]
        lineas += [f"**{nombre}**", "", "| | pred. cerrado | pred. abierto |", "|---|---:|---:|",
                   f"| real cerrado | {mm[0, 0]} | {mm[0, 1]} |", f"| real abierto | {mm[1, 0]} | {mm[1, 1]} |", ""]
    tr = ", ".join(f"{a:.1f}-{b:.1f} s" for a, b in r["tramos_ear"]) or "ninguno"
    pc = r["prob_cnn_media"]
    lineas += ["## Contraste con la señal del video", "",
               f"- Tramos (>= 1 s) en que EAR detecta ojos cerrados: {tr}. Si no coinciden con los "
               "intervalos etiquetados, revise las etiquetas o el video antes de interpretar las cifras.",
               f"- Probabilidad media de cerrado de la CNN: {pc['cerrado']:.2f} en tramos etiquetados cerrados "
               f"y {pc['abierto']:.2f} en abiertos (una CNN útil separa ambos valores).", ""]
    ex = {k: m["exactitud"] for k, m in r["metodos"].items()}
    mejor = max(ex, key=ex.get) if len(set(ex.values())) > 1 else "ninguno (empate)"
    degenerados = [k for k, m in r["metodos"].items()
                   if min(m["por_clase"][0]["recall"], m["por_clase"][1]["recall"]) == 0.0]
    lineas += ["## Lectura", "",
               f"Mayor exactitud: **{mejor}** (EAR {ex['EAR'] * 100:.1f} %, CNN {ex['CNN'] * 100:.1f} %)."]
    if degenerados:
        lineas.append(f"**Atención:** {', '.join(degenerados)} predice una sola clase (recall 0 en la otra); "
                      "su F1 de la clase que acierta es trivial y no indica que distinga ojos abiertos de cerrados.")
    lineas += ["La CNN se entrenó con capturas de la misma persona y entorno que el video, así que su "
               "resultado debería ser optimista, no una evaluación con otros conductores. Las etiquetas "
               "por intervalo no incluyen parpadeos normales dentro de los tramos abiertos ni la "
               "transición al cerrar o abrir los ojos, lo que penaliza a ambos métodos.", ""]
    ruta.write_text("\n".join(lineas), encoding="utf-8")


def main(argv: list[str] | None = None) -> dict:
    from core.config import CNN_OJOS_PATH
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--video", type=Path, default=ROOT / "data" / "videos" / "ojos_etiquetado.mp4")
    p.add_argument("--cerrado", action="append", metavar="INI-FIN",
                   help="intervalo con ojos cerrados en segundos (repetible); defecto 10-20 y 30-35")
    p.add_argument("--modelo", type=Path, default=CNN_OJOS_PATH)
    p.add_argument("--salida", type=Path, default=ROOT / "resultados")
    args = p.parse_args(argv)
    try:
        intervalos = parsear_intervalos(args.cerrado or INTERVALOS_DEFECTO)
    except ValueError as exc:
        p.error(str(exc))
    if not args.video.is_file():
        p.error(f"no existe el video {args.video}")
    if not args.modelo.is_file():
        p.error(f"no existe {args.modelo}; entrene antes con scripts/entrenar_cnn_ojos.py")

    from core.ojos_cnn import ClasificadorOjos
    df = procesar_video(args.video, ClasificadorOjos(args.modelo))
    r = evaluar(df, intervalos)
    if r["n_util"] == 0:
        p.error("ningún fotograma útil (¿sin rostro o todo en calibración?)")
    args.salida.mkdir(parents=True, exist_ok=True)
    escribir_md(r, args.video.name, intervalos, args.salida / "ear_vs_cnn.md")
    for k, m in r["metodos"].items():
        print(f"{k}: exactitud {m['exactitud']:.3f}, F1 cerrado {m['por_clase'][0]['f1']:.3f}, "
              f"F1 abierto {m['por_clase'][1]['f1']:.3f}")
    return r


if __name__ == "__main__":
    main()
