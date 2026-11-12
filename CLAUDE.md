@AGENTS.md

## Notas para Claude Code

- **Modo plan:** use el modo plan (Shift+Tab) antes de cualquier cambio en `core/riesgo.py`, `core/config.py` o el protocolo de emergencia, y antes de tareas que toquen varios módulos. Muestre el plan y espere aprobación.
- **Subagentes** (`.claude/agents/`):
  - `tester`: córrelo para ejecutar `pytest` y obtener solo el resumen de fallos, sin llenar el contexto principal.
  - `revisor-seguridad`: córrelo antes de cada commit; revisa `git diff` y no edita nada.
- **Skills** `driveguard-*` (`.claude/skills/`): úselas para verificar el entorno, correr escenarios, barrer umbrales, analizar videos, entrenar la CNN y armar el informe.
- Los hooks de `.claude/settings.json` corren pytest tras editar y al terminar; si fallan, corrija antes de continuar.
