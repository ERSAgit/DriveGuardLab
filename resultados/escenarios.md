# Escenarios sintéticos frente al motor de riesgo

Semilla 42, `ConfigRiesgo` con valores por defecto. Se ignoran las filas en calibración (primeros segundos).

| Escenario | Duración (s) | Nivel máximo | Primer instante (s) | Motivos | Emergencia | Instante emergencia (s) |
|---|---:|:---:|---:|---|:---:|---:|
| normal | 60 | NORMAL | 10.00 | - | no | - |
| cansancio | 100 | MEDIO | 40.00 | cansancio_perclos,bostezos | no | - |
| microsueno | 40 | ALTO | 21.53 | microsueno | no | - |
| sin_respuesta | 50 | ALTO | 21.53 | microsueno,cansancio_perclos | sí | 31.53 |
| distraccion | 40 | MEDIO | 23.00 | distraccion | no | - |
| cabeceos | 60 | MEDIO | 40.47 | cabeceos | no | - |
| rostro_ausente | 40 | MEDIO | 23.00 | rostro_ausente | no | - |

Escenarios con emergencia: 1 de 7.
