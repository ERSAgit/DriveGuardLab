# Barrido de umbrales del microsueño

20 conductores sintéticos, semilla 42. Parámetros aleatorios: EAR base 0.25-0.38, ruido 0.005-0.025, parpadeo normal de 0.10 a 0.70 s cada 3-6 s y cierre de microsueño de 1.2 a 3.0 s (inicio en t=20 s).

- **Detección:** % de escenarios `microsueno` que llegan a ALTO con t >= 20 s.
- **Falsas alarmas:** % de escenarios `normal` que llegan a ALTO.

| microsueno_s | factor_ear | Detección (%) | Falsas alarmas (%) | Latencia media (s) |
|---:|---:|---:|---:|---:|
| 0.5 | 0.65 | 100.0 | 15.0 | 0.53 |
| 0.5 | 0.75 | 100.0 | 40.0 | 0.50 |
| 0.5 | 0.85 | 100.0 | 40.0 | 0.44 |
| 1.0 | 0.65 | 100.0 | 0.0 | 1.03 |
| 1.0 | 0.75 | 100.0 | 0.0 | 0.99 |
| 1.0 | 0.85 | 100.0 | 0.0 | 0.93 |
| 1.5 | 0.65 | 85.0 | 0.0 | 1.56 |
| 1.5 | 0.75 | 90.0 | 0.0 | 1.52 |
| 1.5 | 0.85 | 95.0 | 0.0 | 1.46 |
| 2.0 | 0.65 | 50.0 | 0.0 | 1.99 |
| 2.0 | 0.75 | 60.0 | 0.0 | 1.97 |
| 2.0 | 0.85 | 70.0 | 0.0 | 1.90 |

## Recomendación

Con un tope de 5 % de falsas alarmas, la combinación recomendada es **microsueno_s = 1.0 s y factor_ear = 0.85**: detecta 100.0 % de los microsueños con 0.0 % de falsas alarmas y una latencia media de 0.93 s. Los valores por defecto (1.5 s y 0.75) dan 90.0 % de detección y 0.0 % de falsas alarmas. Umbrales de tiempo cortos detectan más, pero convierten parpadeos largos en falsas alarmas; los largos pierden los cierres más breves. Es un resultado sobre datos sintéticos: no cambia los valores por defecto sin confirmación.
