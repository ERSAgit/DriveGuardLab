"""Prueba rápida del script de barrido de umbrales (sin cámara ni MongoDB)."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]


def cargar_modulo():
    ruta = RAIZ / "scripts" / "experimentos" / "umbrales.py"
    spec = importlib.util.spec_from_file_location("umbrales_exp", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_barrido_rapido_genera_salidas(tmp_path):
    modulo = cargar_modulo()
    detalle, resumen = modulo.barrido(n_conductores=2, semilla=7)

    assert len(resumen) == 12
    assert set(resumen["microsueno_s"]) == {0.5, 1.0, 1.5, 2.0}
    assert set(resumen["factor_ear"]) == {0.65, 0.75, 0.85}
    assert len(detalle) == 12 * 2
    for columna in ("deteccion_pct", "falsa_alarma_pct"):
        assert resumen[columna].between(0, 100).all()

    modulo.escribir_salidas(detalle, resumen, tmp_path, semilla=7, n_conductores=2)

    for nombre in ("umbrales.csv", "umbrales.md", "umbrales.png"):
        ruta = tmp_path / nombre
        assert ruta.exists() and ruta.stat().st_size > 0

    csv = pd.read_csv(tmp_path / "umbrales.csv")
    assert len(csv) == len(detalle) + len(resumen)
    assert (csv["tipo"] == "agregado").sum() == 12
    assert "Recomendación" in (tmp_path / "umbrales.md").read_text(encoding="utf-8")
