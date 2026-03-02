"""
BeermoneyClaude — Telegram Notifier
Sends notifications, morning reports, and alerts via Telegram bot.
Graceful no-op if TELEGRAM_BOT_TOKEN is not configured.
"""

from __future__ import annotations

import asyncio
from typing import Any

from core.config import settings
from core.logger import get_logger

log = get_logger("telegram")


class TelegramNotifier:
    """Sends messages to a Telegram chat. No-op if not configured."""

    def __init__(self) -> None:
        self.token: str = settings.TELEGRAM_BOT_TOKEN
        self.chat_id: str = settings.TELEGRAM_CHAT_ID
        self.enabled: bool = bool(self.token and self.chat_id)
        self._bot: Any = None

        if self.enabled:
            log.info("Telegram notifier enabled")
        else:
            log.warning("Telegram not configured — notifications disabled")

    async def _get_bot(self) -> Any:
        """Lazy-initialize the bot instance."""
        if self._bot is None and self.enabled:
            try:
                from telegram import Bot

                self._bot = Bot(token=self.token)
            except ImportError:
                log.error("python-telegram-bot not installed. Run: pip install python-telegram-bot")
                self.enabled = False
                return None
        return self._bot

    async def send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """Send a text message to the configured chat.

        Returns True if sent, False if failed or not configured.
        """
        if not self.enabled:
            return False

        bot = await self._get_bot()
        if not bot:
            return False

        try:
            await bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode=parse_mode,
            )
            log.debug(f"Telegram sent: {text[:50]}...")
            return True
        except Exception as e:
            log.error(f"Telegram send failed: {e}")
            return False

    async def send_morning_report(
        self,
        pending_tasks: list[dict],
        earnings_today: float = 0.0,
        stats: dict | None = None,
    ) -> bool:
        """Send formatted morning summary report."""
        stats = stats or {}

        lines = [
            "*BeermoneyClaude — Morning Report*",
            "",
            f"*Pending tasks:* `{len(pending_tasks)}`",
            f"*Earnings today:* `{earnings_today:.2f} EUR`",
        ]

        if stats:
            lines.append("")
            lines.append("*Session stats:*")
            for key, value in stats.items():
                lines.append(f"  {key}: `{value}`")

        if pending_tasks:
            lines.append("")
            lines.append("*Queue:*")
            for task in pending_tasks[:10]:  # Show max 10
                title = task.get("task_title", "Unknown")
                platform = task.get("platform_slug", "?")
                pay = task.get("estimated_pay", 0)
                currency = task.get("currency", "EUR")
                urgency = task.get("urgency", "medium")
                emoji = {"critical": "!!", "high": "!", "medium": "-", "low": "."}.get(urgency, "-")
                lines.append(f"  {emoji} [{platform}] {title} (`{pay} {currency}`)")

            if len(pending_tasks) > 10:
                lines.append(f"  ... and {len(pending_tasks) - 10} more")

        return await self.send_message("\n".join(lines))

    async def send_alert(self, message: str, urgency: str = "medium") -> bool:
        """Send an alert notification with urgency prefix."""
        prefix = {
            "critical": "CRITICAL",
            "high": "ALERT",
            "medium": "Notice",
            "low": "Info",
        }.get(urgency, "Notice")

        text = f"*{prefix}:* {message}"
        return await self.send_message(text)

    async def send_queue_update(
        self, task_title: str, platform: str, pay: float, currency: str = "EUR"
    ) -> bool:
        """Notify about a new task added to the human queue."""
        text = (
            f"*New task queued*\n"
            f"Platform: `{platform}`\n"
            f"Task: {task_title}\n"
            f"Pay: `{pay} {currency}`"
        )
        return await self.send_message(text)
