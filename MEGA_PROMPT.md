# 🚀 BeermoneyClaude — MEGA PROMPT (Claude Code)

> **Instrucciones de ejecución para Claude Code**
> **Método:** Copiar cada sprint completo → pegar en Claude Code → ejecutar
> **Verificación:** Después de cada sprint, testear antes de pasar al siguiente

---

## INSTRUCCIONES GENERALES PARA CLAUDE CODE

```
Eres el desarrollador principal de BeermoneyClaude, un agente autónomo
que trabaja en plataformas de beermoney (user testing, encuestas, microtareas).

REGLAS:
1. Sigue el MASTERPLAN.md como fuente de verdad
2. Después de cada cambio significativo, verifica que no hay errores de sintaxis
3. Usa type hints en todo el código Python
4. Usa async/await para todo lo que interactúe con el browser
5. Logging con loguru en cada operación importante
6. Manejo de errores robusto (try/except en operaciones de browser)
7. Commits descriptivos después de cada tarea completada
8. NO inventes selectores CSS — marca con # TODO: VERIFY SELECTOR los que no puedas confirmar

STACK PYTHON:
- Python 3.11+
- playwright para browser automation
- loguru para logging
- rich para CLI output
- python-dotenv para config
- pydantic para data models
- cryptography para encriptación
- supabase-py para database
- python-telegram-bot para notificaciones
- httpx para HTTP async

STACK DASHBOARD:
- Next.js 15 (App Router)
- TypeScript
- Tailwind CSS
- shadcn/ui
- Recharts para gráficos
- @supabase/supabase-js
```

---

## SPRINT 0 — SETUP DEL REPO

```
Crea la estructura completa del proyecto BeermoneyClaude.

1. Crea esta estructura de directorios:

BeermoneyClaude/
├── engine/
│   ├── core/
│   ├── plugins/
│   ├── profiler/
│   ├── notifier/
│   ├── scorer/
│   ├── data/
│   │   ├── sessions/
│   │   └── screenshots/
│   ├── tests/
│   │   └── test_plugins/
│   └── docs/
│       └── PLATFORM_FICHAS/
├── dashboard/
│   └── (vacío por ahora)
├── docs/
└── logs/

2. Crea __init__.py en cada paquete Python.

3. Crea requirements.txt:

playwright>=1.49.0
python-dotenv>=1.0.0
rich>=13.0.0
loguru>=0.7.0
python-telegram-bot>=21.0
apscheduler>=3.10.0
supabase>=2.0.0
cryptography>=42.0.0
httpx>=0.27.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
Pillow>=10.0.0

4. Crea pyproject.toml con metadata del proyecto:
- name: beermoney-agent
- version: 0.1.0
- description: "Autonomous agent for beermoney platforms"
- python: ">=3.11"

5. Crea .gitignore:

# Python
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
dist/
build/
venv/
.venv/

# Environment
.env
.env.local

# Data (sensitive)
engine/data/sessions/
engine/data/screenshots/
engine/data/profile.encrypted.json

# Logs
logs/*.log

# Node (dashboard)
node_modules/
.next/
.vercel/

# OS
.DS_Store
Thumbs.db

6. Crea .env.example con TODAS las variables del MASTERPLAN sección 12.

7. Crea README.md profesional:

# 🤖 BeermoneyClaude

> Autonomous agent that works beermoney platforms while you sleep.
> Detects tasks, reserves spots, auto-completes what it can,
> and queues the rest for you with clear instructions.

[Badges: Python 3.11+ | Next.js 15 | Playwright | Supabase | License MIT]

## ⚡ Quick Start

git clone https://github.com/FlowDevAI/BeermoneyClaude.git
cd BeermoneyClaude
cd engine
pip install -r requirements.txt
playwright install chromium
cp ../.env.example ../.env  # Edit with your keys
python setup_wizard.py

# Run
python run.py              # Interactive mode
python run.py --night      # Night agent mode
python run.py --test       # Test browser only

## 🏗 Architecture

[ASCII diagram from MASTERPLAN section 3]

## 📊 Dashboard

[Screenshot placeholder]

## 🔌 Supported Platforms

| Platform | Category | €/h | Status |
|----------|---------|-----|--------|
| Prolific | Research | 9-17 | ✅ Active |
| Respondent | Research | 75-200+ | 🔧 Dev |
| ... | ... | ... | ... |

## ⚠️ Disclaimer

This tool automates task detection and profile filling, NOT task completion.
It never fabricates responses or lies in screeners.

Built by [FLOW DEV AI](https://github.com/FlowDevAI)

Incluye secciones: Features, How It Works, Platforms, Setup, Configuration,
Dashboard, Security, Contributing, License.

8. Inicializa git:
git init
git add .
git commit -m "Initial: project structure, dependencies, README"

9. Verifica que no hay errores de importación:
cd engine && python -c "from core import config; print('OK')"
```

---

## SPRINT 1 — CORE ENGINE

```
Implementa el núcleo del sistema. Después de este sprint, el agente
puede abrir un browser, navegar, tomar screenshots y mantener sesión.

═══════════════════════════════════════════════════════════════
TAREA 1: Config (engine/core/config.py)
═══════════════════════════════════════════════════════════════

from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    SESSIONS_DIR: Path = DATA_DIR / "sessions"
    SCREENSHOTS_DIR: Path = DATA_DIR / "screenshots"
    LOGS_DIR: Path = BASE_DIR.parent / "logs"

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    # Gmail
    GMAIL_ADDRESS: str = ""
    GMAIL_APP_PASSWORD: str = ""

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # Captcha
    TWOCAPTCHA_API_KEY: str = ""

    # Encryption
    ENCRYPTION_KEY: str = ""

    # Agent
    AGENT_MODE: str = "night"     # night | standby | manual
    NIGHT_START_HOUR: int = 23
    NIGHT_END_HOUR: int = 7
    HEADLESS: bool = True
    CHECK_INTERVAL_TIER1: int = 900
    CHECK_INTERVAL_TIER2: int = 1800
    CHECK_INTERVAL_TIER3: int = 3600
    CHECK_INTERVAL_TIER4: int = 3600
    MIN_SCORE_THRESHOLD: int = 30
    SCREENSHOT_RETENTION_DAYS: int = 7

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

# Crear directorios si no existen
for d in [settings.DATA_DIR, settings.SESSIONS_DIR, settings.SCREENSHOTS_DIR, settings.LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)


═══════════════════════════════════════════════════════════════
TAREA 2: Logger (engine/core/logger.py)
═══════════════════════════════════════════════════════════════

from loguru import logger
import sys
from .config import settings

# Remove default handler
logger.remove()

# Console handler (con rich formatting)
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{extra[plugin]:>12}</cyan> | {message}",
    level="INFO",
    colorize=True,
)

# File handler (rotación diaria)
logger.add(
    settings.LOGS_DIR / "agent_{time:YYYY-MM-DD}.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {extra[plugin]:>12} | {message}",
    level="DEBUG",
    rotation="00:00",    # Nueva archivo cada día
    retention="30 days",
    compression="zip",
)

# Configurar default extra
logger = logger.bind(plugin="system")

def get_logger(plugin_name: str):
    """Get a logger instance bound to a specific plugin."""
    return logger.bind(plugin=plugin_name)


═══════════════════════════════════════════════════════════════
TAREA 3: Database client (engine/core/db.py)
═══════════════════════════════════════════════════════════════

Wrapper simple de Supabase con métodos helper:

class Database:
    def __init__(self):
        if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
            self.client = create_client(url, key)
            self.connected = True
        else:
            self.connected = False
            logger.warning("Supabase not configured. Using local storage only.")

    # CRUD helpers para cada tabla:
    async def log_event(self, event_type, platform=None, message=None, details=None, level="info")
    async def add_opportunity(self, data: dict) -> dict
    async def update_opportunity(self, id: str, data: dict)
    async def add_to_queue(self, data: dict) -> dict
    async def get_pending_queue(self) -> list[dict]
    async def mark_queue_done(self, id: str, earnings=None, minutes=None)
    async def add_earning(self, data: dict) -> dict
    async def get_platform(self, slug: str) -> dict | None
    async def update_platform(self, slug: str, data: dict)

    # Si Supabase no está configurado, guardar en JSON local como fallback


═══════════════════════════════════════════════════════════════
TAREA 4: Browser Manager (engine/core/browser.py) — EL MÁS IMPORTANTE
═══════════════════════════════════════════════════════════════

import asyncio
import random
from playwright.async_api import async_playwright, Page, BrowserContext
from datetime import datetime
from .config import settings
from .logger import get_logger

log = get_logger("browser")

# Pool de user agents reales (Chrome en Windows, actualizados)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.86 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]

VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1440, "height": 900},
    {"width": 1536, "height": 864},
]

class BrowserManager:
    """Gestiona Chromium con persistent context y comportamiento humano."""

    def __init__(self):
        self.playwright = None
        self.context: BrowserContext | None = None
        self.pages: dict[str, Page] = {}  # platform_name -> Page
        self._user_agent = random.choice(USER_AGENTS)
        self._viewport = random.choice(VIEWPORTS)

    async def init(self):
        """Inicializa Playwright con persistent context."""
        self.playwright = await async_playwright().start()

        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(settings.SESSIONS_DIR / "browser_profile"),
            headless=settings.HEADLESS,
            user_agent=self._user_agent,
            viewport=self._viewport,
            locale="es-ES",
            timezone_id="Europe/Madrid",
            args=[
                "--disable-blink-features=AutomationControlled",
            ],
        )

        log.info(f"Browser initialized (headless={settings.HEADLESS}, viewport={self._viewport})")

    async def close(self):
        """Cierra browser limpiamente preservando cookies."""
        if self.context:
            await self.context.close()
        if self.playwright:
            await self.playwright.stop()
        log.info("Browser closed")

    async def get_page(self, platform_name: str) -> Page:
        """Obtiene o crea una página para una plataforma."""
        if platform_name not in self.pages or self.pages[platform_name].is_closed():
            page = await self.context.new_page()
            self.pages[platform_name] = page
            log.debug(f"New page created for {platform_name}")
        return self.pages[platform_name]

    async def close_page(self, platform_name: str):
        """Cierra la página de una plataforma."""
        if platform_name in self.pages and not self.pages[platform_name].is_closed():
            await self.pages[platform_name].close()
            del self.pages[platform_name]

    # ─── INTERACCIONES HUMANIZADAS ──────────────────────────

    async def safe_navigate(self, page: Page, url: str, wait_for: str = "networkidle"):
        """Navega a URL con delay humanizado."""
        log.debug(f"Navigating to {url}")
        await page.goto(url, wait_until=wait_for, timeout=30000)
        await self._human_delay(2.0, 5.0)

    async def safe_click(self, page: Page, selector: str, timeout: int = 10000):
        """Click con comportamiento humano."""
        await self._human_delay(0.8, 2.5)

        element = await page.wait_for_selector(selector, timeout=timeout)
        if element:
            box = await element.bounding_box()
            if box:
                target_x = box["x"] + box["width"] / 2 + random.uniform(-3, 3)
                target_y = box["y"] + box["height"] / 2 + random.uniform(-3, 3)
                await page.mouse.move(target_x, target_y, steps=random.randint(5, 15))
                await self._human_delay(0.1, 0.3)

            await element.click()
            log.debug(f"Clicked: {selector}")
        else:
            log.warning(f"Element not found: {selector}")
            raise ElementNotFoundError(selector)

    async def safe_fill(self, page: Page, selector: str, text: str, humanize: bool = True):
        """Escribe texto con comportamiento humano (char a char)."""
        await self._human_delay(0.3, 1.0)

        element = await page.wait_for_selector(selector, timeout=10000)
        if not element:
            raise ElementNotFoundError(selector)

        await element.click()
        await self._human_delay(0.2, 0.5)

        # Limpiar campo existente
        await element.fill("")
        await self._human_delay(0.1, 0.3)

        if humanize:
            for i, char in enumerate(text):
                await element.type(char, delay=random.randint(50, 200))

                # Typo ocasional (1 de cada 30 chars)
                if random.random() < 0.033 and i < len(text) - 1:
                    wrong_char = random.choice("abcdefghijklmnopqrstuvwxyz")
                    await element.type(wrong_char, delay=random.randint(50, 150))
                    await self._human_delay(0.2, 0.5)
                    await page.keyboard.press("Backspace")
                    await self._human_delay(0.1, 0.3)
        else:
            await element.fill(text)

        log.debug(f"Filled: {selector} with {len(text)} chars")

    async def safe_select(self, page: Page, selector: str, value: str):
        """Selecciona opción en dropdown."""
        await self._human_delay(0.5, 1.5)
        await page.select_option(selector, value=value)
        log.debug(f"Selected: {selector} = {value}")

    async def safe_scroll(self, page: Page, direction: str = "down", amount: int = 300):
        """Scroll gradual humanizado."""
        delta = amount if direction == "down" else -amount
        steps = random.randint(3, 6)
        step_amount = delta / steps

        for _ in range(steps):
            await page.mouse.wheel(0, step_amount)
            await self._human_delay(0.1, 0.3)

    # ─── CAPTCHA DETECTION ──────────────────────────────────

    async def detect_captcha(self, page: Page) -> str | None:
        """Detecta CAPTCHA en la página."""
        captcha_selectors = {
            "recaptcha": ["iframe[src*='recaptcha']", ".g-recaptcha", "#recaptcha"],
            "hcaptcha": ["iframe[src*='hcaptcha']", ".h-captcha"],
            "cloudflare": ["iframe[src*='challenges.cloudflare']", "#cf-challenge-running", ".cf-browser-verification"],
        }

        for captcha_type, selectors in captcha_selectors.items():
            for sel in selectors:
                try:
                    element = await page.query_selector(sel)
                    if element:
                        log.warning(f"CAPTCHA detected: {captcha_type}")
                        return captcha_type
                except:
                    continue

        return None

    # ─── SCREENSHOTS ────────────────────────────────────────

    async def take_screenshot(self, page: Page, platform: str, action: str) -> str:
        """Toma screenshot con nombre descriptivo."""
        dir_path = settings.SCREENSHOTS_DIR / platform / datetime.now().strftime("%Y-%m-%d")
        dir_path.mkdir(parents=True, exist_ok=True)

        filename = f"{datetime.now().strftime('%H-%M-%S')}_{action}.png"
        filepath = dir_path / filename
        await page.screenshot(path=str(filepath), full_page=False)
        log.debug(f"Screenshot: {filepath}")
        return str(filepath)

    # ─── HELPERS ────────────────────────────────────────────

    async def _human_delay(self, min_seconds: float, max_seconds: float):
        """Espera un tiempo aleatorio para simular comportamiento humano."""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)

class ElementNotFoundError(Exception):
    def __init__(self, selector: str):
        self.selector = selector
        super().__init__(f"Element not found: {selector}")


═══════════════════════════════════════════════════════════════
TAREA 5: Session Manager (engine/core/session.py)
═══════════════════════════════════════════════════════════════

class SessionManager:
    """Gestiona login y sesiones persistentes."""

    def __init__(self, browser: BrowserManager, db: Database):
        self.browser = browser
        self.db = db
        self.max_login_retries = 3

    async def ensure_logged_in(self, page: Page, plugin) -> bool:
        """
        Asegura que hay sesión activa. Si no, intenta login.
        Returns True si está logueado, False si no se pudo.
        """
        # 1. Verificar sesión existente
        try:
            await self.browser.safe_navigate(page, plugin.dashboard_url)
            if await plugin.is_logged_in(page):
                log.info(f"{plugin.name}: Session active")
                await self.db.update_platform(plugin.name, {"login_status": "ok", "last_login_at": "now()"})
                return True
        except Exception as e:
            log.debug(f"{plugin.name}: Session check failed: {e}")

        # 2. Intentar login
        for attempt in range(1, self.max_login_retries + 1):
            log.info(f"{plugin.name}: Login attempt {attempt}/{self.max_login_retries}")
            try:
                await self.browser.safe_navigate(page, plugin.login_url)
                result = await plugin.login(page)

                if result.success:
                    log.info(f"{plugin.name}: Login successful")
                    await self.db.update_platform(plugin.name, {"login_status": "ok", "last_login_at": "now()"})
                    return True

                if result.needs_captcha:
                    captcha_type = await self.browser.detect_captcha(page)
                    log.warning(f"{plugin.name}: CAPTCHA during login ({captcha_type})")
                    await self.db.update_platform(plugin.name, {"login_status": "captcha"})
                    return False

                if result.needs_2fa:
                    log.warning(f"{plugin.name}: 2FA required")
                    return False

            except Exception as e:
                log.error(f"{plugin.name}: Login error: {e}")
                await self.browser.take_screenshot(page, plugin.name, f"login_error_{attempt}")

            await self.browser._human_delay(5, 10)

        # 3. Login fallido
        log.error(f"{plugin.name}: Login FAILED after {self.max_login_retries} attempts")
        await self.db.update_platform(plugin.name, {"login_status": "failed"})
        return False


═══════════════════════════════════════════════════════════════
TAREA 6: Plugin Base (engine/plugins/base.py)
═══════════════════════════════════════════════════════════════

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime

class TaskDifficulty(str, Enum):
    AUTO = "auto"
    SEMI_AUTO = "semi_auto"
    HUMAN = "human"

class TaskUrgency(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class LoginResult:
    success: bool
    needs_2fa: bool = False
    needs_captcha: bool = False
    error: str | None = None

@dataclass
class DetectedTask:
    platform: str
    external_id: str | None = None
    title: str = ""
    estimated_pay: float = 0.0
    currency: str = "EUR"
    estimated_minutes: int = 0
    effective_hourly_rate: float = 0.0
    difficulty: TaskDifficulty = TaskDifficulty.HUMAN
    urgency: TaskUrgency = TaskUrgency.MEDIUM
    url: str = ""
    details: dict = field(default_factory=dict)
    detected_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self):
        if self.estimated_minutes > 0 and self.estimated_pay > 0:
            self.effective_hourly_rate = round((self.estimated_pay / self.estimated_minutes) * 60, 2)

@dataclass
class AcceptResult:
    success: bool
    needs_human: bool = False
    human_reason: str = ""
    human_instructions: str = ""
    error: str | None = None

@dataclass
class TaskResult:
    task: DetectedTask
    status: str
    action_taken: str
    earnings: float | None = None
    screenshot_path: str | None = None

class PlatformPlugin(ABC):
    """Base class for all platform plugins."""

    name: str = ""
    display_name: str = ""
    url: str = ""
    login_url: str = ""
    dashboard_url: str = ""
    tier: int = 4
    category: str = ""
    check_interval: int = 3600
    currency: str = "EUR"

    @abstractmethod
    async def login(self, page) -> LoginResult: ...

    @abstractmethod
    async def is_logged_in(self, page) -> bool: ...

    @abstractmethod
    async def scan_available_tasks(self, page) -> list[DetectedTask]: ...

    @abstractmethod
    async def accept_task(self, page, task: DetectedTask) -> AcceptResult: ...

    @abstractmethod
    async def classify_task(self, task: DetectedTask) -> TaskDifficulty: ...

    async def auto_complete(self, page, task: DetectedTask) -> TaskResult:
        raise NotImplementedError(f"{self.name} does not support auto_complete")

    async def get_balance(self, page) -> float | None:
        return None

    def __repr__(self):
        return f"<Plugin:{self.name} tier={self.tier}>"


═══════════════════════════════════════════════════════════════
TAREA 7: Human Queue (engine/core/queue.py)
═══════════════════════════════════════════════════════════════

class HumanQueue:
    """Manages tasks that need human intervention."""

    def __init__(self, db: Database):
        self.db = db

    async def add(self, task: DetectedTask, reason: str,
                  instructions: str = "", deadline: str | None = None) -> dict:
        """Add task to human queue."""
        data = {
            "platform_slug": task.platform,
            "task_title": task.title,
            "estimated_pay": task.estimated_pay,
            "currency": task.currency,
            "url": task.url,
            "reason": reason,
            "instructions": instructions,
            "deadline": deadline,
            "urgency": task.urgency.value,
            "status": "pending",
        }
        result = await self.db.add_to_queue(data)
        log.info(f"Added to queue: {task.title} ({reason})")
        return result

    async def get_pending(self) -> list[dict]:
        return await self.db.get_pending_queue()

    async def mark_done(self, queue_id: str, earnings: float = None, minutes: int = None):
        await self.db.mark_queue_done(queue_id, earnings, minutes)

    async def mark_skipped(self, queue_id: str):
        pass  # Update status to 'skipped'

    async def clean_expired(self):
        pass  # Check deadlines, mark expired ones


═══════════════════════════════════════════════════════════════
TAREA 8: Night Agent Scheduler (engine/core/scheduler.py)
═══════════════════════════════════════════════════════════════

Implementa el loop principal del agente nocturno:

class NightAgent:
    """Main night agent that orchestrates everything."""

    def __init__(self):
        self.browser = BrowserManager()
        self.db = Database()
        self.sessions = SessionManager(self.browser, self.db)
        self.queue = HumanQueue(self.db)
        self.plugins: list[PlatformPlugin] = []
        self.running = False
        self.session_id = generate_session_id()  # UUID for this run

    async def start(self):
        """Start the night agent."""
        log.info(f"🌙 Night Agent starting (session: {self.session_id})")
        self.running = True

        try:
            await self.browser.init()
            self.plugins = self._load_active_plugins()
            log.info(f"Loaded {len(self.plugins)} active plugins")

            # Login phase
            await self._login_all()

            # Main loop
            last_check = {1: 0, 2: 0, 3: 0, 4: 0}

            while self.running and self._is_active_time():
                now = time.time()

                for tier in [1, 2, 3, 4]:
                    interval = getattr(settings, f"CHECK_INTERVAL_TIER{tier}")
                    if now - last_check[tier] >= interval:
                        await self._scan_tier(tier)
                        last_check[tier] = now

                await asyncio.sleep(60)

            await self._generate_morning_report()

        except KeyboardInterrupt:
            log.info("Agent stopped by user")
        except Exception as e:
            log.critical(f"Agent crashed: {e}")
        finally:
            await self.browser.close()
            log.info("Night Agent stopped")

    async def _login_all(self):
        for plugin in self.plugins:
            page = await self.browser.get_page(plugin.name)
            success = await self.sessions.ensure_logged_in(page, plugin)
            if not success:
                log.warning(f"Skipping {plugin.name} (login failed)")

    async def _scan_tier(self, tier: int):
        tier_plugins = [p for p in self.plugins if p.tier == tier]
        log.info(f"Scanning Tier {tier}: {len(tier_plugins)} platforms")

        for plugin in tier_plugins:
            try:
                page = await self.browser.get_page(plugin.name)

                if not await plugin.is_logged_in(page):
                    if not await self.sessions.ensure_logged_in(page, plugin):
                        continue

                tasks = await plugin.scan_available_tasks(page)
                log.info(f"{plugin.name}: Found {len(tasks)} tasks")

                if tasks:
                    await self.db.update_platform(plugin.name, {"last_task_found_at": "now()"})

                for task in tasks:
                    await self._process_task(plugin, page, task)

                await self.db.update_platform(plugin.name, {"last_scanned_at": "now()"})
                await self.browser._human_delay(10, 30)

            except Exception as e:
                log.error(f"{plugin.name}: Scan error: {e}")
                await self.browser.take_screenshot(page, plugin.name, "scan_error")

    async def _process_task(self, plugin, page, task: DetectedTask):
        log.info(f"{plugin.name}: Processing '{task.title}' ({task.estimated_pay}{task.currency})")

        # Check for CAPTCHA
        captcha = await self.browser.detect_captcha(page)
        if captcha:
            screenshot = await self.browser.take_screenshot(page, plugin.name, "captcha")
            await self.queue.add(task, reason=f"CAPTCHA: {captcha}",
                                instructions="Resolve CAPTCHA and complete task")
            return

        # Try to accept
        result = await plugin.accept_task(page, task)

        if result.success and not result.needs_human:
            difficulty = await plugin.classify_task(task)

            if difficulty == TaskDifficulty.AUTO:
                try:
                    completion = await plugin.auto_complete(page, task)
                    if completion.status == "completed":
                        log.info(f"✅ Auto-completed: {task.title}")
                        return
                except NotImplementedError:
                    pass
                except Exception as e:
                    log.error(f"Auto-complete failed: {e}")

            screenshot = await self.browser.take_screenshot(page, plugin.name, "queued")
            await self.queue.add(task,
                reason=result.human_reason or difficulty.value,
                instructions=result.human_instructions or f"Complete this {task.platform} task",
                deadline=task.details.get("deadline"))

        elif result.success and result.needs_human:
            await self.queue.add(task,
                reason=result.human_reason,
                instructions=result.human_instructions)

        elif not result.success:
            log.warning(f"Accept failed: {result.error}")

    def _load_active_plugins(self) -> list[PlatformPlugin]:
        # Dynamically import and instantiate plugins
        # based on data/platforms.json "active" flag
        # Sort by tier (1 first)
        pass

    def _is_active_time(self) -> bool:
        hour = datetime.now().hour
        if settings.NIGHT_START_HOUR > settings.NIGHT_END_HOUR:
            return hour >= settings.NIGHT_START_HOUR or hour < settings.NIGHT_END_HOUR
        return settings.NIGHT_START_HOUR <= hour < settings.NIGHT_END_HOUR

    async def _generate_morning_report(self):
        # TODO: Implement in Sprint 5 with Telegram
        log.info("☀️ Morning report generated")


═══════════════════════════════════════════════════════════════
TAREA 9: CLI Entry Point (engine/run.py)
═══════════════════════════════════════════════════════════════

"""
BeermoneyClaude — Entry Point

Usage:
    python run.py                  # Interactive menu
    python run.py --night          # Start night agent
    python run.py --test-browser   # Test browser setup
    python run.py --scan [platform] # Force scan one/all platforms
    python run.py --status         # Show system status
"""

import argparse
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt

console = Console()

async def test_browser():
    """Test that browser works correctly."""
    console.print(Panel("🧪 Testing Browser Setup", style="blue"))

    browser = BrowserManager()
    await browser.init()

    page = await browser.get_page("test")
    await browser.safe_navigate(page, "https://www.google.com")
    screenshot = await browser.take_screenshot(page, "test", "browser_test")

    console.print(f"✅ Browser working! Screenshot: {screenshot}")
    await browser.close()

async def main():
    parser = argparse.ArgumentParser(description="BeermoneyClaude Agent")
    parser.add_argument("--night", action="store_true", help="Start night agent")
    parser.add_argument("--test-browser", action="store_true", help="Test browser")
    parser.add_argument("--scan", nargs="?", const="all", help="Force scan")
    parser.add_argument("--status", action="store_true", help="Show status")
    args = parser.parse_args()

    # Banner
    console.print(Panel.fit(
        "[bold cyan]🤖 BeermoneyClaude[/bold cyan]\n"
        "[dim]Autonomous Beermoney Agent[/dim]",
        border_style="cyan"
    ))

    if args.test_browser:
        await test_browser()
    elif args.night:
        agent = NightAgent()
        await agent.start()
    elif args.status:
        pass  # Show platform status table
    else:
        console.print("\n[bold]What do you want to do?[/bold]\n")
        console.print("  1. 🌙 Start Night Agent")
        console.print("  2. 🧪 Test Browser")
        console.print("  3. 🔍 Force Scan")
        console.print("  4. 📊 Status")
        console.print("  5. ⚙️  Setup Wizard")
        console.print("  6. 🚪 Exit\n")

        choice = Prompt.ask("Select", choices=["1","2","3","4","5","6"])
        # ... handle choices

if __name__ == "__main__":
    asyncio.run(main())


═══════════════════════════════════════════════════════════════
TAREA 10: Platforms JSON (engine/data/platforms.json)
═══════════════════════════════════════════════════════════════

Crea el archivo JSON con TODAS las plataformas del catálogo del MASTERPLAN
sección 9. Cada plataforma tiene esta estructura:

{
  "platforms": [
    {
      "slug": "prolific",
      "name": "Prolific",
      "url": "https://www.prolific.com",
      "login_url": "https://app.prolific.com/login",
      "dashboard_url": "https://app.prolific.com/studies",
      "category": "research",
      "tier": 1,
      "avg_pay_min": 9,
      "avg_pay_max": 17,
      "currency": "GBP",
      "payment_methods": ["paypal"],
      "frequency": "daily",
      "spain_available": true,
      "plugin_status": "planned",
      "active": false,
      "check_interval_seconds": 900,
      "notes": "Studies fill up in minutes. Fast acceptance is critical."
    },
    ...incluir las 26 plataformas del catálogo...
  ]
}

═══════════════════════════════════════════════════════════════
VERIFICACIÓN FINAL SPRINT 1:
═══════════════════════════════════════════════════════════════

Ejecuta estas verificaciones:

1. cd engine && python -c "from core.config import settings; print(settings.BASE_DIR)"
2. cd engine && python -c "from core.logger import get_logger; log = get_logger('test'); log.info('Hello')"
3. cd engine && python -c "from plugins.base import PlatformPlugin, DetectedTask; print('OK')"
4. cd engine && python run.py --test-browser
   → Debe abrir Chromium, navegar a Google, tomar screenshot, cerrar
5. Verificar que data/screenshots/test/ tiene el screenshot
6. Verificar que data/sessions/browser_profile/ existe (cookies persistentes)

git add . && git commit -m "Sprint 1: Core engine - browser, sessions, plugin base, CLI"
```

---

## SPRINT 2 — PROFILER + TELEGRAM + EMAIL MONITOR

> Se copia como prompt separado cuando Sprint 1 esté verificado.
> Disponible en el MASTERPLAN bajo la descripción del Sprint 2.

---

## SPRINT 3 — PLUGIN: PROLIFIC (primera plataforma real)

> Este es el sprint más importante.
> INSTRUCCIÓN CLAVE: Antes de codificar, navegar a Prolific REAL
> con `python run.py --test-browser`, documentar selectores reales,
> y crear la ficha PROLIFIC.md.
>
> Se copia como prompt separado.

---

## NOTAS PARA SPRINTS POSTERIORES

Cada sprint posterior sigue el mismo patrón:

1. RESEARCH: Navegar la plataforma real con Playwright visible
2. FICHA: Documentar en engine/docs/PLATFORM_FICHAS/{PLATFORM}.md
3. CÓDIGO: Implementar plugin siguiendo la base
4. TEST: Ejecutar contra la plataforma real (modo visible)
5. AJUSTE: Corregir selectores, edge cases
6. COMMIT: "{Platform} plugin: login, scan, accept"

Los sprints 6-7 (Dashboard) siguen la metodología EnRuta:
- Create Next.js app
- shadcn init
- Layout + pages
- Supabase integration
- Deploy Vercel
- Redesign visual

---

> **RECUERDA:** Ejecuta un sprint, verifica que funciona,
> y SOLO ENTONCES pasa al siguiente. No saltes sprints.
