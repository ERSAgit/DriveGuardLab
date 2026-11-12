# Barrido de umbrales del motor de riesgo

- Conductores sintéticos: 20 (semilla 42, 15 fps).
- Detección: escenario `microsueno` con nivel ALTO por `microsueno` para t >= 20 s.
- Falsa alarma: escenario `normal` (sin eventos) con nivel ALTO.
- No se modificaron los valores por defecto de `ConfigRiesgo`.

| microsueno_s | factor_ear | detección (%) | falsas alarmas (%) | latencia media (s) |
| ---: | ---: | ---: | ---: | ---: |
| 0.5 | 0.65 | 100.0 | 20.0 | 0.49 |
| 0.5 | 0.75 | 100.0 | 35.0 | 0.45 |
| 0.5 | 0.85 | 100.0 | 40.0 | 0.41 |
| 1.0 | 0.65 | 100.0 | 0.0 | 1.05 |
| 1.0 | 0.75 | 100.0 | 0.0 | 1.04 |
| 1.0 | 0.85 | 100.0 | 0.0 | 0.95 |
| 1.5 | 0.65 | 75.0 | 0.0 | 1.58 |
| 1.5 | 0.75 | 75.0 | 0.0 | 1.56 |
| 1.5 | 0.85 | 85.0 | 0.0 | 1.47 |
| 2.0 | 0.65 | 70.0 | 0.0 | 2.04 |
| 2.0 | 0.75 | 70.0 | 0.0 | 2.03 |
| 2.0 | 0.85 | 80.0 | 0.0 | 1.94 |

## Recomendación

La combinación recomendada es **microsueno_s = 1.0 s** y **factor_ear = 0.75**: detecta 100.0 % de los microsueños con 0.0 % de falsas alarmas y una latencia media de 1.04 s.

Los valores por defecto (`microsueno_s = 1.5` s, `factor_ear = 0.75`) obtienen 75.0 % de detección y 0.0 % de falsas alarmas. La recomendación surge de maximizar la detección entre las combinaciones con falsas alarmas <= 5 %, prefiriendo los valores más cercanos a los defaults cuando hay empate. Si se desea adoptar la recomendación, el cambio debe hacerse de forma explícita en `core/config.py`.
