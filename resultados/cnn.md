# CNN de ojos abiertos/cerrados

Recortes propios de `ojos`, semilla 42, 10 épocas, Adam (lr 1e-3), lote 32. Partición por bloques temporales contiguos de cada clase (70/15/15): entrenamiento 1010, validación 216, prueba 216. Se guarda el modelo con mejor exactitud de validación.

- **Exactitud (prueba):** 100.0 % sobre 216 recortes.
- **Tiempo de inferencia:** 1.25 ms por fotograma (un recorte, CPU, mediana).

## F1 por clase (prueba)

| Clase | Precisión | Recall | F1 | Soporte |
|---|---:|---:|---:|---:|
| cerrado | 1.000 | 1.000 | 1.000 | 110 |
| abierto | 1.000 | 1.000 | 1.000 | 106 |

## Matriz de confusión (filas = real, columnas = predicho)

| | pred. cerrado | pred. abierto |
|---|---:|---:|
| **real cerrado** | 110 | 0 |
| **real abierto** | 0 | 106 |

## Última época

Entrenamiento: pérdida 0.0971, exactitud 0.982. Validación: pérdida 0.0123, exactitud 1.000.

## Limitaciones

Todos los recortes provienen de una misma persona y sesión de captura; aunque la partición temporal evita fotogramas casi idénticos entre conjuntos, la exactitud no anticipa el desempeño con otros conductores, cámaras o iluminación.
