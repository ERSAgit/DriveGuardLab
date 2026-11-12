# EAR vs CNN en un video etiquetado

Video: `ojos_etiquetado.mp4`. Ojos cerrados en: 10-20 s, 30-35 s; abiertos el resto. Se evalúan 450 de 600 fotogramas (225 cerrados, 225 abiertos); excluidos: 0 sin rostro y 150 de calibración.

| Método | Exactitud | F1 cerrado | F1 abierto | Recall cerrado | Precisión cerrado |
|---|---:|---:|---:|---:|---:|
| EAR | 40.4 % | 0.350 | 0.451 | 0.320 | 0.385 |
| CNN | 50.0 % | 0.667 | 0.000 | 1.000 | 0.500 |

## Matrices de confusión (filas = real, columnas = predicho)

**EAR**

| | pred. cerrado | pred. abierto |
|---|---:|---:|
| real cerrado | 72 | 153 |
| real abierto | 115 | 110 |

**CNN**

| | pred. cerrado | pred. abierto |
|---|---:|---:|
| real cerrado | 225 | 0 |
| real abierto | 225 | 0 |

## Contraste con la señal del video

- Tramos (>= 1 s) en que EAR detecta ojos cerrados: 10.0-14.3 s, 23.7-27.6 s, 36.3-39.9 s. Si no coinciden con los intervalos etiquetados, revise las etiquetas o el video antes de interpretar las cifras.
- Probabilidad media de cerrado de la CNN: 0.82 en tramos etiquetados cerrados y 0.85 en abiertos (una CNN útil separa ambos valores).

## Lectura

Mayor exactitud: **CNN** (EAR 40.4 %, CNN 50.0 %).
**Atención:** CNN predice una sola clase (recall 0 en la otra); su F1 de la clase que acierta es trivial y no indica que distinga ojos abiertos de cerrados.
La CNN se entrenó con capturas de la misma persona y entorno que el video, así que su resultado debería ser optimista, no una evaluación con otros conductores. Las etiquetas por intervalo no incluyen parpadeos normales dentro de los tramos abiertos ni la transición al cerrar o abrir los ojos, lo que penaliza a ambos métodos.

## Limitaciones

- **Etiquetas frente a la señal:** los intervalos cerrados dados no coinciden con los tramos donde EAR ve los ojos cerrados (ver la sección anterior), por lo que la exactitud de EAR queda por debajo del azar. Se mantuvieron las etiquetas originales; no se corrigieron.
- **La CNN no discrimina en este video:** predice «cerrado» casi siempre (probabilidad media similar en tramos cerrados y abiertos), de modo que su exactitud (~50 %) y su F1 de cerrado (~0.67) son triviales. Su 100 % de exactitud en `cnn.md` no se traslada al video.
- **Causa probable:** los recortes de entrenamiento son muy oscuros y las clases se capturaron en ráfagas separadas, así que la red pudo aprender diferencias de iluminación entre ráfagas en lugar del estado del ojo. La partición temporal no lo detecta, porque cada clase se reparte dentro de su propia ráfaga.
- **Qué haría falta:** recapturar ojos abiertos y cerrados intercalados y con iluminación variada, y verificar las etiquetas del video. No se probó el reentrenamiento ni se modificó `core/ojos_cnn.py`.
- **Alcance:** una sola persona, un solo video y 450 fotogramas útiles; las cifras no son generalizables.
