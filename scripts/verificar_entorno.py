"""Verifica el entorno de DriveGuard Lab (reemplaza el notebook 00).

Revisa librerías (con versión), el modelo face_landmarker.task, las carpetas de
datos, MongoDB (ping) y la API (/health, solo si está arriba). Escribe
resultados/entorno.md. Una dependencia ausente se informa pero no hace fallar
el script; MongoDB o la API caídos tampoco (la app tolera ambos casos).

Uso (desde la raíz del repositorio):
    python scripts/verificar_entorno.py --salida resultados
"""
from __future__ import annotations

import argparse
import sys
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# (nombre del paquete en pip, módulo a importar)
LIBRERIAS = [
    ("mediapipe", "mediapipe"), ("opencv-contrib-python", "cv2"), ("numpy", "numpy"),
    ("pandas", "pandas"), ("matplotlib", "matplotlib"), ("torch", "torch"),
    ("fastapi", "fastapi"), ("uvicorn", "uvicorn"), ("streamlit", "streamlit"),
    ("streamlit-webrtc", "streamlit_webrtc"), ("pymongo", "pymongo"),
    ("requests", "requests"), ("pytest", "pytest"),
]
CARPETAS = ["data/capturas", "data/ejemplos", "data/ojos", "data/videos", "models", "assets"]


def revisar_librerias(librerias=LIBRERIAS) -> list[dict]:
    filas = []
    for paquete, modulo in librerias:
        try:
            import_module(modulo)
            try:
                v = version(paquete)
            except PackageNotFoundError:
                v = "?"
            filas.append({"nombre": paquete, "ok": True, "detalle": v})
        except Exception as exc:  # noqa: BLE001 - se informa cualquier fallo de importación
            filas.append({"nombre": paquete, "ok": False, "detalle": f"{type(exc).__name__}: {exc}"})
    return filas


def revisar_modelo(ruta: Path) -> dict:
    ruta = Path(ruta)
    if ruta.exists():
        return {"nombre": ruta.name, "ok": True, "detalle": f"{ruta.stat().st_size / 1024:.0f} KB"}
    return {"nombre": ruta.name, "ok": False,
            "detalle": "falta; ejecute python scripts/descargar_modelos.py"}


def revisar_carpetas(raiz: Path, carpetas=CARPETAS) -> list[dict]:
    filas = []
    for c in carpetas:
        p = Path(raiz) / c
        if p.is_dir():
            n = sum(1 for f in p.rglob("*") if f.is_file() and f.name != ".gitkeep")
            filas.append({"nombre": c, "ok": True, "detalle": f"{n} archivos"})
        else:
            filas.append({"nombre": c, "ok": False, "detalle": "no existe"})
    return filas


def _host(uri: str) -> str:
    """Solo host:puerto; nunca usuario ni contraseña."""
    u = urlparse(uri)
    return f"{u.hostname or '?'}:{u.port or 27017}"


def revisar_mongo(uri: str, timeout_ms: int = 2000) -> dict:
    destino = _host(uri)
    try:
        from pymongo import MongoClient
        MongoClient(uri, serverSelectionTimeoutMS=timeout_ms).admin.command("ping")
        return {"nombre": f"MongoDB ({destino})", "ok": True, "detalle": "ping correcto"}
    except Exception as exc:  # noqa: BLE001
        return {"nombre": f"MongoDB ({destino})", "ok": False,
                "detalle": f"sin respuesta ({type(exc).__name__})"}


def revisar_api(url: str, timeout_s: float = 2.0) -> dict:
    try:
        import requests
        r = requests.get(url.rstrip("/") + "/health", timeout=timeout_s)
        r.raise_for_status()
        d = r.json()
        return {"nombre": f"API ({url})", "ok": True,
                "detalle": f"status={d.get('status')}, mongodb={d.get('mongodb')}"}
    except Exception as exc:  # noqa: BLE001
        return {"nombre": f"API ({url})", "ok": False,
                "detalle": f"no disponible ({type(exc).__name__}); inícela con uvicorn si la necesita"}


def escribir_md(secciones: dict[str, list[dict]], ruta: Path) -> None:
    lineas = ["# Verificación del entorno", "",
              f"Python {sys.version.split()[0]} en `{sys.platform}`.", ""]
    for titulo, filas in secciones.items():
        lineas += [f"## {titulo}", "", "| Elemento | Estado | Detalle |", "|---|:---:|---|"]
        for f in filas:
            lineas.append(f"| {f['nombre']} | {'OK' if f['ok'] else 'FALLA'} | {f['detalle']} |")
        lineas.append("")
    total = sum(len(f) for f in secciones.values())
    ok = sum(x["ok"] for f in secciones.values() for x in f)
    lineas += ["## Resumen", "", f"{ok} de {total} comprobaciones correctas.", ""]
    ruta.write_text("\n".join(lineas), encoding="utf-8")


def main(argv: list[str] | None = None) -> dict[str, list[dict]]:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--salida", type=Path, default=ROOT / "resultados")
    args = p.parse_args(argv)

    from core.config import API_URL, LANDMARKER_PATH, MONGO_URI
    secciones = {
        "Librerías": revisar_librerias(),
        "Modelo": [revisar_modelo(LANDMARKER_PATH)],
        "Carpetas": revisar_carpetas(ROOT),
        "Servicios": [revisar_mongo(MONGO_URI), revisar_api(API_URL)],
    }
    args.salida.mkdir(parents=True, exist_ok=True)
    escribir_md(secciones, args.salida / "entorno.md")
    for titulo, filas in secciones.items():
        for f in filas:
            print(f"[{'OK' if f['ok'] else '--'}] {titulo}: {f['nombre']} - {f['detalle']}")
    return secciones


if __name__ == "__main__":
    main()
