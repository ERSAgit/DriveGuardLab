"""Barrido de umbrales del microsueño: detección vs. falsas alarmas.

Barre microsueno_s x factor_ear con conductores sintéticos aleatorios (semilla
fija). Los mismos conductores se reutilizan en todas las combinaciones, así las
diferencias vienen solo de los umbrales. No modifica los valores por defecto de
ConfigRiesgo: crea una instancia por combinación.

Uso (desde la raíz del repositorio):
    python scripts/experimentos/umbrales.py --conductores 20 --semilla 42 --salida resultados
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

from core.config import ConfigRiesgo  # noqa: E402
from core.simulacion import ejecutar, generar_mediciones  # noqa: E402

MICROSUENO_S = [0.5, 1.0, 1.5, 2.0]
FACTOR_EAR = [0.65, 0.75, 0.85]
T_CIERRE = 20.0            # inicio del cierre en el escenario "microsueno"
FALSAS_MAX_PCT = 5.0       # tope de falsas alarmas para recomendar


def muestrear_conductores(n: int, semilla: int) -> list[dict]:
    """Parámetros aleatorios y reproducibles de n conductores sintéticos."""
    rng = np.random.default_rng(semilla)
    conductores = []
    for i in range(n):
        conductores.append({
            "conductor": i,
            "semilla": int(rng.integers(0, 2**31 - 1)),
            "ear_base": float(rng.uniform(0.25, 0.38)),
            "ruido": float(rng.uniform(0.005, 0.025)),
            "parpadeo_cada_s": float(rng.uniform(3.0, 6.0)),
            "dur_parpadeo": float(rng.uniform(0.10, 0.70)),
            "dur_cierre": float(rng.uniform(1.2, 3.0)),
        })
    return conductores


def _mediciones(c: dict, escenario: str) -> list:
    extra = {"dur_cierre": c["dur_cierre"]} if escenario == "microsueno" else {}
    return generar_mediciones(escenario, semilla=c["semilla"], ear_base=c["ear_base"],
                              ruido=c["ruido"], parpadeo_cada_s=c["parpadeo_cada_s"],
                              dur_parpadeo=c["dur_parpadeo"], **extra)


def evaluar(conductores: list[dict]) -> pd.DataFrame:
    """Una fila por combinación y conductor."""
    datos = [(c, _mediciones(c, "microsueno"), _mediciones(c, "normal")) for c in conductores]
    filas = []
    for ms in MICROSUENO_S:
        for fe in FACTOR_EAR:
            cfg = ConfigRiesgo(microsueno_s=ms, factor_ear=fe)
            for c, med_micro, med_normal in datos:
                df = ejecutar(med_micro, cfg)
                alto = df[(df["t"] >= T_CIERRE) & (df["nivel"] == "ALTO")]
                detectado = not alto.empty
                latencia = float(alto["t"].iloc[0] - T_CIERRE) if detectado else np.nan
                falsa = bool((ejecutar(med_normal, cfg)["nivel"] == "ALTO").any())
                filas.append({"microsueno_s": ms, "factor_ear": fe,
                              "conductor": c["conductor"], "dur_cierre": c["dur_cierre"],
                              "dur_parpadeo": c["dur_parpadeo"],
                              "detectado": detectado, "latencia_s": latencia,
                              "falsa_alarma": falsa})
    return pd.DataFrame(filas)


def agregar(detalle: pd.DataFrame) -> pd.DataFrame:
    """Una fila por combinación con porcentajes y latencia media."""
    g = detalle.groupby(["microsueno_s", "factor_ear"])
    res = g.agg(deteccion_pct=("detectado", "mean"),
                falsas_alarmas_pct=("falsa_alarma", "mean"),
                latencia_media_s=("latencia_s", "mean")).reset_index()
    res["deteccion_pct"] = (res["deteccion_pct"] * 100).round(1)
    res["falsas_alarmas_pct"] = (res["falsas_alarmas_pct"] * 100).round(1)
    res["latencia_media_s"] = res["latencia_media_s"].round(2)
    res.insert(2, "n_conductores", int(detalle["conductor"].nunique()))
    return res


def recomendar(res: pd.DataFrame) -> pd.Series:
    """Máxima detección con falsas alarmas <= tope; desempata por menos falsas
    alarmas y menor latencia. Si ninguna cumple, la de menos falsas alarmas."""
    ok = res[res["falsas_alarmas_pct"] <= FALSAS_MAX_PCT]
    if ok.empty:
        return res.sort_values(["falsas_alarmas_pct", "deteccion_pct"],
                               ascending=[True, False]).iloc[0]
    return ok.sort_values(["deteccion_pct", "falsas_alarmas_pct", "latencia_media_s"],
                          ascending=[False, True, True]).iloc[0]


def escribir_md(res: pd.DataFrame, rec: pd.Series, conductores: list[dict],
                semilla: int, ruta: Path) -> None:
    defecto = ConfigRiesgo()
    fila_def = res[(res["microsueno_s"] == defecto.microsueno_s)
                   & (res["factor_ear"] == defecto.factor_ear)]
    n = len(conductores)
    lineas = [
        "# Barrido de umbrales del microsueño", "",
        f"{n} conductores sintéticos, semilla {semilla}. Parámetros aleatorios: EAR base "
        "0.25-0.38, ruido 0.005-0.025, parpadeo normal de 0.10 a 0.70 s cada 3-6 s y "
        "cierre de microsueño de 1.2 a 3.0 s (inicio en t=20 s).", "",
        "- **Detección:** % de escenarios `microsueno` que llegan a ALTO con t >= 20 s.",
        "- **Falsas alarmas:** % de escenarios `normal` que llegan a ALTO.", "",
        "| microsueno_s | factor_ear | Detección (%) | Falsas alarmas (%) | Latencia media (s) |",
        "|---:|---:|---:|---:|---:|",
    ]
    for _, r in res.iterrows():
        lat = "-" if pd.isna(r["latencia_media_s"]) else f"{r['latencia_media_s']:.2f}"
        lineas.append(f"| {r['microsueno_s']:.1f} | {r['factor_ear']:.2f} | "
                      f"{r['deteccion_pct']:.1f} | {r['falsas_alarmas_pct']:.1f} | {lat} |")
    texto = (f"Con un tope de {FALSAS_MAX_PCT:.0f} % de falsas alarmas, la combinación "
             f"recomendada es **microsueno_s = {rec['microsueno_s']:.1f} s y factor_ear = "
             f"{rec['factor_ear']:.2f}**: detecta {rec['deteccion_pct']:.1f} % de los "
             f"microsueños con {rec['falsas_alarmas_pct']:.1f} % de falsas alarmas")
    if not pd.isna(rec["latencia_media_s"]):
        texto += f" y una latencia media de {rec['latencia_media_s']:.2f} s"
    texto += ". "
    if not fila_def.empty:
        d = fila_def.iloc[0]
        texto += (f"Los valores por defecto ({defecto.microsueno_s} s y {defecto.factor_ear}) "
                  f"dan {d['deteccion_pct']:.1f} % de detección y "
                  f"{d['falsas_alarmas_pct']:.1f} % de falsas alarmas. ")
    texto += ("Umbrales de tiempo cortos detectan más, pero convierten parpadeos largos en "
              "falsas alarmas; los largos pierden los cierres más breves. Es un resultado "
              "sobre datos sintéticos: no cambia los valores por defecto sin confirmación.")
    lineas += ["", "## Recomendación", "", texto, ""]
    ruta.write_text("\n".join(lineas), encoding="utf-8")


def escribir_png(res: pd.DataFrame, ruta: Path) -> None:
    fig, ejes = plt.subplots(1, 2, figsize=(10, 4), constrained_layout=True)
    for ax, col, titulo, cmap in (
            (ejes[0], "deteccion_pct", "Detección (%)", "Blues"),
            (ejes[1], "falsas_alarmas_pct", "Falsas alarmas (%)", "Oranges")):
        m = res.pivot(index="factor_ear", columns="microsueno_s", values=col)
        im = ax.imshow(m.values, cmap=cmap, vmin=0, vmax=100, aspect="auto", origin="lower")
        ax.set_xticks(range(len(m.columns)), [f"{x:.1f}" for x in m.columns])
        ax.set_yticks(range(len(m.index)), [f"{x:.2f}" for x in m.index])
        ax.set_xlabel("microsueno_s (s)")
        ax.set_ylabel("factor_ear")
        ax.set_title(titulo)
        for i in range(m.shape[0]):
            for j in range(m.shape[1]):
                v = m.values[i, j]
                ax.text(j, i, f"{v:.0f}", ha="center", va="center",
                        color="white" if v > 60 else "black")
        fig.colorbar(im, ax=ax, shrink=0.85)
    fig.savefig(ruta, dpi=150)
    plt.close(fig)


def main(argv: list[str] | None = None) -> pd.DataFrame:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--conductores", type=int, default=20)
    p.add_argument("--semilla", type=int, default=42)
    p.add_argument("--salida", type=Path, default=ROOT / "resultados")
    args = p.parse_args(argv)
    if args.conductores < 1:
        p.error("--conductores debe ser >= 1")

    conductores = muestrear_conductores(args.conductores, args.semilla)
    detalle = evaluar(conductores)
    res = agregar(detalle)
    rec = recomendar(res)

    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)
    res.to_csv(salida / "umbrales.csv", index=False)
    detalle.to_csv(salida / "umbrales_detalle.csv", index=False)
    escribir_md(res, rec, conductores, args.semilla, salida / "umbrales.md")
    escribir_png(res, salida / "umbrales.png")
    print(res.to_string(index=False))
    print(f"\nRecomendada: microsueno_s={rec['microsueno_s']}, factor_ear={rec['factor_ear']}")
    return res


if __name__ == "__main__":
    main()
