"""
BeermoneyClaude — Alert Manager
Orchestrates all notifications with rate limiting.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from core.logger import get_logger

if TYPE_CHECKING:
    from plugins.base import DetectedTask

    from core.db import Database

    from .telegram_bot import TelegramNotifier

log = get_logger("alerts")

# Minimum seconds between alerts of the same type
RATE_LIMIT_SECONDS: int = 300  # 5 minutes


class AlertManager:
    """Central notification hub with rate limiting."""

    def __init__(self, telegram: TelegramNotifier, db: Database) -> None:
        self.telegram = telegram
        self.db = db
        self._last_alert: dict[str, float] = {}

    def _is_rate_limited(self, alert_type: str) -> bool:
        """Check if this alert type was sent recently."""
        last = self._last_alert.get(alert_type, 0)
        if time.time() - last < RATE_LIMIT_SECONDS:
            log.debug(f"Rate limited: {alert_type}")
            return True
        return False

    def _mark_sent(self, alert_type: str) -> None:
        """Record that an alert was just sent."""
        self._last_alert[alert_type] = time.time()

    async def alert_new_task(self, task: DetectedTask) -> None:
        """Alert about a new task if it's high urgency."""
        if task.urgency.value not in ("critical", "high"):
            return

        alert_key = f"new_task:{task.platform}:{task.external_id or task.title}"
        if self._is_rate_limited(alert_key):
            return

        await self.telegram.send_queue_update(
            task_title=task.title,
            platform=task.platform,
            pay=task.estimated_pay,
            currency=task.currency,
        )
        self._mark_sent(alert_key)

    async def alert_login_failed(self, platform: str, reason: str) -> None:
        """Always alert on login failures."""
        alert_key = f"login_failed:{platform}"
        if self._is_rate_limited(alert_key):
            return

        await self.telegram.send_alert(
            f"Login failed for *{platform}*: {reason}",
            urgency="high",
        )
        self._mark_sent(alert_key)

    async def alert_captcha(self, platform: str, captcha_type: str) -> None:
        """Always alert when a CAPTCHA is encountered."""
        alert_key = f"captcha:{platform}"
        if self._is_rate_limited(alert_key):
            return

        await self.telegram.send_alert(
            f"CAPTCHA detected on *{platform}*: {captcha_type}",
            urgency="high",
        )
        self._mark_sent(alert_key)

    async def alert_agent_error(self, error: str) -> None:
        """Alert on critical agent errors."""
        alert_key = "agent_error"
        if self._is_rate_limited(alert_key):
            return

        await self.telegram.send_alert(
            f"Agent error: `{error[:200]}`",
            urgency="critical",
        )
        self._mark_sent(alert_key)

    async def send_morning_report(self) -> None:
        """Aggregate data and send the morning summary via Telegram."""
        pending = await self.db.get_pending_queue()

        # Calculate today's earnings from local DB
        earnings_today = 0.0
        try:
            earnings_records = self.db._local_read("earnings") if not self.db.connected else []
            if self.db.connected:
                from datetime import datetime, timezone

                today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                result = (
                    self.db.client.table("earnings")
                    .select("amount")
                    .gte("created_at", today)
                    .execute()
                )
                earnings_today = sum(r.get("amount", 0) for r in (result.data or []))
            else:
                from datetime import datetime, timezone

                today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                earnings_today = sum(
                    r.get("amount", 0)
                    for r in earnings_records
                    if r.get("created_at", "").startswith(today)
                )
        except Exception as e:
            log.warning(f"Could not calculate earnings: {e}")

        # Session stats from agent logs
        stats: dict[str, int] = {}
        try:
            if not self.db.connected:
                logs = self.db._local_read("agent_logs")
                today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                today_logs = [l for l in logs if l.get("created_at", "").startswith(today)]
                stats["tasks_detected"] = sum(
                    1 for l in today_logs if l.get("event_type") == "task_auto_completed"
                )
                stats["errors"] = sum(
                    1 for l in today_logs if l.get("level") in ("error", "critical")
                )
        except Exception as e:
            log.warning(f"Could not gather stats: {e}")

        await self.telegram.send_morning_report(
            pending_tasks=pending,
            earnings_today=earnings_today,
            stats=stats,
        )
        log.info("Morning report sent")
