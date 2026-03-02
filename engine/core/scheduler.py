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

from notifier.telegram_bot import TelegramNotifier
from notifier.alerts import AlertManager

log = get_logger("agent")


def _generate_session_id() -> str:
    return f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"


class NightAgent:
    """Main night agent that orchestrates platform scanning."""

    def __init__(self, duration_minutes: int = 0) -> None:
        self.browser = BrowserManager()
        self.db = Database()
        self.sessions = SessionManager(self.browser, self.db)
        self.queue = HumanQueue(self.db)
        self.telegram = TelegramNotifier()
        self.alerter = AlertManager(self.telegram, self.db)
        self.plugins: list[PlatformPlugin] = []
        self.running: bool = False
        self.session_id: str = _generate_session_id()
        self.duration_minutes: int = duration_minutes  # 0 = use time window
        self._start_time: float = 0.0

        # Session stats
        self.stats = {
            "platforms_scanned": set(),
            "tasks_detected": 0,
            "tasks_accepted": 0,
            "tasks_auto_completed": 0,
            "tasks_queued": 0,
            "errors": 0,
            "scans": [],  # list of {platform, tasks_found, error, timestamp}
        }

    async def start(self) -> None:
        """Start the night agent loop."""
        log.info(f"Night Agent starting (session: {self.session_id})")
        self.running = True
        self._start_time = time.time()

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
            await self.alerter.alert_agent_error(str(e))
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
                    await self.alerter.alert_login_failed(plugin.name, "Login returned False")
            except Exception as e:
                log.error(f"{plugin.name}: Login phase error: {e}")
                await self.alerter.alert_login_failed(plugin.name, str(e))

    async def _scan_tier(self, tier: int) -> None:
        """Scan all platforms in a given tier. Errors are isolated per plugin."""
        tier_plugins = [p for p in self.plugins if p.tier == tier]
        if not tier_plugins:
            return

        log.info(f"Scanning Tier {tier}: {len(tier_plugins)} platforms")

        for plugin in tier_plugins:
            try:
                page = await self.browser.get_page(plugin.name)

                # Verify session is still active
                if not await plugin.is_logged_in(page):
                    log.info(f"{plugin.name}: Session expired, re-logging in...")
                    if not await self.sessions.ensure_logged_in(page, plugin):
                        log.warning(f"{plugin.name}: Re-login failed, skipping")
                        await self.alerter.alert_login_failed(
                            plugin.name, "Session expired and re-login failed"
                        )
                        self._record_scan(plugin.name, 0, error="login_failed")
                        continue

                tasks = await plugin.scan_available_tasks(page)
                log.info(f"{plugin.name}: Found {len(tasks)} tasks")

                # Record scan result
                self._record_scan(plugin.name, len(tasks))

                if tasks:
                    await self.db.update_platform(
                        plugin.name,
                        {"last_task_found_at": datetime.now().isoformat()},
                    )

                for task in tasks:
                    try:
                        await self._process_task(plugin, page, task)
                    except Exception as task_err:
                        log.error(f"{plugin.name}: Error processing task '{task.title}': {task_err}")

                await self.db.update_platform(
                    plugin.name,
                    {"last_scanned_at": datetime.now().isoformat()},
                )

                # Delay between platforms
                await self.browser._human_delay(10, 30)

            except Exception as e:
                log.error(f"{plugin.name}: Scan error: {e}")
                self._record_scan(plugin.name, 0, error=str(e))
                await self.alerter.alert_agent_error(f"{plugin.name} scan failed: {e}")
                try:
                    page = await self.browser.get_page(plugin.name)
                    await self.browser.take_screenshot(page, plugin.name, "scan_error")
                except Exception:
                    pass
                # Continue to next plugin — don't crash the loop
                continue

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

        # Alert for high-urgency tasks
        await self.alerter.alert_new_task(task)

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
            await self.alerter.alert_captcha(plugin.name, captcha)
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
            self.stats["tasks_accepted"] += 1
            difficulty = await plugin.classify_task(task)

            if difficulty == TaskDifficulty.AUTO:
                try:
                    completion = await plugin.auto_complete(page, task)
                    if completion.status == "completed":
                        log.info(f"Auto-completed: {task.title}")
                        self.stats["tasks_auto_completed"] += 1
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
            self.stats["tasks_queued"] += 1
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
            self.stats["tasks_accepted"] += 1
            self.stats["tasks_queued"] += 1
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
        """Dynamically load active plugins from platforms.json."""
        platforms_path = settings.DATA_DIR / "platforms.json"

        if not platforms_path.exists():
            log.warning("platforms.json not found")
            return []

        data = json.loads(platforms_path.read_text(encoding="utf-8"))
        active = [p for p in data.get("platforms", []) if p.get("active")]

        if not active:
            log.warning("No active platforms in platforms.json")
            return []

        plugins: list[PlatformPlugin] = []
        for platform in active:
            slug = platform["slug"]
            try:
                module = import_module(f"plugins.{slug}")
                plugin_class = getattr(module, "Plugin", None)
                if plugin_class and issubclass(plugin_class, PlatformPlugin):
                    instance = plugin_class()
                    plugins.append(instance)
                    log.info(f"Loaded plugin: {instance.display_name} (Tier {instance.tier})")
                else:
                    log.warning(f"Plugin {slug} has no 'Plugin' export")
            except ImportError as e:
                log.warning(f"Plugin module not found: {slug} ({e})")
            except Exception as e:
                log.error(f"Failed to load plugin {slug}: {e}")

        # Sort by tier (1 = highest priority)
        plugins.sort(key=lambda p: p.tier)
        log.info(f"Total plugins loaded: {len(plugins)} of {len(active)} active")
        return plugins

    def _is_active_time(self) -> bool:
        """Check if we're within the configured active hours or duration."""
        # If duration mode is set, use elapsed time instead of clock
        if self.duration_minutes > 0:
            elapsed = time.time() - self._start_time
            return elapsed < (self.duration_minutes * 60)

        hour = datetime.now().hour
        start = settings.NIGHT_START_HOUR
        end = settings.NIGHT_END_HOUR

        if start > end:
            # Overnight window (e.g., 23:00 to 07:00)
            return hour >= start or hour < end
        return start <= hour < end

    def _record_scan(
        self, platform: str, tasks_found: int, error: str = ""
    ) -> None:
        """Record a scan result for the morning report."""
        self.stats["platforms_scanned"].add(platform)
        self.stats["tasks_detected"] += tasks_found
        if error:
            self.stats["errors"] += 1
        self.stats["scans"].append({
            "platform": platform,
            "tasks_found": tasks_found,
            "error": error,
            "timestamp": datetime.now().isoformat(),
        })

    async def _generate_morning_report(self) -> None:
        """Generate and send morning summary via Telegram."""
        elapsed = time.time() - self._start_time if self._start_time else 0
        pending = await self.queue.get_pending()

        # Build summary
        summary_lines = [
            f"Session: {self.session_id}",
            f"Duration: {int(elapsed // 60)}m {int(elapsed % 60)}s",
            f"Plugins loaded: {len(self.plugins)}",
            f"Platforms scanned: {len(self.stats['platforms_scanned'])}",
            f"Total scans: {len(self.stats['scans'])}",
            f"Tasks detected: {self.stats['tasks_detected']}",
            f"Tasks accepted: {self.stats['tasks_accepted']}",
            f"Tasks auto-completed: {self.stats['tasks_auto_completed']}",
            f"Tasks in queue: {len(pending)}",
            f"Errors: {self.stats['errors']}",
        ]

        log.info("=== MORNING REPORT ===")
        for line in summary_lines:
            log.info(f"  {line}")
        log.info("=== END REPORT ===")

        await self.alerter.send_morning_report()

        await self.db.log_event(
            "morning_report",
            message=" | ".join(summary_lines),
            session_id=self.session_id,
        )
