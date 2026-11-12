---
name: driveguard-umbrales
description: Barrido de umbrales del motor de riesgo (microsueno_s × factor_ear) con 20 conductores sintéticos, midiendo tasa de detección y falsas alarmas. Úsala para elegir o justificar umbrales.
---

# Barrido de umbrales

Script: `scripts/experimentos/umbrales.py` con `argparse` (`--conductores` 20, `--semilla` 42, `--salida` `resultados/`). No cree notebooks. **No modifique los valores por defecto de `ConfigRiesgo`**; cree una instancia por combinación (`ConfigRiesgo(microsueno_s=..., factor_ear=...)` o `dataclasses.replace`).

Parámetros del barrido:
- `microsueno_s` ∈ {0.5, 1.0, 1.5, 2.0}
- `factor_ear` ∈ {0.65, 0.75, 0.85}
- Total: 12 combinaciones × 20 conductores.

Pasos:
1. Genere 20 conductores sintéticos variando con una semilla fija (`numpy.random.default_rng(semilla)`): `ear_base` (0.24–0.36), `ruido` (0.008–0.02), `parpadeo_cada_s` (3–6) y `dur_parpadeo` (0.10–0.25), pasados a `core.simulacion.generar_mediciones`.
2. Por conductor y combinación ejecute dos escenarios con `core.simulacion.ejecutar`:
   - `microsueno` (con cierre real de 2.5 s): **detección** = el nivel llega a ALTO por microsueño.
   - `normal`: **falsa alarma** = el nivel llega a ALTO o MEDIO en un escenario sin eventos.
3. Agregue por combinación: tasa de detección (%), tasa de falsas alarmas (%) y, para los detectados, la latencia media desde el inicio del cierre (t=20 s).
4. Guarde `resultados/umbrales.csv` (una fila por combinación y conductor, más una agregada), `resultados/umbrales.png` (mapa de calor de detección y de falsas alarmas, ejes `microsueno_s` y `factor_ear`) y `resultados/umbrales.md` con la tabla agregada y una recomendación razonada. Indique que los valores por defecto son 1.5 s y 0.75 y cómo se comparan.
5. Si la recomendación difiere de los valores por defecto, **no los cambie**: proponga el cambio y pida confirmación.
6. Ejecute `python -m pytest -q` antes de terminar.
