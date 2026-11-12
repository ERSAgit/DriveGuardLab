"""Los 7 escenarios sintéticos de core.simulacion frente al motor de riesgo.

Reemplaza el notebook 03. Para cada escenario se ignoran las filas en
calibración y se reporta: nivel máximo, primer instante en que se alcanza,
motivos activos, si hubo emergencia y en qué instante. Usa ConfigRiesgo con sus
valores por defecto (no los modifica).

Uso (desde la raíz del repositorio):
    python scripts/experimentos/escenarios.py --semilla 42 --salida resultados
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.config import ConfigRiesgo  # noqa: E402
from core.simulacion import ESCENARIOS, ejecutar, generar_mediciones  # noqa: E402

NIVELES = ["NORMAL", "BAJO", "MEDIO", "ALTO"]


def resumir_escenario(nombre: str, df: pd.DataFrame) -> dict:
    """Resume la trayectoria del motor (DataFrame de core.simulacion.ejecutar)."""
    activo = df[~df["calibrando"]]
    if activo.empty:
        return {"escenario": nombre, "duracion_s": float(df["t"].max()), "nivel_max": "NORMAL",
                "t_nivel_max_s": None, "motivos": "", "emergencia": False, "t_emergencia_s": None}
    rango = activo["nivel"].map(NIVELES.index)
    nivel_max = NIVELES[int(rango.max())]
    t_max = float(activo.loc[activo["nivel"] == nivel_max, "t"].iloc[0])
    motivos: list[str] = []
    for cadena in activo["motivos"]:
        for m in filter(None, str(cadena).split(",")):
            if m not in motivos:
                motivos.append(m)
    emer = activo[activo["emergencia"]]
    return {"escenario": nombre, "duracion_s": round(float(df["t"].max()), 1),
            "nivel_max": nivel_max, "t_nivel_max_s": round(t_max, 2),
            "motivos": ",".join(motivos), "emergencia": not emer.empty,
            "t_emergencia_s": None if emer.empty else round(float(emer["t"].iloc[0]), 2)}


def ejecutar_escenarios(semilla: int = 42, config: ConfigRiesgo | None = None) -> pd.DataFrame:
    filas = []
    for nombre in ESCENARIOS:
        df = ejecutar(generar_mediciones(nombre, semilla=semilla), config)
        filas.append(resumir_escenario(nombre, df))
    return pd.DataFrame(filas)


def escribir_md(res: pd.DataFrame, semilla: int, ruta: Path) -> None:
    def f(v):
        return "-" if v is None or pd.isna(v) else f"{v:.2f}"

    lineas = [
        "# Escenarios sintéticos frente al motor de riesgo", "",
        f"Semilla {semilla}, `ConfigRiesgo` con valores por defecto. Se ignoran las filas "
        "en calibración (primeros segundos).", "",
        "| Escenario | Duración (s) | Nivel máximo | Primer instante (s) | Motivos | Emergencia | Instante emergencia (s) |",
        "|---|---:|:---:|---:|---|:---:|---:|",
    ]
    for _, r in res.iterrows():
        lineas.append(f"| {r['escenario']} | {r['duracion_s']:.0f} | {r['nivel_max']} | "
                      f"{f(r['t_nivel_max_s'])} | {r['motivos'] or '-'} | "
                      f"{'sí' if r['emergencia'] else 'no'} | {f(r['t_emergencia_s'])} |")
    lineas += ["", f"Escenarios con emergencia: {int(res['emergencia'].sum())} de {len(res)}.", ""]
    ruta.write_text("\n".join(lineas), encoding="utf-8")


def main(argv: list[str] | None = None) -> pd.DataFrame:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--semilla", type=int, default=42)
    p.add_argument("--salida", type=Path, default=ROOT / "resultados")
    args = p.parse_args(argv)

    res = ejecutar_escenarios(args.semilla)
    args.salida.mkdir(parents=True, exist_ok=True)
    res.to_csv(args.salida / "escenarios.csv", index=False)
    escribir_md(res, args.semilla, args.salida / "escenarios.md")
    print(res.to_string(index=False))
    return res


if __name__ == "__main__":
    main()
