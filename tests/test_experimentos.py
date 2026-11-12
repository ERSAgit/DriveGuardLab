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


# ------------------------------------------------------------ verificar_entorno
def test_entorno_informa_servicios_caidos(tmp_path, monkeypatch):
    from scripts import verificar_entorno as ve

    monkeypatch.setattr(ve, "revisar_mongo",
                        lambda uri: {"nombre": "MongoDB", "ok": False, "detalle": "caido"})
    monkeypatch.setattr(ve, "revisar_api",
                        lambda url: {"nombre": "API", "ok": False, "detalle": "caida"})
    secciones = ve.main(["--salida", str(tmp_path)])
    texto = (tmp_path / "entorno.md").read_text(encoding="utf-8")
    assert "## Servicios" in texto and "FALLA" in texto
    assert {"Librerías", "Modelo", "Carpetas", "Servicios"} == set(secciones)


def test_entorno_host_no_expone_credenciales():
    from scripts import verificar_entorno as ve

    assert ve._host("mongodb://usuario:secreto@miservidor:27018/db") == "miservidor:27018"
    assert "secreto" not in ve._host("mongodb://usuario:secreto@miservidor")


def test_entorno_revisiones_basicas(tmp_path):
    from scripts import verificar_entorno as ve

    assert not ve.revisar_modelo(tmp_path / "no_existe.task")["ok"]
    (tmp_path / "data").mkdir()
    filas = {f["nombre"]: f["ok"] for f in ve.revisar_carpetas(tmp_path, ["data", "otra"])}
    assert filas == {"data": True, "otra": False}
    lib = ve.revisar_librerias([("numpy", "numpy"), ("inexistente", "modulo_que_no_existe_xyz")])
    assert [f["ok"] for f in lib] == [True, False]
