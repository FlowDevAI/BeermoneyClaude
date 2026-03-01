"""
BeermoneyClaude — Human Queue
Manages tasks that require human intervention.
"""

from __future__ import annotations

from plugins.base import DetectedTask

from .db import Database
from .logger import get_logger

log = get_logger("queue")


class HumanQueue:
    """Queue of tasks that need a human to complete."""

    def __init__(self, db: Database) -> None:
        self.db = db

    async def add(
        self,
        task: DetectedTask,
        reason: str,
        instructions: str = "",
        deadline: str | None = None,
        screenshot_path: str | None = None,
    ) -> dict:
        """Add a task to the human queue."""
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
            "screenshot_path": screenshot_path,
            "status": "pending",
        }
        result = await self.db.add_to_queue(data)
        log.info(f"Added to queue: {task.title} ({reason})")
        return result

    async def get_pending(self) -> list[dict]:
        """Get all pending tasks in the queue."""
        return await self.db.get_pending_queue()

    async def mark_done(
        self,
        queue_id: str,
        earnings: float | None = None,
        minutes: int | None = None,
    ) -> None:
        """Mark a queued task as completed."""
        await self.db.mark_queue_done(queue_id, earnings, minutes)
        log.info(f"Queue item {queue_id} marked done")

    async def mark_skipped(self, queue_id: str) -> None:
        """Mark a queued task as skipped."""
        if self.db.connected:
            self.db.client.table("human_queue").update(
                {"status": "skipped"}
            ).eq("id", queue_id).execute()
        else:
            records = self.db._local_read("human_queue")
            for r in records:
                if r.get("id") == queue_id:
                    r["status"] = "skipped"
                    break
            self.db._local_write("human_queue", records)
        log.info(f"Queue item {queue_id} skipped")

    async def clean_expired(self) -> int:
        """Check deadlines and mark expired tasks. Returns count of expired."""
        from datetime import datetime, timezone

        pending = await self.get_pending()
        expired_count = 0

        for item in pending:
            deadline = item.get("deadline")
            if deadline:
                try:
                    deadline_dt = datetime.fromisoformat(deadline)
                    if deadline_dt < datetime.now(timezone.utc):
                        queue_id = item["id"]
                        if self.db.connected:
                            self.db.client.table("human_queue").update(
                                {"status": "expired"}
                            ).eq("id", queue_id).execute()
                        else:
                            records = self.db._local_read("human_queue")
                            for r in records:
                                if r.get("id") == queue_id:
                                    r["status"] = "expired"
                                    break
                            self.db._local_write("human_queue", records)
                        expired_count += 1
                        log.info(f"Queue item {queue_id} expired")
                except (ValueError, TypeError):
                    continue

        return expired_count
