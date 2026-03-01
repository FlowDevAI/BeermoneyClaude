"""
BeermoneyClaude — Session Manager
Handles login persistence and session verification for platform plugins.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .browser import BrowserManager
from .db import Database
from .logger import get_logger

if TYPE_CHECKING:
    from playwright.async_api import Page

    from plugins.base import PlatformPlugin

log = get_logger("session")


class SessionManager:
    """Manages login and persistent sessions across platforms."""

    def __init__(self, browser: BrowserManager, db: Database) -> None:
        self.browser = browser
        self.db = db
        self.max_login_retries: int = 3

    async def ensure_logged_in(self, page: "Page", plugin: "PlatformPlugin") -> bool:
        """
        Ensure there's an active session. Attempts login if needed.
        Returns True if logged in, False if login failed.
        """
        # 1. Check existing session
        try:
            await self.browser.safe_navigate(page, plugin.dashboard_url)
            if await plugin.is_logged_in(page):
                log.info(f"{plugin.name}: Session active")
                await self.db.update_platform(
                    plugin.name,
                    {"login_status": "ok"},
                )
                return True
        except Exception as e:
            log.debug(f"{plugin.name}: Session check failed: {e}")

        # 2. Attempt login with retries
        for attempt in range(1, self.max_login_retries + 1):
            log.info(f"{plugin.name}: Login attempt {attempt}/{self.max_login_retries}")
            try:
                await self.browser.safe_navigate(page, plugin.login_url)
                result = await plugin.login(page)

                if result.success:
                    log.info(f"{plugin.name}: Login successful")
                    await self.db.update_platform(
                        plugin.name,
                        {"login_status": "ok"},
                    )
                    return True

                if result.needs_captcha:
                    captcha_type = await self.browser.detect_captcha(page)
                    log.warning(
                        f"{plugin.name}: CAPTCHA during login ({captcha_type})"
                    )
                    await self.db.update_platform(
                        plugin.name,
                        {"login_status": "captcha"},
                    )
                    return False

                if result.needs_2fa:
                    log.warning(f"{plugin.name}: 2FA required")
                    await self.db.update_platform(
                        plugin.name,
                        {"login_status": "2fa_required"},
                    )
                    return False

            except Exception as e:
                log.error(f"{plugin.name}: Login error: {e}")
                await self.browser.take_screenshot(
                    page, plugin.name, f"login_error_{attempt}"
                )

            await self.browser._human_delay(5, 10)

        # 3. All retries exhausted
        log.error(
            f"{plugin.name}: Login FAILED after {self.max_login_retries} attempts"
        )
        await self.db.update_platform(
            plugin.name,
            {"login_status": "failed"},
        )
        return False
