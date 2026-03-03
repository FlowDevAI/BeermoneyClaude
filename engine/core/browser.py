"""
BeermoneyClaude — Browser Manager
Playwright persistent context with humanized interactions and anti-detection.
"""

from __future__ import annotations

import asyncio
import random
from datetime import datetime

from playwright.async_api import BrowserContext, Page, async_playwright

from .config import settings
from .logger import get_logger

log = get_logger("browser")

# Real Chrome user agents (updated periodically)
USER_AGENTS: list[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.86 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]

VIEWPORTS: list[dict[str, int]] = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1440, "height": 900},
    {"width": 1536, "height": 864},
]


class ElementNotFoundError(Exception):
    """Raised when a page element cannot be found."""

    def __init__(self, selector: str) -> None:
        self.selector = selector
        super().__init__(f"Element not found: {selector}")


class BrowserManager:
    """Manages Chromium with persistent context and human-like behavior."""

    def __init__(self, headless: bool | None = None) -> None:
        self.playwright = None
        self.context: BrowserContext | None = None
        self.pages: dict[str, Page] = {}
        self._user_agent: str = random.choice(USER_AGENTS)
        self._viewport: dict[str, int] = random.choice(VIEWPORTS)
        self._headless: bool = headless if headless is not None else settings.HEADLESS

    async def init(self) -> None:
        """Initialize Playwright with persistent browser context."""
        self.playwright = await async_playwright().start()

        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(settings.SESSIONS_DIR / "browser_profile"),
            headless=self._headless,
            user_agent=self._user_agent,
            viewport=self._viewport,
            locale="es-ES",
            timezone_id="Europe/Madrid",
            args=[
                "--disable-blink-features=AutomationControlled",
            ],
        )

        log.info(
            f"Browser initialized (headless={self._headless}, "
            f"viewport={self._viewport['width']}x{self._viewport['height']})"
        )

    async def close(self) -> None:
        """Close browser gracefully, preserving cookies."""
        for name, page in list(self.pages.items()):
            if not page.is_closed():
                await page.close()
        self.pages.clear()

        if self.context:
            await self.context.close()
        if self.playwright:
            await self.playwright.stop()
        log.info("Browser closed")

    async def get_page(self, platform_name: str) -> Page:
        """Get or create a page for a platform."""
        if platform_name not in self.pages or self.pages[platform_name].is_closed():
            page = await self.context.new_page()
            self.pages[platform_name] = page
            log.debug(f"New page created for {platform_name}")
        return self.pages[platform_name]

    async def close_page(self, platform_name: str) -> None:
        """Close a platform's page."""
        if platform_name in self.pages and not self.pages[platform_name].is_closed():
            await self.pages[platform_name].close()
            del self.pages[platform_name]

    # ─── HUMANIZED INTERACTIONS ───────────────────────────────

    async def safe_navigate(
        self, page: Page, url: str, wait_for: str = "networkidle"
    ) -> None:
        """Navigate to URL with human-like delay."""
        log.debug(f"Navigating to {url}")
        await page.goto(url, wait_until=wait_for, timeout=30000)
        await self._human_delay(2.0, 5.0)

    async def safe_click(
        self, page: Page, selector: str, timeout: int = 10000
    ) -> None:
        """Click with human-like mouse movement."""
        await self._human_delay(0.8, 2.5)

        element = await page.wait_for_selector(selector, timeout=timeout)
        if element:
            box = await element.bounding_box()
            if box:
                target_x = box["x"] + box["width"] / 2 + random.uniform(-3, 3)
                target_y = box["y"] + box["height"] / 2 + random.uniform(-3, 3)
                await page.mouse.move(
                    target_x, target_y, steps=random.randint(5, 15)
                )
                await self._human_delay(0.1, 0.3)

            await element.click()
            log.debug(f"Clicked: {selector}")
        else:
            log.warning(f"Element not found: {selector}")
            raise ElementNotFoundError(selector)

    async def safe_fill(
        self,
        page: Page,
        selector: str,
        text: str,
        humanize: bool = True,
    ) -> None:
        """Type text with human-like character-by-character input."""
        await self._human_delay(0.3, 1.0)

        element = await page.wait_for_selector(selector, timeout=10000)
        if not element:
            raise ElementNotFoundError(selector)

        await element.click()
        await self._human_delay(0.2, 0.5)

        # Clear existing text
        await element.fill("")
        await self._human_delay(0.1, 0.3)

        if humanize:
            for i, char in enumerate(text):
                await element.type(char, delay=random.randint(50, 200))

                # Occasional typo (1 in 30 chars)
                if random.random() < 0.033 and i < len(text) - 1:
                    wrong_char = random.choice("abcdefghijklmnopqrstuvwxyz")
                    await element.type(wrong_char, delay=random.randint(50, 150))
                    await self._human_delay(0.2, 0.5)
                    await page.keyboard.press("Backspace")
                    await self._human_delay(0.1, 0.3)
        else:
            await element.fill(text)

        log.debug(f"Filled: {selector} ({len(text)} chars)")

    async def safe_select(self, page: Page, selector: str, value: str) -> None:
        """Select dropdown option with delay."""
        await self._human_delay(0.5, 1.5)
        await page.select_option(selector, value=value)
        log.debug(f"Selected: {selector} = {value}")

    async def safe_scroll(
        self, page: Page, direction: str = "down", amount: int = 300
    ) -> None:
        """Gradual human-like scrolling."""
        delta = amount if direction == "down" else -amount
        steps = random.randint(3, 6)
        step_amount = delta / steps

        for _ in range(steps):
            await page.mouse.wheel(0, step_amount)
            await self._human_delay(0.1, 0.3)

    # ─── CAPTCHA DETECTION ────────────────────────────────────

    async def detect_captcha(self, page: Page) -> str | None:
        """Detect CAPTCHA on the current page. Returns type or None."""
        captcha_selectors: dict[str, list[str]] = {
            "recaptcha": [
                "iframe[src*='recaptcha']",
                ".g-recaptcha",
                "#recaptcha",
            ],
            "hcaptcha": [
                "iframe[src*='hcaptcha']",
                ".h-captcha",
            ],
            "cloudflare": [
                "iframe[src*='challenges.cloudflare']",
                "#cf-challenge-running",
                ".cf-browser-verification",
            ],
        }

        for captcha_type, selectors in captcha_selectors.items():
            for sel in selectors:
                try:
                    element = await page.query_selector(sel)
                    if element:
                        log.warning(f"CAPTCHA detected: {captcha_type}")
                        return captcha_type
                except Exception:
                    continue

        return None

    # ─── SCREENSHOTS ──────────────────────────────────────────

    async def take_screenshot(
        self, page: Page, platform: str, action: str
    ) -> str:
        """Take a screenshot with descriptive naming."""
        dir_path = (
            settings.SCREENSHOTS_DIR / platform / datetime.now().strftime("%Y-%m-%d")
        )
        dir_path.mkdir(parents=True, exist_ok=True)

        filename = f"{datetime.now().strftime('%H-%M-%S')}_{action}.png"
        filepath = dir_path / filename
        await page.screenshot(path=str(filepath), full_page=False)
        log.debug(f"Screenshot: {filepath}")
        return str(filepath)

    # ─── HELPERS ──────────────────────────────────────────────

    async def _human_delay(self, min_seconds: float, max_seconds: float) -> None:
        """Random delay to simulate human behavior."""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)
