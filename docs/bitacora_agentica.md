# Bitácora agéntica

Datos medidos por el estudiante. Las celdas con "—" no se midieron o no aplican (esa herramienta no participó en la etapa). "Tiempo hasta verde" se reporta como la duración de la etapa (hora fin − hora inicio), porque no se midió por separado.

## Etapa 1: Configuración

| Campo | Claude Code | OpenCode |
|---|---|---|
| Rama | lab/solarte-emmanuel | — |
| Modelo | Sonnet 5.5 | — |
| Hora inicio | 9:08 | — |
| Hora fin | 9:26 | — |
| Tiempo hasta verde (min) | 18 (duración de la etapa) | — |
| Costo (% de cupo) | No separable por tarea (ver "Costo") | — |
| Intervenciones humanas | 2 (pedí diagnosticar el MCP de mongodb; elegí instalarlo global) | — |
| Iteraciones fallidas | 1 (ver "Qué salió mal") | — |
| Pruebas nuevas | — | — |
| Errores graves | Ninguno; `revisor-seguridad` sin hallazgos | — |

## Etapa 2: E3.3 Umbrales

| Campo | Claude Code | OpenCode |
|---|---|---|
| Rama | lab/solarte-emmanuel | lab/solarte-emmanuel-oc (desde 1de8cee) |
| Modelo | Sonnet 5.5 | Big Pickle (OpenCode Zen, gratuito); OpenCode 1.19.5 |
| Hora inicio | 9:29 | 10:16 |
| Hora fin | 9:34 | 10:20 |
| Tiempo hasta verde (min) | 5 (duración de la etapa) | 4 (duración de la etapa) |
| Costo (% de cupo) | No separable por tarea (ver "Costo") | USD 0; 58.5K tokens |
| Intervenciones humanas | 0 | 0 |
| Iteraciones fallidas | 0 | 0 |
| Pruebas nuevas | 2 | 1 |
| Errores graves | Sin errores graves | — |

Observaciones:

- Claude Code agregó latencia y un CSV por conductor sin que se pidiera.
- Recomendación de Claude Code: microsueno_s = 1.0 s y factor_ear = 0.85. Con los valores por defecto, 90 % de detección.
- Recomendación de OpenCode: microsueno_s = 1.0 s y factor_ear = 0.75. Con los valores por defecto, 75 % de detección.

## Etapa 3: Experimentos

| Campo | Claude Code | OpenCode |
|---|---|---|
| Rama | lab/solarte-emmanuel | — |
| Modelo | Sonnet 5.5 | — |
| Hora inicio | 9:38 | — |
| Hora fin | 9:56 | — |
| Tiempo hasta verde (min) | 18 (duración de la etapa) | — |
| Costo (% de cupo) | No separable por tarea (ver "Costo") | — |
| Intervenciones humanas | 1 (el agente quedó en modo plan y la herramienta de plan dio error al cambiar de modo) | — |
| Iteraciones fallidas | — | — |
| Pruebas nuevas | pytest pasó de 45 a 61 | — |
| Errores graves | — | — |

Hallazgos:

- La CNN obtiene 100 % en prueba pero predice "cerrado" en todo el video, porque los recortes son oscuros (media 38/255) y las clases se capturaron en tandas separadas.
- Las etiquetas del video no coinciden con el guion: los cerrados reales están en 10.0-14.3, 23.7-27.6 y 36.3-39.9 s.

## Costo

El costo de Claude Code no se puede separar por tarea. La sesión completa (configuración, umbrales y experimentos) equivale a USD 1.72 a precios de API (Sonnet 1.24, Opus 0.48, Haiku 0.0004) y usó el 25 % del cupo de la sesión de 5 h de Claude Pro. El subagente `revisor-seguridad` con Opus representó el 18 % del uso de las últimas 24 h.

OpenCode (Big Pickle, OpenCode Zen): USD 0, 58.5K tokens en la etapa de umbrales.

## Prompts clave

PENDIENTE: el estudiante no entregó los prompts. Pegue aquí los que más influyeron (uno por viñeta, indicando etapa y herramienta).

-

## Qué salió mal y cómo se detectó

- **Configuración (Claude Code):** el MCP de mongodb aparecía `failed` en `/mcp` por un timeout de `npx` al arrancar. Se detectó por ejecución (`/mcp`). Se corrigió instalando el servidor de forma global.
- **Experimentos (Claude Code):** el agente quedó en modo plan y la herramienta de plan dio error al cambiar de modo; requirió una intervención humana.
- **Experimentos (CNN):** la CNN obtiene 100 % en prueba pero predice "cerrado" en todo el video (recortes oscuros, clases capturadas en tandas separadas). Se detectó al compararla con el video etiquetado.
- **Experimentos (etiquetas):** las etiquetas del video no coinciden con el guion; los cerrados reales son 10.0-14.3, 23.7-27.6 y 36.3-39.9 s.
- **Revisión de seguridad:** `revisor-seguridad` no reportó hallazgos en la etapa de configuración.

## Conclusión

(escrita por el estudiante)
