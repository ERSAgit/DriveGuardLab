---
name: driveguard-informe
description: Reúne los resultados/*.md y la bitácora agéntica en un borrador de informe docs/informe_borrador.md. Úsala al final, cuando los experimentos ya corrieron.
---

# Informe borrador

No cree notebooks ni nuevos experimentos: esta skill solo reúne material existente.

1. Liste `resultados/*.md` (esperados: `escenarios.md`, `umbrales.md`, `video.md`, `cnn.md`). Anote cuáles faltan; no los genere por su cuenta, sugiera la skill correspondiente (`driveguard-escenarios`, `driveguard-umbrales`, `driveguard-video`, `driveguard-cnn`).
2. Lea `docs/bitacora_agentica.md`. Si está vacía (solo la plantilla), avise y continúe marcando esa sección como pendiente.
3. Cree `docs/informe_borrador.md` con esta estructura:
   - **Resumen** (5 líneas: qué se hizo y hallazgos principales).
   - **Método:** entorno, semilla fija, `ConfigRiesgo` por defecto, escenarios y datos usados.
   - **Resultados:** una subsección por archivo de `resultados/`, con sus tablas y referencia a las figuras (`![...](../resultados/xxx.png)`) y a los CSV.
   - **Comparación Claude Code vs OpenCode:** resumen de las tablas de la bitácora (tiempo hasta verde, costo, intervenciones, errores graves).
   - **Qué salió mal y cómo se detectó** (de la bitácora).
   - **Limitaciones y ética:** prototipo académico, datos sintéticos, sin imágenes de rostros en el repositorio.
   - **Conclusiones.**
4. Copie cifras exactamente de los archivos fuente; no invente ni redondee valores. Marque con `PENDIENTE:` todo lo que no se pueda completar.
5. No incluya contenido de `.env`, credenciales ni rutas con datos personales. Revise que no se hayan añadido imágenes de rostros con `git status`.
6. Termine con la lista de archivos fuente usados y los faltantes.
