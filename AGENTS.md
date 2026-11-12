# AGENTS.md

Fuente única de instrucciones para agentes (Claude Code, OpenCode, etc.). `CLAUDE.md` la importa con `@AGENTS.md`.

## Qué es el proyecto

DriveGuard Lab: prototipo académico (código, comentarios e interfaz en español) que detecta somnolencia y riesgo del conductor con una cámara web usando MediaPipe FaceLandmarker (EAR, MAR, pose de la cabeza). Hace sonar una alarma local y, si el conductor no responde, hay SOS o un choque simulado, ejecuta un protocolo de emergencia (correo, Telegram, SMS opcional). Curso: Deep Learning y Agentes Inteligentes. El detalle de umbrales, API y modelo de datos está en `README.md`.

## Entorno y comandos

Windows, Anaconda, entorno `DriveGuardLab` (Python 3.11) ya activo. No usar `uv`. Ejecutar siempre desde la raíz del repositorio (los imports son `core.*`, `backend.*`, `frontend.*`). MongoDB local en `mongodb://localhost:27017`, base `driveguard_lab`.

```bat
conda activate DriveGuardLab
python -m pytest                                  # 43 pruebas, sin cámara ni MongoDB real (mongomock)
python -m pytest tests/test_riesgo.py::nombre     # una sola prueba
python -m uvicorn backend.main:app --reload --port 8000   # API
python -m streamlit run frontend/app.py                   # interfaz
python scripts/descargar_modelos.py               # models/face_landmarker.task (--vit descarga también el ViT)
python scripts/generar_recursos.py                # assets/*.wav y data/ejemplos/*.csv
```

No hay linter ni formateador configurados.

## Arquitectura (resumen)

- `core/` (sin interfaz, compartido por API, app, scripts): `config.py` (`.env`, `ConfigRiesgo`, crea `data/`, `models/`, `assets/` al importarse), `landmarks.py` (MediaPipe Tasks, no `mp.solutions`), `riesgo.py` (`MotorRiesgo`: calibración, reglas, histéresis, emergencia), `pipeline.py` (`ProcesadorConductor` por fotograma y `analizar_video`), `alarma.py`, `faces.py` (ViT de expresiones en hilo aparte), `ojos_cnn.py` (CNN opcional), `notificaciones.py`, `impacto.py`, `simulacion.py` (mediciones sintéticas por escenario), `storage.py` (MongoDB).
- `backend/` FastAPI: `main.py` registra `conductores_api`, `sesiones_api`, `alertas_api`.
- `frontend/` Streamlit: `app.py` y un `*_ui.py` por pestaña; `api_client.py` habla con la API.

**Hilos:** `streamlit-webrtc` ejecuta `ProcesadorConductor.procesar()` en su propio hilo de video (MediaPipe, motor de riesgo, alarma con pygame/winsound). El hilo de Streamlit no toca el video: `@st.fragment(run_every=0.5)` en `monitoreo_ui.py` lee `snapshot()`, envía eventos a la API cada 5 s y maneja la cuenta regresiva. El ViT corre en un tercer hilo como máximo cada `EXPRESION_INTERVALO_S`.

**Tolerancia a fallos:** sin MongoDB, cámara y alarma siguen; si la API no responde en una emergencia, la interfaz envía la alerta directamente. Las alertas de una misma sesión respetan `ALERTA_COOLDOWN_S`.

**Convenciones:** solo se guardan métricas numéricas, nunca imágenes. El texto dibujado con OpenCV debe ser ASCII (`_ascii()` en `pipeline.py`). Las pruebas inyectan un `detector` falso en `ProcesadorConductor` y usan `alarma=None` / `expresiones=False`.

## Reglas

1. **No crear notebooks.** Los experimentos son scripts en `scripts/experimentos/` con `argparse`, semilla fija y salida en `resultados/` (CSV, PNG, MD).
2. **No cambiar los valores por defecto de `ConfigRiesgo`** (`core/config.py`) sin pedir confirmación. Para experimentos, crear una instancia con valores distintos.
3. **No leer, imprimir ni modificar `.env`.** Usar `NOTIFICACIONES_SIMULADAS=true` salvo que el usuario pida expresamente un envío real.
4. **No instalar `opencv-python-headless`** (MediaPipe usa `opencv-contrib-python`; mezclarlos rompe `cv2`).
5. **Toda función nueva en `core/` lleva prueba en `tests/`**, y se corre `python -m pytest` antes de terminar.
6. **No hacer `git push` ni borrar ramas.** Commits pequeños con Conventional Commits en español (por ejemplo `feat(core): agrega ...`).
7. **No guardar imágenes de rostros en el repositorio** (capturas, fotogramas, videos de personas, recortes de ojos propios).
