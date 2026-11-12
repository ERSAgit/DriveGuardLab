"""Barrido de umbrales del motor de riesgo (microsueno_s x factor_ear).

Genera conductores sintéticos con parámetros aleatorios y mide, por cada
combinación de umbrales, la tasa de detección del microsueño y la tasa de
falsas alarmas en un escenario normal. No modifica los valores por defecto de
ConfigRiesgo: crea una instancia por combinación.

Uso: python scripts/experimentos/umbrales.py --conductores 20 --semilla 42 --salida resultados
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

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.config import ConfigRiesgo  # noqa: E402
from core.simulacion import ejecutar, generar_mediciones  # noqa: E402

MICROSUENO_S = [0.5, 1.0, 1.5, 2.0]
FACTOR_EAR = [0.65, 0.75, 0.85]
FPS = 15
T_INICIO_CIERRE = 20.0
FALSAS_ALARMAS_ACEPTABLES = 5.0


def generar_conductores(n: int, semilla: int) -> list[dict]:
    """Perfiles sintéticos con parámetros fisiológicos variados."""
    rng = np.random.default_rng(semilla)
    return [
        {
            "conductor_id": i + 1,
            "ear_base": float(rng.uniform(0.24, 0.36)),
            "ruido": float(rng.uniform(0.008, 0.02)),
            "parpadeo_cada_s": float(rng.uniform(3.0, 6.0)),
            "dur_parpadeo": float(rng.uniform(0.10, 0.70)),
            "dur_cierre": float(rng.uniform(1.2, 3.0)),
        }
        for i in range(n)
    ]


def generar_escenarios(conductores: list[dict], semilla: int) -> dict[tuple[int, str], list]:
    """Mediciones de los escenarios normal y microsueño para cada conductor."""
    mediciones = {}
    for c in conductores:
        cid = c["conductor_id"]
        base = {
            "fps": FPS,
            "semilla": semilla + cid,
            "ear_base": c["ear_base"],
            "parpadeo_cada_s": c["parpadeo_cada_s"],
            "ruido": c["ruido"],
            "dur_parpadeo": c["dur_parpadeo"],
        }
        mediciones[(cid, "normal")] = generar_mediciones("normal", **base)
        mediciones[(cid, "microsueno")] = generar_mediciones(
            "microsueno", dur_cierre=c["dur_cierre"], **base)
    return mediciones


def _primer_alto_por_microsueno(estados: pd.DataFrame) -> float | None:
    altos = estados[(estados["nivel"] == "ALTO") & (estados["t"] >= T_INICIO_CIERRE)
                    & estados["motivos"].str.contains("microsueno")]
    return None if altos.empty else float(altos["t"].iloc[0])


def _hay_alto(estados: pd.DataFrame) -> bool:
    return bool((estados["nivel"] == "ALTO").any())


def barrido(n_conductores: int, semilla: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Ejecuta el barrido y devuelve (detalle por conductor, resumen agregado)."""
    conductores = generar_conductores(n_conductores, semilla)
    mediciones = generar_escenarios(conductores, semilla)
    filas = []
    for microsueno_s in MICROSUENO_S:
        for factor_ear in FACTOR_EAR:
            config = ConfigRiesgo(microsueno_s=microsueno_s, factor_ear=factor_ear)
            for c in conductores:
                cid = c["conductor_id"]
                estado_micro = ejecutar(mediciones[(cid, "microsueno")], config)
                t_alto = _primer_alto_por_microsueno(estado_micro)
                estado_normal = ejecutar(mediciones[(cid, "normal")], config)
                filas.append({
                    "microsueno_s": microsueno_s,
                    "factor_ear": factor_ear,
                    "conductor_id": cid,
                    "deteccion_pct": 100.0 if t_alto is not None else 0.0,
                    "falsa_alarma_pct": 100.0 if _hay_alto(estado_normal) else 0.0,
                    "latencia_s": None if t_alto is None else t_alto - T_INICIO_CIERRE,
                    "ear_base": round(c["ear_base"], 4),
                    "ruido": round(c["ruido"], 4),
                    "dur_parpadeo": round(c["dur_parpadeo"], 4),
                    "dur_cierre": round(c["dur_cierre"], 4),
                })
    detalle = pd.DataFrame(filas)
    resumen = detalle.groupby(["microsueno_s", "factor_ear"], as_index=False).agg(
        deteccion_pct=("deteccion_pct", "mean"),
        falsa_alarma_pct=("falsa_alarma_pct", "mean"),
        latencia_s=("latencia_s", lambda s: s.mean(skipna=True) if s.notna().any() else np.nan),
        conductores=("conductor_id", "count"),
    )
    return detalle, resumen


def _recomendar(resumen: pd.DataFrame) -> pd.Series:
    candidatos = resumen[resumen["falsa_alarma_pct"] <= FALSAS_ALARMAS_ACEPTABLES].copy()
    if candidatos.empty:
        candidatos = resumen.copy()
    candidatos["dist_default"] = (candidatos["microsueno_s"] - 1.5).abs() + \
                                 (candidatos["factor_ear"] - 0.75).abs()
    candidatos = candidatos.sort_values(
        ["deteccion_pct", "falsa_alarma_pct", "dist_default"],
        ascending=[False, True, True])
    return candidatos.iloc[0]


def _tabla_md(resumen: pd.DataFrame) -> str:
    lineas = [
        "| microsueno_s | factor_ear | detección (%) | falsas alarmas (%) | latencia media (s) |",
        "| ---: | ---: | ---: | ---: | ---: |",
    ]
    for fila in resumen.itertuples(index=False):
        latencia = "—" if pd.isna(fila.latencia_s) else f"{fila.latencia_s:.2f}"
        lineas.append(
            f"| {fila.microsueno_s:.1f} | {fila.factor_ear:.2f} | "
            f"{fila.deteccion_pct:.1f} | {fila.falsa_alarma_pct:.1f} | {latencia} |")
    return "\n".join(lineas)


def escribir_salidas(detalle: pd.DataFrame, resumen: pd.DataFrame, salida: Path,
                     semilla: int, n_conductores: int) -> None:
    """Escribe umbrales.csv, umbrales.md y umbrales.png en la carpeta de salida."""
    salida.mkdir(parents=True, exist_ok=True)
    csv = pd.concat([
        detalle.assign(tipo="conductor"),
        resumen.assign(tipo="agregado", conductor_id=""),
    ], ignore_index=True)
    csv.to_csv(salida / "umbrales.csv", index=False)

    recomendado = _recomendar(resumen)
    por_defecto = resumen[(resumen["microsueno_s"] == 1.5)
                          & (resumen["factor_ear"] == 0.75)].iloc[0]

    texto = [
        "# Barrido de umbrales del motor de riesgo",
        "",
        f"- Conductores sintéticos: {n_conductores} (semilla {semilla}, {FPS} fps).",
        f"- Detección: escenario `microsueno` con nivel ALTO por `microsueno` para t >= {T_INICIO_CIERRE:.0f} s.",
        "- Falsa alarma: escenario `normal` (sin eventos) con nivel ALTO.",
        "- No se modificaron los valores por defecto de `ConfigRiesgo`.",
        "",
        _tabla_md(resumen),
        "",
        "## Recomendación",
        "",
        f"La combinación recomendada es **microsueno_s = {recomendado.microsueno_s:.1f} s** "
        f"y **factor_ear = {recomendado.factor_ear:.2f}**: detecta "
        f"{recomendado.deteccion_pct:.1f} % de los microsueños con "
        f"{recomendado.falsa_alarma_pct:.1f} % de falsas alarmas"
        + (f" y una latencia media de {recomendado.latencia_s:.2f} s."
           if not pd.isna(recomendado.latencia_s) else "."),
        "",
        f"Los valores por defecto (`microsueno_s = 1.5` s, `factor_ear = 0.75`) obtienen "
        f"{por_defecto.deteccion_pct:.1f} % de detección y "
        f"{por_defecto.falsa_alarma_pct:.1f} % de falsas alarmas. "
        "La recomendación surge de maximizar la detección entre las combinaciones con "
        f"falsas alarmas <= {FALSAS_ALARMAS_ACEPTABLES:.0f} %, prefiriendo los valores "
        "más cercanos a los defaults cuando hay empate. Si se desea adoptar la "
        "recomendación, el cambio debe hacerse de forma explícita en `core/config.py`.",
    ]
    (salida / "umbrales.md").write_text("\n".join(texto) + "\n", encoding="utf-8")

    piv_det = resumen.pivot(index="factor_ear", columns="microsueno_s",
                            values="deteccion_pct").reindex(index=FACTOR_EAR, columns=MICROSUENO_S)
    piv_fa = resumen.pivot(index="factor_ear", columns="microsueno_s",
                           values="falsa_alarma_pct").reindex(index=FACTOR_EAR, columns=MICROSUENO_S)

    fig, ejes = plt.subplots(1, 2, figsize=(11, 4.2))
    for ax, datos, titulo in (
            (ejes[0], piv_det, "Detección de microsueño (%)"),
            (ejes[1], piv_fa, "Falsas alarmas (%)")):
        imagen = ax.imshow(datos.values, vmin=0, vmax=100, cmap="RdYlGn", aspect="auto")
        ax.set_title(titulo)
        ax.set_xticks(range(len(MICROSUENO_S)), [f"{v:.1f}" for v in MICROSUENO_S])
        ax.set_yticks(range(len(FACTOR_EAR)), [f"{v:.2f}" for v in FACTOR_EAR])
        ax.set_xlabel("microsueno_s")
        ax.set_ylabel("factor_ear")
        for i in range(datos.shape[0]):
            for j in range(datos.shape[1]):
                ax.text(j, i, f"{datos.values[i, j]:.0f}", ha="center", va="center",
                        color="black", fontsize=10)
        fig.colorbar(imagen, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(salida / "umbrales.png", dpi=120, bbox_inches="tight")
    plt.close(fig)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--conductores", type=int, default=20,
                        help="número de conductores sintéticos (default: 20)")
    parser.add_argument("--semilla", type=int, default=42,
                        help="semilla aleatoria (default: 42)")
    parser.add_argument("--salida", type=Path, default=Path("resultados"),
                        help="carpeta de salida (default: resultados)")
    args = parser.parse_args(argv)

    detalle, resumen = barrido(args.conductores, args.semilla)
    escribir_salidas(detalle, resumen, args.salida, args.semilla, args.conductores)
    print(f"[OK] {len(MICROSUENO_S) * len(FACTOR_EAR)} combinaciones, "
          f"{args.conductores} conductores -> {args.salida}")


if __name__ == "__main__":
    main()
