---
name: driveguard-verificar-entorno
description: Verifica que el entorno de DriveGuard Lab funciona (librerías, carpetas, modelo, sonidos, MongoDB, cámara y pruebas). Reemplaza el notebook 00_Verificacion_Entorno. Úsala al empezar o cuando algo falle al arrancar.
---

# Verificar el entorno

Genera un informe `resultados/verificacion_entorno.md`. No lea ni imprima `.env`.

1. Confirme el entorno: `python --version` debe dar 3.11 y `conda info --envs` debe marcar `DriveGuardLab` como activo.
2. Librerías: importe `cv2`, `mediapipe`, `numpy`, `pandas`, `fastapi`, `streamlit`, `pymongo`, `torch` y `pygame` (cada una en su propio `try`) e imprima la versión de las que existan. Verifique que `pip list` no incluya `opencv-python-headless`; si aparece, avise y no lo reinstale sin confirmación.
3. Carpetas: tras `import core.config` deben existir `data/`, `data/capturas`, `data/videos`, `data/ejemplos`, `data/ojos`, `models/` y `assets/`.
4. Modelo: compruebe que existe `models/face_landmarker.task`; si falta, proponga `python scripts/descargar_modelos.py` y pida confirmación antes de descargar.
5. Recursos: compruebe `assets/alarma_media.wav`, `assets/alarma_alta.wav` y `data/ejemplos/*.csv`; si faltan, proponga `python scripts/generar_recursos.py`.
6. MongoDB: ejecute `mongosh --eval "db.runCommand({ping:1})" mongodb://localhost:27017/driveguard_lab` (o `pymongo` con `serverSelectionTimeoutMS=2000`). Un fallo no es crítico: la cámara y la alarma funcionan sin MongoDB.
7. Cámara (opcional): abra `cv2.VideoCapture(0)`, lea un fotograma y reporte solo la resolución. No guarde ni muestre la imagen.
8. Pruebas: `python -m pytest -q`; deben pasar 43.
9. Escriba el informe con una tabla Componente | Estado (OK/FALLA/OMITIDO) | Detalle, y una lista de acciones recomendadas.
