---
name: driveguard-escenarios
description: Ejecuta los 7 escenarios sintéticos de core.simulacion con el motor de riesgo y reporta nivel máximo, instante en que se alcanza, motivos y si hubo emergencia. Úsala para comprobar el comportamiento del motor sin cámara.
---

# Escenarios sintéticos

Escenarios en `core.simulacion.ESCENARIOS`: `normal`, `cansancio`, `microsueno`, `sin_respuesta`, `distraccion`, `cabeceos`, `rostro_ausente`.

El código va en un script `scripts/experimentos/escenarios.py` con `argparse` (`--semilla` por defecto 42, `--fps` 15, `--salida` por defecto `resultados/`). No cree notebooks.

1. Para cada escenario: `mediciones = generar_mediciones(escenario, fps, semilla)` y `df = ejecutar(mediciones, ConfigRiesgo())`. Use los valores por defecto de `ConfigRiesgo` sin modificarlos.
2. Inspeccione `df.columns` (vienen de `EstadoRiesgo.a_dict()` más `motivos` y `ear_crudo`) para localizar las columnas de nivel y de emergencia.
3. Por escenario calcule: nivel máximo según `core.riesgo.ORDEN`, el primer instante `t` en que se alcanza ese nivel, el conjunto de motivos observados (columna `motivos`) y si la emergencia se activó (y cuándo).
4. Compare con lo esperado: `normal` debe quedar en NORMAL sin emergencia; `microsueno` debe llegar a ALTO por microsueño tras ~1,5 s de cierre; `sin_respuesta` debe activar emergencia; `distraccion` y `rostro_ausente` deben llegar a MEDIO; `cabeceos` a MEDIO; `cansancio` a MEDIO. Marque cualquier discrepancia.
5. Guarde `resultados/escenarios.csv` (una fila por escenario), `resultados/escenarios.png` (EAR y nivel en el tiempo por escenario, ejes rotulados en español) y `resultados/escenarios.md` con la tabla y las discrepancias.
6. Ejecute `python -m pytest -q` antes de terminar.
