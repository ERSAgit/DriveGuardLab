"""Pruebas rápidas de la CNN de ojos con recortes sintéticos (sin cámara ni datos reales)."""
import cv2
import numpy as np
import pytest

from core.ojos_cnn import TAM, ClasificadorOjos, crear_cnn, preparar
from scripts import entrenar_cnn_ojos as ent
from scripts.metricas import matriz_confusion, reporte


def _recorte(abierto: bool, rng) -> np.ndarray:
    img = np.full((TAM, TAM), 140, np.uint8)
    if abierto:
        cv2.ellipse(img, (32, 32), (22, 12), 0, 0, 360, 235, -1)
        cv2.circle(img, (32, 32), 7, 20, -1)
    else:
        cv2.line(img, (8, 32), (56, 32), 20, 3)
    ruido = rng.normal(0, 6, img.shape)
    return np.clip(img + ruido, 0, 255).astype(np.uint8)


@pytest.fixture
def datos(tmp_path):
    rng = np.random.default_rng(0)
    for carpeta, abierto in (("abiertos", True), ("cerrados", False)):
        d = tmp_path / "ojos" / "propios" / carpeta
        d.mkdir(parents=True)
        for i in range(40):
            cv2.imwrite(str(d / f"{carpeta[:-2]}_{1000 + i}_{i}.png"), _recorte(abierto, rng))
    return tmp_path / "ojos"


def test_arquitectura_y_preparar():
    import torch
    x = preparar([np.zeros((TAM, TAM), np.uint8), np.full((TAM, TAM), 255, np.uint8)])
    assert tuple(x.shape) == (2, 1, TAM, TAM)
    assert float(x.min()) == -1.0 and float(x.max()) == 1.0
    assert tuple(crear_cnn().eval()(x).shape) == (2, 2)
    assert torch.isfinite(crear_cnn()(x)).all()


def test_particion_por_bloques_sin_mezclar(datos):
    X, y, orden = ent.cargar_recortes(datos)
    assert X.shape == (80, TAM, TAM) and set(y) == {0, 1}
    tr, va, te = ent.particionar_bloques(y, orden)
    assert len(set(tr) & set(va)) == len(set(tr) & set(te)) == len(set(va) & set(te)) == 0
    assert len(tr) + len(va) + len(te) == 80
    for clase in (0, 1):                      # por clase: train < val < test en el tiempo
        o = lambda idx: orden[idx][y[idx] == clase]
        assert o(tr).max() < o(va).min() and o(va).max() < o(te).min()


def test_entrenar_guarda_modelo_y_reportes(datos, tmp_path):
    modelo, salida = tmp_path / "m" / "cnn.pt", tmp_path / "res"
    modelo.parent.mkdir()
    modelo.write_bytes(b"modelo previo")
    args = ["--datos", str(datos), "--salida", str(salida), "--modelo", str(modelo),
            "--epocas", "6", "--semilla", "3", "--lote", "8"]
    r = ent.main(args)
    assert modelo.stat().st_size > 100 and (modelo.parent / "cnn.prev.pt").read_bytes() == b"modelo previo"
    for nombre in ("cnn.md", "cnn_curvas.png"):
        assert (salida / nombre).stat().st_size > 0
    assert len(r["historial"]) == 6 and 0 <= r["reporte"]["exactitud"] <= 1
    assert r["reporte"]["exactitud"] > 0.9          # clases muy separables
    clf = ClasificadorOjos(modelo)
    p = clf.prob_cerrado([_recorte(False, np.random.default_rng(1)), _recorte(True, np.random.default_rng(2))])
    assert p[0] > p[1]
    assert "Matriz de confusión" in (salida / "cnn.md").read_text(encoding="utf-8")
    # el respaldo no se pisa en una segunda ejecución
    ent.main(args)
    assert (modelo.parent / "cnn.prev.pt").read_bytes() == b"modelo previo"


def test_entrenamiento_reproducible(datos):
    X, y, orden = ent.cargar_recortes(datos)
    tr, va, _ = ent.particionar_bloques(y, orden)
    _, h1 = ent.entrenar(X, y, tr, va, 1, 5)
    _, h2 = ent.entrenar(X, y, tr, va, 1, 5)
    assert h1 == h2


def test_sin_datos_falla(tmp_path):
    with pytest.raises(FileNotFoundError):
        ent.cargar_recortes(tmp_path)


def test_metricas_casos_conocidos():
    y, p = [0, 0, 0, 1, 1, 1], [0, 0, 1, 1, 1, 1]
    assert matriz_confusion(y, p).tolist() == [[2, 1], [0, 3]]
    r = reporte(y, p)
    assert r["exactitud"] == pytest.approx(5 / 6)
    assert r["por_clase"][0]["f1"] == pytest.approx(2 * 1.0 * (2 / 3) / (1.0 + 2 / 3))
    assert reporte([], [])["exactitud"] == 0.0
