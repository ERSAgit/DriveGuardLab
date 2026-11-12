# Verificación del entorno

Python 3.11.16 en `win32`.

## Librerías

| Elemento | Estado | Detalle |
|---|:---:|---|
| mediapipe | OK | 1.2.0 |
| opencv-contrib-python | OK | 5.0.0.93 |
| numpy | OK | 2.4.6 |
| pandas | OK | 3.1.0 |
| matplotlib | OK | 3.11.2 |
| torch | OK | 2.15.0 |
| fastapi | OK | 0.162.0 |
| uvicorn | OK | 0.54.0 |
| streamlit | OK | 1.66.1 |
| streamlit-webrtc | OK | 0.79.0 |
| pymongo | OK | 4.19.0 |
| requests | OK | 2.34.2 |
| pytest | OK | 9.2.0 |

## Modelo

| Elemento | Estado | Detalle |
|---|:---:|---|
| face_landmarker.task | OK | 3671 KB |

## Carpetas

| Elemento | Estado | Detalle |
|---|:---:|---|
| data/capturas | OK | 1 archivos |
| data/ejemplos | OK | 2 archivos |
| data/ojos | OK | 1442 archivos |
| data/videos | OK | 3 archivos |
| models | OK | 2 archivos |
| assets | OK | 2 archivos |

## Servicios

| Elemento | Estado | Detalle |
|---|:---:|---|
| MongoDB (localhost:27017) | OK | ping correcto |
| API (http://127.0.0.1:8000) | FALLA | no disponible (ConnectTimeout); inícela con uvicorn si la necesita |

## Resumen

21 de 22 comprobaciones correctas.
