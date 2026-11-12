---
name: driveguard-cnn
description: Entrena, evalúa y guarda la CNN de ojos abiertos/cerrados (core.ojos_cnn) y compara su desempeño con el método EAR. Reemplaza el notebook 04. Úsala cuando haya datos de ojos disponibles.
---

# CNN de ojos y comparación EAR vs CNN

Script: `scripts/experimentos/cnn.py` con `argparse` (`--datos` carpeta con subcarpetas `abiertos/` y `cerrados/`, `--epocas`, `--semilla` 42, `--salida` `resultados/`). No cree notebooks. Fije la semilla en `random`, `numpy` y `torch`.

Privacidad: los recortes de ojos son imágenes de rostros. `data/ojos/` está ignorado por git; **no versione imágenes** ni las copie a otra carpeta del repositorio.

Pasos:
1. Localice los datos: MRL Eye Dataset o capturas propias en `data/ojos/` (por ejemplo `data/ojos/propios/abiertos` y `.../cerrados`). Si no hay datos, detenga y dígalo; no invente datos.
2. Cargue las imágenes en gris, redimensione a `core.ojos_cnn.TAM` (64) y normalice con `core.ojos_cnn.preparar`. Clases según `core.ojos_cnn.CLASES` (`cerrado`=0, `abierto`=1). Divida 70/15/15 estratificado con semilla fija.
3. Entrene la red de `core.ojos_cnn.crear_cnn()` (PyTorch, CPU), con pérdida y optimizador explícitos. Guarde la curva de pérdida y exactitud por época.
4. Evalúe en el conjunto de prueba: exactitud, precisión, recall, F1 y matriz de confusión.
5. Guarde los pesos en `models/cnn_ojos.pt` (ruta `CNN_OJOS_PATH`; el archivo está en `.gitignore`). Compruebe que `ClasificadorOjos(CNN_OJOS_PATH)` lo carga y que `prob_cerrado` devuelve probabilidades entre 0 y 1.
6. **Comparación EAR vs CNN:** sobre el mismo conjunto de prueba (o sobre `core.simulacion` si no hay EAR real), calcule el cierre predicho por EAR (umbral `ConfigRiesgo().ear_umbral_defecto`) y por la CNN, y compare F1 y errores. No cambie los valores de `ConfigRiesgo`.
7. Guarde `resultados/cnn_metricas.csv`, `resultados/cnn_confusion.png`, `resultados/cnn_curvas.png` y `resultados/cnn.md` con la tabla EAR vs CNN y conclusiones. Explique cómo activarla en la app (`OJOS_METODO=cnn`) sin editar `.env`.
8. Si añade funciones nuevas a `core/`, agregue su prueba en `tests/` y ejecute `python -m pytest -q`.
