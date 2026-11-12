---
name: driveguard-video
description: Analiza una foto o un video propio con core.pipeline y compara lo detectado contra un guion de lo que ocurre en el video. Úsala para validar el detector con grabaciones del usuario.
---

# Foto o video propio

Script: `scripts/experimentos/video.py` con `argparse` (`--entrada` ruta de la foto o video, `--guion` CSV opcional, `--salida` `resultados/`, `--max-segundos`). No cree notebooks.

Privacidad (regla 7 de AGENTS.md): el video o la foto del usuario se lee desde donde esté, **no se copia al repositorio** y no se guardan fotogramas ni video anotado dentro del repo. Si se quiere un video anotado, escríbalo en una ruta fuera del repositorio o en `resultados/*.mp4` (ignorado por git) y avise que es temporal. Solo se guardan métricas numéricas.

Pasos:
1. Verifique que existe `models/face_landmarker.task`; si no, proponga `python scripts/descargar_modelos.py`.
2. **Video:** `core.pipeline.analizar_video(ruta, config=ConfigRiesgo(), expresiones=False, max_segundos=...)` devuelve un DataFrame por fotograma. **Foto:** `core.landmarks.DetectorRostro(modo="imagen")` (confirme el nombre del modo leyendo `core/landmarks.py`) y reporte EAR, MAR, pitch y yaw.
3. Resuma por tramos: nivel máximo, instantes de cambio de nivel, motivos y emergencia.
4. **Guion:** si el usuario da un CSV `inicio_s,fin_s,evento` (por ejemplo `cierre_ojos`, `bostezo`, `giro_cabeza`), compare cada fila con los eventos detectados en esa ventana (tolerancia ±1 s). Calcule aciertos, omisiones y falsas detecciones. Sin guion, pídalo o describa solo lo detectado.
5. Guarde `resultados/video.csv` (métricas por segundo), `resultados/video.png` (EAR, umbral y nivel en el tiempo) y `resultados/video.md` con el resumen y la comparación con el guion.
6. Ejecute `python -m pytest -q` antes de terminar.
