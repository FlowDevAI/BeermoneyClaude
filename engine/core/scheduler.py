"""
BeermoneyClaude — Night Agent Scheduler
Main orchestrator that runs the scanning loop.
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from datetime import datetime
from importlib import import_module
from pathlib import Path

from plugins.base import DetectedTask, PlatformPlugin, TaskDifficulty

from .browser import BrowserManager
from .config import settings
from .db import Database
from .logger import get_logger
from .queue import HumanQueue
from .session import SessionManager

log = get_logger("agent")


def _generate_session_id() -> str:
    return f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"


class NightAgent:
    """Main night agent that orchestrates platform scanning."""

    def __init__(self) -> None:
        self.browser = BrowserManager()
        self.db = Database()
        self.sessions = SessionManager(self.browser, self.db)
        self.queue = HumanQueue(self.db)
        self.plugins: list[PlatformPlugin] = []
        self.running: bool = False
        self.session_id: str = _generate_session_id()

    async def start(self) -> None:
        """Start the night agent loop."""
        log.info(f"Night Agent starting (session: {self.session_id})")
        self.running = True

        try:
            await self.browser.init()
            self.plugins = self._load_active_plugins()
            log.info(f"Loaded {len(self.plugins)} active plugins")

            await self.db.log_event(
                "agent_start",
                message=f"Night Agent started with {len(self.plugins)} plugins",
                session_id=self.session_id,
            )

            # Login phase
            await self._login_all()

            # Main scan loop
            last_check: dict[int, float] = {1: 0, 2: 0, 3: 0, 4: 0}

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
            await self.db.log_event(
                "agent_crash",
                message=str(e),
                level="critical",
                session_id=self.session_id,
            )
        finally:
            await self.browser.close()
            await self.db.log_event(
                "agent_stop",
                message="Night Agent stopped",
                session_id=self.session_id,
            )
            log.info("Night Agent stopped")

    async def stop(self) -> None:
        """Signal the agent to stop gracefully."""
        self.running = False
        log.info("Stop signal received")

    async def _login_all(self) -> None:
        """Login to all active platforms."""
        for plugin in self.plugins:
            try:
                page = await self.browser.get_page(plugin.name)
                success = await self.sessions.ensure_logged_in(page, plugin)
                if not success:
                    log.warning(f"Skipping {plugin.name} (login failed)")
            except Exception as e:
                log.error(f"{plugin.name}: Login phase error: {e}")

    async def _scan_tier(self, tier: int) -> None:
        """Scan all platforms in a given tier."""
        tier_plugins = [p for p in self.plugins if p.tier == tier]
        if not tier_plugins:
            return

        log.info(f"Scanning Tier {tier}: {len(tier_plugins)} platforms")

        for plugin in tier_plugins:
            try:
                page = await self.browser.get_page(plugin.name)

                # Verify session is still active
                if not await plugin.is_logged_in(page):
                    if not await self.sessions.ensure_logged_in(page, plugin):
                        continue

                tasks = await plugin.scan_available_tasks(page)
                log.info(f"{plugin.name}: Found {len(tasks)} tasks")

                if tasks:
                    await self.db.update_platform(
                        plugin.name,
                        {"last_task_found_at": datetime.now().isoformat()},
                    )

                for task in tasks:
                    await self._process_task(plugin, page, task)

                await self.db.update_platform(
                    plugin.name,
                    {"last_scanned_at": datetime.now().isoformat()},
                )

                # Delay between platforms
                await self.browser._human_delay(10, 30)

            except Exception as e:
                log.error(f"{plugin.name}: Scan error: {e}")
                try:
                    page = await self.browser.get_page(plugin.name)
                    await self.browser.take_screenshot(page, plugin.name, "scan_error")
                except Exception:
                    pass

    async def _process_task(
        self,
        plugin: PlatformPlugin,
        page,
        task: DetectedTask,
    ) -> None:
        """Process a single detected task."""
        log.info(
            f"{plugin.name}: Processing '{task.title}' "
            f"({task.estimated_pay} {task.currency})"
        )

        # Log the opportunity
        await self.db.add_opportunity(
            {
                "source": plugin.name,
                "external_id": task.external_id,
                "title": task.title,
                "estimated_pay": task.estimated_pay,
                "currency": task.currency,
                "estimated_minutes": task.estimated_minutes,
                "effective_hourly_rate": task.effective_hourly_rate,
                "url": task.url,
                "status": "detected",
            }
        )

        # Check for CAPTCHA
        captcha = await self.browser.detect_captcha(page)
        if captcha:
            screenshot = await self.browser.take_screenshot(
                page, plugin.name, "captcha"
            )
            await self.queue.add(
                task,
                reason=f"CAPTCHA: {captcha}",
                instructions="Resolve CAPTCHA and complete task",
                screenshot_path=screenshot,
            )
            return

        # Try to accept the task
        result = await plugin.accept_task(page, task)

        if result.success and not result.needs_human:
            difficulty = await plugin.classify_task(task)

            if difficulty == TaskDifficulty.AUTO:
                try:
                    completion = await plugin.auto_complete(page, task)
                    if completion.status == "completed":
                        log.info(f"Auto-completed: {task.title}")
                        await self.db.log_event(
                            "task_auto_completed",
                            platform=plugin.name,
                            message=task.title,
                            session_id=self.session_id,
                        )
                        return
                except NotImplementedError:
                    pass
                except Exception as e:
                    log.error(f"Auto-complete failed: {e}")

            # Queue for human
            screenshot = await self.browser.take_screenshot(
                page, plugin.name, "queued"
            )
            await self.queue.add(
                task,
                reason=result.human_reason or difficulty.value,
                instructions=(
                    result.human_instructions
                    or f"Complete this {task.platform} task"
                ),
                deadline=task.details.get("deadline"),
                screenshot_path=screenshot,
            )

        elif result.success and result.needs_human:
            screenshot = await self.browser.take_screenshot(
                page, plugin.name, "needs_human"
            )
            await self.queue.add(
                task,
                reason=result.human_reason,
                instructions=result.human_instructions,
                screenshot_path=screenshot,
            )

        elif not result.success:
            log.warning(f"Accept failed: {result.error}")
            await self.db.log_event(
                "task_accept_failed",
                platform=plugin.name,
                message=f"{task.title}: {result.error}",
                level="warning",
                session_id=self.session_id,
            )

    def _load_active_plugins(self) -> list[PlatformPlugin]:
        """Load active plugins from platforms.json."""
        platforms_path = settings.DATA_DIR / "platforms.json"

        if not platforms_path.exists():
            log.warning("platforms.json not found")
            return []

        data = json.loads(platforms_path.read_text(encoding="utf-8"))
        active = [p for p in data.get("platforms", []) if p.get("active")]

        plugins: list[PlatformPlugin] = []
        for platform in active:
            slug = platform["slug"]
            try:
                module = import_module(f"plugins.{slug}")
                plugin_class = getattr(module, "Plugin", None)
                if plugin_class and issubclass(plugin_class, PlatformPlugin):
                    plugins.append(plugin_class())
                    log.debug(f"Loaded plugin: {slug}")
            except (ImportError, AttributeError) as e:
                log.debug(f"Plugin not available: {slug} ({e})")

        # Sort by tier (highest priority first)
        plugins.sort(key=lambda p: p.tier)
        return plugins

    def _is_active_time(self) -> bool:
        """Check if we're within the configured active hours."""
        hour = datetime.now().hour
        start = settings.NIGHT_START_HOUR
        end = settings.NIGHT_END_HOUR

        if start > end:
            # Overnight window (e.g., 23:00 to 07:00)
            return hour >= start or hour < end
        return start <= hour < end

    async def _generate_morning_report(self) -> None:
        """Generate and send morning summary. TODO: Telegram integration in Sprint 2."""
        pending = await self.queue.get_pending()
        log.info(
            f"Morning report: {len(pending)} tasks in queue"
        )
        await self.db.log_event(
            "morning_report",
            message=f"{len(pending)} pending tasks",
            session_id=self.session_id,
        )
