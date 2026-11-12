"""Analiza un video propio con core.pipeline (reemplaza parte del notebook 03).

Corre el pipeline completo (MediaPipe + motor de riesgo) sobre un video local y
escribe resultados/video.md (% de rostro detectado, niveles y motivos) y
resultados/video.png (curvas de EAR y nivel en el tiempo). Solo se guardan
métricas numéricas: nunca fotogramas ni recortes de la cara.

Uso (desde la raíz del repositorio):
    python scripts/experimentos/analizar_video.py --video data/videos/prueba.mp4
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

NIVELES = ["NORMAL", "BAJO", "MEDIO", "ALTO"]


def resumir(df: pd.DataFrame) -> dict:
    """Cifras principales a partir del DataFrame de core.pipeline.analizar_video."""
    n = len(df)
    activo = df[~df["calibrando"]]
    pct_rostro = 100.0 * float(df["rostro"].mean()) if n else 0.0
    niveles = {k: (100.0 * float((activo["nivel"] == k).mean()) if len(activo) else 0.0)
               for k in NIVELES}
    motivos: dict[str, int] = {}
    for cadena in activo["motivos"]:
        for m in filter(None, str(cadena).split(",")):
            motivos[m] = motivos.get(m, 0) + 1
    duracion = float(df["t"].max()) if n else 0.0
    return {"fotogramas": n, "duracion_s": duracion,
            "fps": (n - 1) / duracion if duracion > 0 else 0.0,
            "pct_rostro": pct_rostro, "calibracion_s": float(df.loc[df["calibrando"], "t"].max())
            if df["calibrando"].any() else 0.0,
            "pct_nivel": niveles, "motivos": motivos, "n_activos": len(activo),
            "emergencia": bool(df["emergencia"].any())}


def escribir_md(r: dict, video: str, ruta: Path) -> None:
    lineas = [
        "# Análisis de un video propio", "",
        f"Video: `{video}` ({r['fotogramas']} fotogramas, {r['duracion_s']:.1f} s, "
        f"≈{r['fps']:.1f} fps). No se guardan fotogramas, solo métricas.", "",
        f"- **Rostro detectado:** {r['pct_rostro']:.1f} % de los fotogramas.",
        f"- **Calibración:** primeros {r['calibracion_s']:.1f} s (excluidos de niveles y motivos).",
        f"- **Emergencia:** {'sí' if r['emergencia'] else 'no'}.", "",
        "## Tiempo por nivel (tras calibrar)", "", "| Nivel | % de fotogramas |", "|---|---:|",
    ]
    lineas += [f"| {k} | {v:.1f} |" for k, v in r["pct_nivel"].items()]
    lineas += ["", "## Motivos", ""]
    if r["motivos"]:
        lineas += ["| Motivo | Fotogramas | % |", "|---|---:|---:|"]
        for m, c in sorted(r["motivos"].items(), key=lambda kv: -kv[1]):
            lineas.append(f"| {m} | {c} | {100 * c / max(r['n_activos'], 1):.1f} |")
    else:
        lineas.append("Ningún motivo de riesgo activo.")
    lineas.append("")
    ruta.write_text("\n".join(lineas), encoding="utf-8")


def escribir_png(df: pd.DataFrame, ruta: Path) -> None:
    t = df["t"].to_numpy()
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 5), sharex=True, constrained_layout=True,
                                 height_ratios=[3, 2])
    a1.plot(t, df["ear"].astype(float), color="#1f77b4", lw=1, label="EAR")
    a1.plot(t, df["ear_umbral"].astype(float), color="#d62728", lw=1.2, ls="--", label="Umbral")
    sin_rostro = ~df["rostro"].astype(bool).to_numpy()
    a1.fill_between(t, 0, 1, where=sin_rostro, color="0.7", alpha=0.5,
                    transform=a1.get_xaxis_transform(), label="Sin rostro")
    a1.set_ylabel("EAR")
    a1.set_title("Apertura ocular (EAR) y rostro detectado")
    a1.legend(loc="upper right", ncols=3, fontsize=8)
    nivel = df["nivel"].map(NIVELES.index).to_numpy()
    a2.step(t, nivel, where="post", color="#ff7f0e")
    if df["calibrando"].any():
        a2.axvspan(0, float(df.loc[df["calibrando"], "t"].max()), color="0.85", label="Calibración")
        a2.legend(loc="upper right", fontsize=8)
    a2.set_yticks(range(4), NIVELES)
    a2.set_ylabel("Nivel de riesgo")
    a2.set_xlabel("Tiempo (s)")
    for ax in (a1, a2):
        ax.grid(alpha=0.3)
    fig.savefig(ruta, dpi=150)
    plt.close(fig)


def main(argv: list[str] | None = None) -> dict:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--video", type=Path, required=True, help="ruta del video propio")
    p.add_argument("--max-segundos", type=float, default=None)
    p.add_argument("--salida", type=Path, default=ROOT / "resultados")
    args = p.parse_args(argv)
    if not args.video.is_file():
        p.error(f"no existe el video {args.video}")

    from core.pipeline import analizar_video
    df = analizar_video(args.video, max_segundos=args.max_segundos)
    if df.empty:
        p.error("el video no tiene fotogramas legibles")
    r = resumir(df)
    args.salida.mkdir(parents=True, exist_ok=True)
    nombre = args.video.name
    escribir_md(r, nombre, args.salida / "video.md")
    escribir_png(df, args.salida / "video.png")
    print(f"{nombre}: rostro {r['pct_rostro']:.1f} %, niveles {r['pct_nivel']}, motivos {r['motivos']}")
    return r


if __name__ == "__main__":
    main()
