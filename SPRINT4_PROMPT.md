# SPRINT 4 — PLUGIN: CLICKWORKER + NIGHT AGENT LOOP

## CONTEXTO
Estás desarrollando BeermoneyClaude, un agente autónomo de beermoney.
Sprints 0-3 completos (core engine, profiler, telegram, email monitor, prolific plugin).
Lee MASTERPLAN.md si necesitas contexto adicional.

Prolific está pendiente de verificar selectores (cuenta con restricciones temporales).
Avanzamos con la siguiente plataforma: Clickworker.

## OBJETIVO
1. Crear plugin completo para Clickworker (Tier 3 — microtareas diarias)
2. Hacer funcional el Night Agent loop con múltiples plugins
3. Testear un ciclo corto real con al menos 1 plataforma

## POR QUÉ CLICKWORKER
- No tiene waitlist — registro inmediato
- Tiene tareas diarias (no esporádico como Prolific)
- Incluye UHRS (Microsoft) que paga decente
- Buen candidato para tareas AUTO (categorización simple)
- Nos permite testear el loop nocturno con tareas reales

---

## TAREA 1: Research Clickworker

Crea `engine/scripts/research_clickworker.py` siguiendo el mismo patrón del research de Prolific.

El script debe:
1. Abrir browser VISIBLE (headless=False)
2. Navegar a https://www.clickworker.com y al login
3. Documentar selectores del login form
4. Esperar login manual del usuario
5. Documentar el dashboard de tareas (workplace)
6. Buscar:
   - Container de tareas/jobs disponibles
   - Título de cada tarea
   - Pago por tarea
   - Tipo de tarea (UHRS, clickworker native, etc.)
   - Botón para empezar/aceptar tarea
   - Saldo/balance del usuario
   - Estado cuando no hay tareas
7. Inspeccionar si hay sección UHRS y cómo se accede
8. Tomar screenshots de todo
9. Guardar HTML structure del dashboard
10. Mantener browser abierto para inspección manual con F12

URLs importantes a probar:
- https://www.clickworker.com/login
- https://workplace.clickworker.com/
- https://workplace.clickworker.com/en/jobs
- https://www.clickworker.com/en/clickworker (profile)

NOTA IMPORTANTE: Clickworker tiene una zona "workplace" separada del marketing site.
El workplace es donde están las tareas reales.

## TAREA 2: Ficha de plataforma

Crear `engine/docs/PLATFORM_FICHAS/CLICKWORKER.md` basado en los resultados del research.

Incluir:
```markdown
# FICHA: Clickworker

## Info General
- URL: https://www.clickworker.com
- Workplace URL: https://workplace.clickworker.com
- Login URL: [descubierta]
- Tier: 3
- Categoría: microtasks
- Ratio €/h: 5-15€
- Moneda: EUR
- Pago: PayPal, SEPA (mínimo 5€)
- Frecuencia: Diaria

## Selectores Descubiertos
### Login
- Email: [selector real]
- Password: [selector real]
- Submit: [selector real]

### Verificación logged in
- Selector: [selector real]

### Dashboard / Workplace
- Container de jobs: [selector]
- Job card individual: [selector]
- Título: [selector]
- Pago: [selector]
- Tipo: [selector]
- Botón start: [selector]
- Estado vacío: [selector]

### UHRS
- Enlace a UHRS: [selector]
- Cómo acceder: [flujo]

## Tipos de Tareas
- Categorización de textos/imágenes → AUTO posible
- Transcripción simple → SEMI_AUTO
- Evaluación de búsqueda (UHRS) → SEMI_AUTO/HUMAN
- Encuestas → HUMAN
- Escritura creativa → HUMAN

## Edge Cases
- Cualificaciones necesarias para ciertas tareas
- Assessments previos (tests de prueba)
- UHRS tiene su propia interfaz dentro de Clickworker
- Tareas con deadline
- Límite de tareas por día
```

## TAREA 3: Plugin Clickworker

Crear `engine/plugins/clickworker.py`:

```python
"""
Clickworker Plugin — Tier 3 (Microtasks)

Clickworker offers daily microtasks including UHRS (Microsoft) tasks.
Some tasks are auto-completable (simple categorization),
others need human judgment.

Key features:
- Daily availability (not sporadic like Prolific)
- Mix of AUTO and HUMAN tasks
- UHRS integration for search evaluation tasks
- Assessments required for some task types
"""

from plugins.base import (
    PlatformPlugin, LoginResult, DetectedTask,
    AcceptResult, TaskResult, TaskDifficulty, TaskUrgency,
)
from core.browser import BrowserManager
from core.logger import get_logger

log = get_logger("clickworker")

class ClickworkerPlugin(PlatformPlugin):
    name = "clickworker"
    display_name = "Clickworker"
    url = "https://www.clickworker.com"
    login_url = "https://workplace.clickworker.com/en/login"  # TODO: VERIFY
    dashboard_url = "https://workplace.clickworker.com/en/jobs"  # TODO: VERIFY
    tier = 3
    category = "microtasks"
    check_interval = 3600  # 60 min
    currency = "EUR"

    SELECTORS = {
        # TODO: Fill with REAL selectors from research
    }

    # Implement all abstract methods:
    # - login(page) → email/password login
    # - is_logged_in(page)
    # - scan_available_tasks(page) → list jobs in workplace
    # - accept_task(page, task) → start job
    # - classify_task(task):
    #     - "categorization", "tagging" → AUTO
    #     - "transcription", "uhrs" → SEMI_AUTO
    #     - "survey", "writing", "evaluation" → HUMAN

# IMPORTANT: Export alias for auto-discovery
Plugin = ClickworkerPlugin
```

Implementa completo con:
- Login robusto con retry
- Scan que detecte todos los jobs disponibles
- Clasificación inteligente por tipo de tarea
- Detección de assessments requeridos
- Detección de UHRS vs native tasks
- Logging detallado + screenshots

## TAREA 4: Night Agent Loop funcional

Actualiza `engine/core/scheduler.py` para que el loop nocturno sea completamente funcional:

### 4a. Plugin Discovery
`_load_active_plugins()` debe:
1. Leer `data/platforms.json`
2. Filtrar solo `"active": true`
3. Para cada plataforma activa, intentar importar `plugins/{slug}.py`
4. Verificar que el módulo exporta `Plugin` (alias de la clase)
5. Instanciar y devolver lista ordenada por tier (1 primero)
6. Log de cada plugin cargado y cada error de carga

```python
def _load_active_plugins(self) -> list[PlatformPlugin]:
    """Dynamically load active plugins from platforms.json."""
    import json
    from importlib import import_module

    platforms_file = settings.DATA_DIR / "platforms.json"
    with open(platforms_file) as f:
        data = json.load(f)

    plugins = []
    for p in data["platforms"]:
        if not p.get("active", False):
            continue
        slug = p["slug"]
        try:
            module = import_module(f"plugins.{slug}")
            plugin_class = getattr(module, "Plugin", None)
            if plugin_class:
                instance = plugin_class()
                plugins.append(instance)
                log.info(f"Loaded plugin: {instance.display_name} (Tier {instance.tier})")
            else:
                log.warning(f"Plugin {slug} has no 'Plugin' export")
        except Exception as e:
            log.error(f"Failed to load plugin {slug}: {e}")

    # Sort by tier (1 = highest priority)
    plugins.sort(key=lambda p: p.tier)
    return plugins
```

### 4b. Robust scan loop
Actualiza `_scan_tier()` para que:
- Si un plugin falla, los demás continúen (isolate errors)
- Registre cada scan en Supabase (o JSON local)
- Envíe alertas por Telegram cuando:
  - Detecta tarea de alta urgencia
  - Login falla
  - CAPTCHA detectado
  - Error inesperado

### 4c. Morning report
Implementa `_generate_morning_report()` que:
1. Recopile stats de la sesión nocturna:
   - Plataformas escaneadas
   - Tareas detectadas
   - Tareas aceptadas
   - Tareas completadas (auto)
   - Tareas en cola humana
   - Errores encontrados
2. Envíe resumen por Telegram con formato limpio
3. Guarde resumen en logs

### 4d. Short cycle mode
Añade un modo de ciclo corto para testing:
```python
python run.py --night --duration 30  # Solo 30 minutos de ciclo (para testing)
```

## TAREA 5: Test script Clickworker

Crear `engine/scripts/test_clickworker.py` igual que el de Prolific:
- Modo visible
- Login manual si necesario
- Scan y mostrar tareas en tabla Rich
- Opción de aceptar una tarea

## TAREA 6: Test del Night Agent Loop

Crear `engine/scripts/test_night_loop.py`:

```python
"""
Test the Night Agent loop with a short cycle.
Runs for 5 minutes with all active plugins.

Usage:
    python scripts/test_night_loop.py              # 5 min test
    python scripts/test_night_loop.py --duration 1  # 1 min test
"""

# This script should:
# 1. Set HEADLESS=False for visible debugging
# 2. Start NightAgent with a short duration override
# 3. Let it scan all active plugins once
# 4. Show results in Rich table
# 5. Generate a mini morning report
# 6. Print summary of what happened
```

## TAREA 7: Actualizar platforms.json

Actualizar `data/platforms.json`:
- Clickworker: `"active": true, "plugin_status": "testing"`
- Prolific: mantener `"active": true, "plugin_status": "testing"`
  (cuando resolvamos la restricción de cuenta, ya está listo)

## TAREA 8: Git commit

```bash
git add .
git commit -m "Sprint 4: Clickworker plugin + functional night agent loop"
git push
```

## VERIFICACIONES

1. `python -c "from plugins.clickworker import Plugin; print('Clickworker OK')"` → sin error
2. `python scripts/research_clickworker.py` → browser visible, documenta selectores
3. `python scripts/test_clickworker.py --login-only` → login funcional
4. `python scripts/test_clickworker.py --scan-only` → muestra tareas disponibles
5. `python scripts/test_night_loop.py --duration 1` → ejecuta ciclo corto, escanea plugins activos, genera mini report
6. `python run.py --status` → muestra ambos plugins activos
7. Ficha en engine/docs/PLATFORM_FICHAS/CLICKWORKER.md tiene selectores reales
8. Screenshots en data/screenshots/clickworker_research/

## NOTAS CRÍTICAS

- RESEARCH FIRST: no inventes selectores. Ejecuta el research script primero.
- Clickworker tiene workplace separado del marketing site — las tareas están en workplace.clickworker.com
- UHRS (Microsoft) se accede DESDE Clickworker — es una sección especial, no un site separado
- Algunas tareas requieren "assessments" (tests previos) — el plugin debe detectar esto
- El Night Agent loop debe ser robusto: un plugin que falle NO debe crashear los demás
- Para testing del loop nocturno, usa --duration para ciclos cortos
- Credenciales de Clickworker: el usuario se registrará manualmente antes de ejecutar
