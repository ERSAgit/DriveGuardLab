"""Prueba rápida del barrido de umbrales (pocos conductores)."""
import pandas as pd

from scripts.experimentos import umbrales


def test_umbrales_genera_salidas(tmp_path):
    res = umbrales.main(["--conductores", "3", "--semilla", "7", "--salida", str(tmp_path)])
    for nombre in ("umbrales.csv", "umbrales.md", "umbrales.png", "umbrales_detalle.csv"):
        assert (tmp_path / nombre).stat().st_size > 0
    csv = pd.read_csv(tmp_path / "umbrales.csv")
    assert len(csv) == 12 == len(res)
    assert csv["deteccion_pct"].between(0, 100).all()
    assert csv["falsas_alarmas_pct"].between(0, 100).all()
    assert "Recomendación" in (tmp_path / "umbrales.md").read_text(encoding="utf-8")


def test_umbrales_reproducible(tmp_path):
    a = umbrales.main(["--conductores", "2", "--semilla", "1", "--salida", str(tmp_path / "a")])
    b = umbrales.main(["--conductores", "2", "--semilla", "1", "--salida", str(tmp_path / "b")])
    pd.testing.assert_frame_equal(a, b)
