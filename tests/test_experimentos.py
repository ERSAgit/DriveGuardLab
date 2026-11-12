"""Pruebas rápidas de los scripts de experimentos (sin cámara ni datos reales)."""
import numpy as np
import pandas as pd
import pytest

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


# ----------------------------------------------------------------- escenarios
def test_escenarios_resultados_esperados(tmp_path):
    from core.simulacion import ESCENARIOS
    from scripts.experimentos import escenarios

    res = escenarios.main(["--semilla", "42", "--salida", str(tmp_path)])
    assert list(res["escenario"]) == list(ESCENARIOS) and len(res) == 7
    por = res.set_index("escenario")
    assert por.loc["normal", "nivel_max"] == "NORMAL" and not por.loc["normal", "emergencia"]
    assert por.loc["microsueno", "nivel_max"] == "ALTO"
    assert por.loc["sin_respuesta", "emergencia"]
    assert por.loc["sin_respuesta", "t_emergencia_s"] > por.loc["sin_respuesta", "t_nivel_max_s"]
    assert (res.loc[res["nivel_max"] != "NORMAL", "t_nivel_max_s"] >= 10.0).all()   # tras calibrar
    assert (tmp_path / "escenarios.csv").stat().st_size > 0
    assert "sin_respuesta" in (tmp_path / "escenarios.md").read_text(encoding="utf-8")


def test_escenarios_ignora_calibracion():
    from scripts.experimentos import escenarios

    df = pd.DataFrame({"t": [0.0, 1.0], "nivel": ["ALTO", "ALTO"], "motivos": ["x", "x"],
                       "calibrando": [True, True], "emergencia": [True, True]})
    r = escenarios.resumir_escenario("falso", df)
    assert r["nivel_max"] == "NORMAL" and not r["emergencia"]


# ------------------------------------------------------------- analizar_video
def _df_video(n=60):
    t = np.arange(n) / 10.0
    return pd.DataFrame({
        "t": t, "nivel": ["NORMAL"] * 40 + ["ALTO"] * (n - 40), "ear": np.full(n, 0.3),
        "ear_umbral": np.full(n, 0.21), "rostro": [True] * (n - 10) + [False] * 10,
        "calibrando": t < 2.0, "emergencia": [False] * n,
        "motivos": [""] * 40 + ["microsueno"] * (n - 40)})


def test_video_resumen_y_salidas(tmp_path):
    from scripts.experimentos import analizar_video as av

    df = _df_video()
    r = av.resumir(df)
    assert r["fotogramas"] == 60 and abs(r["pct_rostro"] - 100 * 50 / 60) < 1e-6
    assert r["motivos"] == {"microsueno": 20}
    assert abs(sum(r["pct_nivel"].values()) - 100) < 1e-6
    av.escribir_md(r, "demo.mp4", tmp_path / "video.md")
    av.escribir_png(df, tmp_path / "video.png")
    assert "microsueno" in (tmp_path / "video.md").read_text(encoding="utf-8")
    assert (tmp_path / "video.png").stat().st_size > 0


def test_video_inexistente_falla(tmp_path):
    from scripts.experimentos import analizar_video as av

    with pytest.raises(SystemExit):
        av.main(["--video", str(tmp_path / "no_existe.mp4"), "--salida", str(tmp_path)])


# ------------------------------------------------------------------ ear_vs_cnn
def test_ear_vs_cnn_intervalos_y_etiquetas():
    from scripts.experimentos import ear_vs_cnn as ev

    assert ev.parsear_intervalos(["10-20", "30-35"]) == [(10.0, 20.0), (30.0, 35.0)]
    for malo in ("20-10", "abc", "10"):
        with pytest.raises(ValueError):
            ev.parsear_intervalos([malo])
    y = ev.etiquetar([5, 10, 19.9, 20, 31], [(10, 20), (30, 35)])
    assert y.tolist() == [1, 0, 0, 1, 0]


def test_ear_vs_cnn_metricas_con_df_sintetico(tmp_path):
    from scripts.experimentos import ear_vs_cnn as ev

    t = np.arange(0, 40, 0.5)
    cerrado = ((t >= 10) & (t < 20)) | ((t >= 30) & (t < 35))
    df = pd.DataFrame({"t": t, "rostro": True, "calibrando": t < 5.0, "ear_cerrado": cerrado,
                       "prob_cnn_cerrado": np.where(cerrado, 0.9, 0.1)})
    df.loc[df["t"] == 12.0, "rostro"] = False                    # fotograma sin rostro: excluido
    r = ev.evaluar(df, [(10, 20), (30, 35)])
    assert r["n_sin_rostro"] == 1 and r["n_calibracion"] == 10
    assert r["metodos"]["EAR"]["exactitud"] == 1.0 and r["metodos"]["CNN"]["por_clase"][0]["f1"] == 1.0
    assert r["tramos_ear"][0][0] == 10.0
    # una CNN que siempre dice "cerrado" tiene exactitud ~ proporción de cerrados
    df["prob_cnn_cerrado"] = 0.99
    peor = ev.evaluar(df, [(10, 20), (30, 35)])["metodos"]["CNN"]
    assert peor["por_clase"][1]["f1"] == 0.0 and peor["exactitud"] < 0.5
    ev.escribir_md(r, "demo.mp4", [(10, 20), (30, 35)], tmp_path / "ear_vs_cnn.md")
    texto = (tmp_path / "ear_vs_cnn.md").read_text(encoding="utf-8")
    assert "F1 cerrado" in texto and "Contraste con la señal" in texto


def test_ear_vs_cnn_sin_modelo_o_video_falla(tmp_path):
    from scripts.experimentos import ear_vs_cnn as ev

    with pytest.raises(SystemExit):
        ev.main(["--video", str(tmp_path / "x.mp4"), "--salida", str(tmp_path)])
    (tmp_path / "v.mp4").write_bytes(b"x")
    with pytest.raises(SystemExit):
        ev.main(["--video", str(tmp_path / "v.mp4"), "--modelo", str(tmp_path / "no.pt"),
                 "--salida", str(tmp_path)])
