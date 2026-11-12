"""Métricas de clasificación con numpy (sin depender de scikit-learn)."""
from __future__ import annotations

import numpy as np


def matriz_confusion(y_true, y_pred, n_clases: int = 2) -> np.ndarray:
    """Filas = clase real, columnas = clase predicha."""
    m = np.zeros((n_clases, n_clases), dtype=int)
    for t, p in zip(np.asarray(y_true, dtype=int), np.asarray(y_pred, dtype=int)):
        m[t, p] += 1
    return m


def reporte(y_true, y_pred, n_clases: int = 2) -> dict:
    """Exactitud y precisión / recall / F1 por clase (0 si el denominador es 0)."""
    m = matriz_confusion(y_true, y_pred, n_clases)
    total = int(m.sum())
    por_clase = []
    for c in range(n_clases):
        tp = int(m[c, c])
        fp = int(m[:, c].sum() - tp)
        fn = int(m[c, :].sum() - tp)
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        por_clase.append({"precision": prec, "recall": rec, "f1": f1, "soporte": tp + fn})
    return {"exactitud": float(np.trace(m) / total) if total else 0.0, "n": total,
            "por_clase": por_clase, "matriz": m}
