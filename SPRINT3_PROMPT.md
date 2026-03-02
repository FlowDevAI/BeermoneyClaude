# SPRINT 3 — PLUGIN: PROLIFIC (Primera plataforma real)

## CONTEXTO
Estás desarrollando BeermoneyClaude, un agente autónomo de beermoney.
Sprint 0 (estructura) y Sprint 1 (core engine) y Sprint 2 (profiler + telegram + email) están completos.
Lee MASTERPLAN.md si necesitas contexto adicional.

## OBJETIVO
Crear el plugin completo para Prolific — la plataforma más importante (Tier 1).
Prolific es una plataforma de investigación académica donde los "studies" se llenan en minutos.
La velocidad de aceptación es CRÍTICA.

## ENFOQUE: RESEARCH FIRST
IMPORTANTE: No inventes selectores CSS. El approach es:
1. Primero investigar la web real de Prolific
2. Documentar los flujos y selectores reales
3. Solo entonces codificar el plugin

## TAREA 1: Investigar Prolific (modo visible)

Crea un script temporal `engine/scripts/research_prolific.py` que:

```python
"""
Script de investigación para Prolific.
Abre el browser en modo VISIBLE (headless=False) para documentar:
- Flujo de login
- Estructura del dashboard de studies
- Selectores CSS reales
- Flujo de aceptación de study

INSTRUCCIONES:
1. Ejecutar: python scripts/research_prolific.py
2. El browser se abre visible
3. Navega manualmente al login si es necesario
4. El script toma screenshots automáticos de cada página
5. Inspeccionar el DOM para documentar selectores
"""

import asyncio
from playwright.async_api import async_playwright
from pathlib import Path

SCREENSHOTS_DIR = Path("data/screenshots/prolific_research")
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

async def research():
    async with async_playwright() as p:
        # Modo VISIBLE para investigar
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="en-GB",
            timezone_id="Europe/Madrid",
        )
        page = await context.new_page()
        
        # 1. Ir al login
        print("\n📍 Navigating to Prolific...")
        await page.goto("https://app.prolific.com/login", wait_until="networkidle")
        await page.screenshot(path=str(SCREENSHOTS_DIR / "01_login_page.png"))
        print("📸 Screenshot: login page")
        
        # 2. Inspeccionar selectores del login
        print("\n🔍 Inspecting login form selectors...")
        selectors_to_check = [
            # Email field candidates
            'input[type="email"]',
            'input[name="email"]',
            '#email',
            'input[id*="email"]',
            'input[placeholder*="email" i]',
            'input[data-testid*="email"]',
            # Password field candidates
            'input[type="password"]',
            'input[name="password"]',
            '#password',
            'input[data-testid*="password"]',
            # Submit button candidates
            'button[type="submit"]',
            'button[data-testid*="login"]',
            'button[data-testid*="submit"]',
            'button:has-text("Log in")',
            'button:has-text("Sign in")',
            # Google/social login
            'button:has-text("Google")',
            'a[href*="google"]',
        ]
        
        for sel in selectors_to_check:
            try:
                el = await page.query_selector(sel)
                if el:
                    tag = await el.evaluate("e => e.tagName")
                    text = await el.evaluate("e => e.textContent?.trim() || ''")
                    attrs = await el.evaluate("""e => {
                        const a = {};
                        for (const attr of e.attributes) a[attr.name] = attr.value;
                        return a;
                    }""")
                    print(f"  ✅ FOUND: {sel}")
                    print(f"     Tag: {tag}, Text: '{text[:50]}'")
                    print(f"     Attrs: {attrs}")
            except Exception as e:
                pass
        
        # 3. Esperar login manual
        print("\n" + "="*60)
        print("👤 POR FAVOR: Haz login MANUALMENTE en el browser")
        print("   (email + password + 2FA si aplica)")
        print("   Cuando estés en el dashboard, presiona ENTER aquí")
        print("="*60)
        input()
        
        # 4. Documentar dashboard de studies
        await page.screenshot(path=str(SCREENSHOTS_DIR / "02_dashboard.png"), full_page=True)
        print("📸 Screenshot: dashboard")
        
        # 5. Inspeccionar estructura del dashboard
        print("\n🔍 Inspecting dashboard structure...")
        dashboard_selectors = [
            # Study list containers
            '[data-testid*="study"]',
            '[data-testid*="task"]',
            '[class*="study"]',
            '[class*="Study"]',
            '[class*="task"]',
            'article',
            '.card',
            '[role="listitem"]',
            # Study details
            '[data-testid*="reward"]',
            '[data-testid*="time"]',
            '[data-testid*="places"]',
            '[class*="reward"]',
            '[class*="Reward"]',
            # Accept/Reserve button
            'button:has-text("Take part")',
            'button:has-text("Reserve")',
            'button:has-text("Start")',
            'button:has-text("Accept")',
            'a:has-text("Take part")',
            # Navigation
            'nav',
            '[data-testid*="nav"]',
            # User/profile indicators (proves logged in)
            '[data-testid*="user"]',
            '[data-testid*="avatar"]',
            '[data-testid*="profile"]',
            '[class*="avatar"]',
            '[class*="Avatar"]',
            'img[alt*="avatar" i]',
            # Balance
            '[data-testid*="balance"]',
            '[class*="balance"]',
            '[class*="Balance"]',
            # Empty state (no studies)
            '[data-testid*="empty"]',
            '[class*="empty"]',
            '[class*="Empty"]',
            ':text("no studies")',
            ':text("No studies")',
            ':text("check back")',
        ]
        
        for sel in dashboard_selectors:
            try:
                elements = await page.query_selector_all(sel)
                if elements:
                    print(f"\n  ✅ FOUND {len(elements)}x: {sel}")
                    for i, el in enumerate(elements[:3]):  # Max 3 per selector
                        tag = await el.evaluate("e => e.tagName")
                        text = await el.evaluate("e => e.textContent?.trim()?.substring(0, 100) || ''")
                        classes = await el.evaluate("e => e.className || ''")
                        print(f"     [{i}] Tag: {tag}, Class: '{classes[:80]}', Text: '{text[:60]}'")
            except:
                pass
        
        # 6. Extraer HTML de la zona principal (para análisis)
        print("\n🔍 Extracting main content HTML structure...")
        try:
            main_html = await page.evaluate("""() => {
                const main = document.querySelector('main') || document.querySelector('[role="main"]') || document.querySelector('#root > div');
                if (!main) return 'No main element found';
                // Get simplified structure (no inline styles, shortened classes)
                const clone = main.cloneNode(true);
                // Remove script tags
                clone.querySelectorAll('script, style').forEach(e => e.remove());
                return clone.innerHTML.substring(0, 5000);
            }""")
            
            # Save to file for analysis
            with open(str(SCREENSHOTS_DIR / "dashboard_structure.html"), "w", encoding="utf-8") as f:
                f.write(main_html)
            print("  💾 Saved dashboard HTML structure to dashboard_structure.html")
        except Exception as e:
            print(f"  ❌ Error extracting HTML: {e}")
        
        # 7. Intentar navegar a la página de studies directamente
        current_url = page.url
        print(f"\n📍 Current URL: {current_url}")
        
        study_urls = [
            "https://app.prolific.com/studies",
            "https://app.prolific.com/participant/studies", 
            "https://app.prolific.com/studies/active",
        ]
        
        for url in study_urls:
            try:
                print(f"\n📍 Trying: {url}")
                await page.goto(url, wait_until="networkidle", timeout=10000)
                await page.screenshot(path=str(SCREENSHOTS_DIR / f"03_studies_{url.split('/')[-1]}.png"))
                print(f"  Current URL after navigation: {page.url}")
                print(f"  📸 Screenshot saved")
            except Exception as e:
                print(f"  ❌ Error: {e}")
        
        # 8. Resumen final
        print("\n" + "="*60)
        print("📋 RESEARCH COMPLETE")
        print(f"Screenshots saved to: {SCREENSHOTS_DIR}")
        print("\nFiles to review:")
        for f in SCREENSHOTS_DIR.iterdir():
            print(f"  📄 {f.name}")
        print("="*60)
        
        # Mantener browser abierto para inspección manual
        print("\n🔍 Browser stays open for manual inspection.")
        print("   Use DevTools (F12) to inspect elements.")
        print("   Press ENTER to close.")
        input()
        
        await browser.close()

asyncio.run(research())
```

Crea este script y ejecútalo. El browser se abrirá visible para que yo pueda hacer login manualmente.
Los resultados (selectores encontrados + screenshots) se guardan automáticamente.

NOTA: Si no tengo cuenta en Prolific todavía, el script igual documenta el login form.
Si ya tengo cuenta, hago login manual y el script documenta el dashboard.

## TAREA 2: Crear la ficha de plataforma

Basándote en los resultados del script de research, crea:
`engine/docs/PLATFORM_FICHAS/PROLIFIC.md`

Usa esta estructura:

```markdown
# FICHA: Prolific

## Info General
- URL: https://www.prolific.com
- App URL: https://app.prolific.com
- Login URL: https://app.prolific.com/login
- Dashboard URL: [URL real descubierta]
- Tier: 1
- Categoría: research (academic studies)
- Ratio €/h: £6-15 (mínimo legal £6/h, media £9-12/h)
- Moneda: GBP
- Pago: PayPal, circle

## Selectores Descubiertos
(rellenar con los resultados del research script)

### Login
- Email: [selector real]
- Password: [selector real]
- Submit: [selector real]
- Google login: [si existe]

### Verificación logged in
- Selector: [selector que confirma sesión activa]

### Dashboard de Studies
- Container de studies: [selector]
- Study card individual: [selector]
- Título del study: [selector]
- Reward/pago: [selector]
- Tiempo estimado: [selector]
- Plazas disponibles: [selector]
- Botón Take Part: [selector]
- Estado vacío (no studies): [selector o texto]

## Flujo de Login
1. Navegar a login URL
2. Rellenar email
3. Rellenar password
4. Click submit
5. ¿2FA?: [Sí/No — tipo]
6. ¿CAPTCHA?: [Sí/No — tipo]
7. Redirige a: [URL del dashboard]

## Flujo de Aceptación
1. Desde dashboard, cada study muestra: título, reward, tiempo, plazas
2. Click "Take part in this study" (o similar)
3. ¿Redirige a externa?: Sí — Qualtrics, Google Forms, etc.
4. Deadline: varía por study (típico 1-24h)
5. ¿Se puede abandonar?: Sí, "Return submission"

## Clasificación de Tareas
- AUTO: Ninguna (los studies son externos y requieren opinión/interacción humana)
- SEMI_AUTO: Screeners demográficos antes del study
- HUMAN: Todos los studies en sí (encuestas externas)

## Qué puede hacer el agente
1. ✅ Login automático
2. ✅ Detectar studies disponibles
3. ✅ Extraer: título, pay, duración, plazas
4. ✅ Reservar plaza (click "Take part") — VELOCIDAD CRÍTICA
5. ✅ Detectar screener previo y auto-rellenar demográficos
6. ❌ Completar el study en sí (es externo + opiniones)

## Lo que el agente DEBE hacer rápido
Prolific studies se llenan en 1-5 minutos.
El agente debe:
- Scan cada 5-15 minutos (tier 1)
- Al detectar study → accept INMEDIATAMENTE (no calcular score primero)
- Notificar por Telegram con urgencia CRITICAL

## Edge Cases
- Studies que requieren webcam/micrófono → detectar y queue humana
- Studies con prescreening → puede que no seas elegible
- Plazas se llenan → manejar "study full" gracefully
- Prolific puede mostrar "About You" para completar perfil
- Rate limiting: no refrescar más de 1 vez por minuto

## Anti-Bot
- Prolific usa detección moderna
- NO usar intervalos fijos (añadir random jitter)
- NO refrescar agresivamente
- Comportamiento realista: abrir, scrollear, esperar, actuar
```

## TAREA 3: Implementar el plugin

Crea `engine/plugins/prolific.py` basándote en los selectores REALES descubiertos.

El plugin DEBE:

1. **Heredar de PlatformPlugin** (engine/plugins/base.py)
2. **Implementar TODOS los métodos abstractos:**
   - `login(page)` → flujo completo de login
   - `is_logged_in(page)` → verificar sesión activa
   - `scan_available_tasks(page)` → detectar studies en el dashboard
   - `accept_task(page, task)` → click "Take part" rápido
   - `classify_task(task)` → casi todo es HUMAN (studies externos)

3. **Características especiales de Prolific:**
   - `TURBO_MODE`: cuando detecta study, aceptar SIN delay humanizado (velocidad > stealth)
   - Extraer reward en GBP y convertir a EUR estimado (×1.16 aprox)
   - Detectar "places remaining" para urgencia
   - Manejar "study full" (no es error, es normal)
   - Detectar si hay screener previo antes del study externo

4. **Selectores:** 
   - Usar los descubiertos en el research script
   - Si algún selector no se pudo confirmar, marcarlo con `# TODO: VERIFY SELECTOR`
   - Implementar fallbacks (intentar selector A, si falla intentar B)

5. **Logging detallado:**
   - Log cada study detectado con detalles
   - Log cada intento de aceptación
   - Screenshot antes y después de accept

Estructura del archivo:

```python
"""
Prolific Plugin — Tier 1 (Highest Priority)

Prolific is an academic research platform where studies fill up
in minutes. Speed of acceptance is CRITICAL.

IMPORTANT: This plugin prioritizes SPEED over stealth when accepting.
The scan phase uses normal humanized delays, but acceptance is turbo.
"""

import asyncio
import re
from datetime import datetime
from typing import Optional

from playwright.async_api import Page, TimeoutError as PlaywrightTimeout

from plugins.base import (
    PlatformPlugin,
    LoginResult,
    DetectedTask,
    AcceptResult,
    TaskResult,
    TaskDifficulty,
    TaskUrgency,
)
from core.browser import BrowserManager, ElementNotFoundError
from core.logger import get_logger

log = get_logger("prolific")

# GBP to EUR approximate conversion
GBP_TO_EUR = 1.16

class ProlificPlugin(PlatformPlugin):
    name = "prolific"
    display_name = "Prolific"
    url = "https://www.prolific.com"
    login_url = "https://app.prolific.com/login"
    dashboard_url = "https://app.prolific.com/studies"  # TODO: VERIFY URL
    tier = 1
    category = "research"
    check_interval = 900  # 15 minutes
    currency = "GBP"
    
    # === SELECTORS (from research) ===
    # TODO: Replace with REAL selectors from research script
    SELECTORS = {
        # Login
        "login_email": 'input[type="email"]',  # TODO: VERIFY
        "login_password": 'input[type="password"]',  # TODO: VERIFY
        "login_submit": 'button[type="submit"]',  # TODO: VERIFY
        
        # Logged in verification
        "user_indicator": '[data-testid="user-menu"]',  # TODO: VERIFY
        
        # Studies dashboard
        "study_card": '[data-testid="study-card"]',  # TODO: VERIFY
        "study_title": '[data-testid="study-title"]',  # TODO: VERIFY
        "study_reward": '[data-testid="study-reward"]',  # TODO: VERIFY
        "study_time": '[data-testid="study-time"]',  # TODO: VERIFY
        "study_places": '[data-testid="study-places"]',  # TODO: VERIFY
        "take_part_button": 'button:has-text("Take part")',  # TODO: VERIFY
        
        # States
        "no_studies": ':text("No studies available")',  # TODO: VERIFY
        "study_full": ':text("This study is full")',  # TODO: VERIFY
        
        # CAPTCHA
        "captcha_recaptcha": 'iframe[src*="recaptcha"]',
        "captcha_cloudflare": '#cf-challenge-running',
    }
    
    async def login(self, page: Page) -> LoginResult:
        """Login to Prolific."""
        # ... implement based on real selectors
    
    async def is_logged_in(self, page: Page) -> bool:
        """Check if logged into Prolific."""
        # ... check for user indicator
    
    async def scan_available_tasks(self, page: Page) -> list[DetectedTask]:
        """Scan for available studies."""
        # ... scan dashboard, extract study details
    
    async def accept_task(self, page: Page, task: DetectedTask) -> AcceptResult:
        """Accept a study — TURBO MODE (minimal delays)."""
        # ... click take part FAST
    
    async def classify_task(self, task: DetectedTask) -> TaskDifficulty:
        """Almost all Prolific studies are HUMAN (external surveys)."""
        return TaskDifficulty.HUMAN
    
    # === HELPERS ===
    
    def _parse_reward(self, text: str) -> float:
        """Parse reward text like '£8.50' to float."""
        match = re.search(r'[£$€]?\s*([\d.]+)', text)
        return float(match.group(1)) if match else 0.0
    
    def _parse_minutes(self, text: str) -> int:
        """Parse time text like '15 minutes' to int."""
        match = re.search(r'(\d+)\s*min', text, re.IGNORECASE)
        return int(match.group(1)) if match else 0
    
    def _parse_places(self, text: str) -> int:
        """Parse places text like '3 places remaining' to int."""
        match = re.search(r'(\d+)\s*place', text, re.IGNORECASE)
        return int(match.group(1)) if match else -1
    
    def _gbp_to_eur(self, gbp: float) -> float:
        """Convert GBP to EUR estimate."""
        return round(gbp * GBP_TO_EUR, 2)
```

Implementa el plugin completo con:
- Manejo robusto de errores (try/except en cada operación de browser)
- Fallback selectors donde sea posible
- Screenshots automáticos de acciones importantes
- Logging detallado con get_logger("prolific")

## TAREA 4: Integrar con el scheduler

En `engine/core/scheduler.py`, actualiza `_load_active_plugins()` para que:
1. Lea `data/platforms.json`
2. Instancie los plugins que tengan `"active": true`
3. Prolific debe estar activo por defecto para testing

También actualiza `data/platforms.json` para marcar Prolific como:
```json
"plugin_status": "testing",
"active": true
```

## TAREA 5: Crear test script

Crea `engine/scripts/test_prolific.py`:

```python
"""
Test script for Prolific plugin.
Runs in VISIBLE mode for manual verification.

Usage:
    python scripts/test_prolific.py              # Full test
    python scripts/test_prolific.py --login-only  # Just test login
    python scripts/test_prolific.py --scan-only   # Just test scanning
"""

# This script should:
# 1. Initialize browser in VISIBLE mode
# 2. Create ProlificPlugin instance
# 3. Attempt login (may need manual intervention for 2FA/CAPTCHA)
# 4. Scan for studies
# 5. Print found studies in a nice table (Rich)
# 6. Ask user: "Accept a study? [y/N]"
# 7. If yes, attempt accept on first study
# 8. Show results
```

## TAREA 6: Git commit

```bash
git add .
git commit -m "Sprint 3: Prolific plugin - research, ficha, login, scan, accept"
```

## VERIFICACIONES

Después de implementar todo:

1. `python -c "from plugins.prolific import ProlificPlugin; print('Prolific OK')"` → debe importar sin error
2. `python scripts/research_prolific.py` → debe abrir browser visible y documentar selectores
3. `python scripts/test_prolific.py --login-only` → debe poder hacer login (manual si hay CAPTCHA)
4. `python scripts/test_prolific.py --scan-only` → debe mostrar studies disponibles (o "no studies")
5. Verificar que `data/screenshots/prolific_research/` tiene screenshots
6. Verificar que `engine/docs/PLATFORM_FICHAS/PROLIFIC.md` existe y tiene selectores reales

## NOTAS IMPORTANTES

- Los selectores REALES son lo más importante. No inventes. Si el research script no puede encontrar un selector, marca con TODO: VERIFY SELECTOR y usa el mejor candidato.
- Prolific cambia su frontend de vez en cuando. Los selectores pueden necesitar actualización.
- Si Prolific usa un SPA (React/Angular), los selectores pueden ser dinámicos. Usa `page.wait_for_selector()` con timeouts generosos.
- Si hay CAPTCHA en el login, el plugin debe detectarlo y parar (no intentar resolver automáticamente en este sprint).
- Para testing, usa `headless=False` SIEMPRE hasta que todo funcione.
