"""
BeermoneyClaude — Database Client
Supabase wrapper with local JSON fallback when not configured.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import settings
from .logger import get_logger

log = get_logger("database")

LOCAL_FALLBACK_DIR = settings.DATA_DIR / "local_db"


class Database:
    """Wrapper around Supabase with local JSON fallback."""

    def __init__(self) -> None:
        self.client: Any | None = None
        self.connected: bool = False
        self._init_connection()

    def _init_connection(self) -> None:
        if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
            try:
                from supabase import create_client

                self.client = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_SERVICE_ROLE_KEY,
                )
                self.connected = True
                log.info("Supabase connected")
            except Exception as e:
                log.error(f"Supabase connection failed: {e}")
                self._init_local()
        else:
            log.warning("Supabase not configured — using local JSON fallback")
            self._init_local()

    def _init_local(self) -> None:
        self.connected = False
        LOCAL_FALLBACK_DIR.mkdir(parents=True, exist_ok=True)
        for table in ["agent_logs", "opportunities", "human_queue", "earnings", "platforms", "daily_stats"]:
            path = LOCAL_FALLBACK_DIR / f"{table}.json"
            if not path.exists():
                path.write_text("[]", encoding="utf-8")

    # ─── LOCAL HELPERS ────────────────────────────────────────

    def _local_read(self, table: str) -> list[dict]:
        path = LOCAL_FALLBACK_DIR / f"{table}.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def _local_write(self, table: str, data: list[dict]) -> None:
        path = LOCAL_FALLBACK_DIR / f"{table}.json"
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    def _local_append(self, table: str, record: dict) -> dict:
        records = self._local_read(table)
        record.setdefault("id", f"local-{len(records) + 1}")
        record.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        records.append(record)
        self._local_write(table, records)
        return record

    # ─── AGENT LOGS ───────────────────────────────────────────

    async def log_event(
        self,
        event_type: str,
        platform: str | None = None,
        message: str | None = None,
        details: dict | None = None,
        level: str = "info",
        session_id: str | None = None,
    ) -> dict:
        data = {
            "event_type": event_type,
            "platform_slug": platform,
            "message": message,
            "details": details,
            "level": level,
            "session_id": session_id,
        }
        if self.connected:
            result = self.client.table("agent_logs").insert(data).execute()
            return result.data[0] if result.data else data
        return self._local_append("agent_logs", data)

    # ─── OPPORTUNITIES ────────────────────────────────────────

    async def add_opportunity(self, data: dict) -> dict:
        if self.connected:
            result = self.client.table("opportunities").insert(data).execute()
            return result.data[0] if result.data else data
        return self._local_append("opportunities", data)

    async def update_opportunity(self, opp_id: str, data: dict) -> None:
        if self.connected:
            self.client.table("opportunities").update(data).eq("id", opp_id).execute()
        else:
            records = self._local_read("opportunities")
            for r in records:
                if r.get("id") == opp_id:
                    r.update(data)
                    break
            self._local_write("opportunities", records)

    # ─── HUMAN QUEUE ──────────────────────────────────────────

    async def add_to_queue(self, data: dict) -> dict:
        if self.connected:
            result = self.client.table("human_queue").insert(data).execute()
            return result.data[0] if result.data else data
        return self._local_append("human_queue", data)

    async def get_pending_queue(self) -> list[dict]:
        if self.connected:
            result = (
                self.client.table("human_queue")
                .select("*")
                .eq("status", "pending")
                .order("created_at", desc=False)
                .execute()
            )
            return result.data or []
        records = self._local_read("human_queue")
        return [r for r in records if r.get("status") == "pending"]

    async def mark_queue_done(
        self,
        queue_id: str,
        earnings: float | None = None,
        minutes: int | None = None,
    ) -> None:
        data: dict[str, Any] = {
            "status": "completed",
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
        if earnings is not None:
            data["actual_earnings"] = earnings
        if minutes is not None:
            data["actual_minutes"] = minutes

        if self.connected:
            self.client.table("human_queue").update(data).eq("id", queue_id).execute()
        else:
            records = self._local_read("human_queue")
            for r in records:
                if r.get("id") == queue_id:
                    r.update(data)
                    break
            self._local_write("human_queue", records)

    # ─── EARNINGS ─────────────────────────────────────────────

    async def add_earning(self, data: dict) -> dict:
        if self.connected:
            result = self.client.table("earnings").insert(data).execute()
            return result.data[0] if result.data else data
        return self._local_append("earnings", data)

    # ─── PLATFORMS ────────────────────────────────────────────

    async def get_platform(self, slug: str) -> dict | None:
        if self.connected:
            result = (
                self.client.table("platforms")
                .select("*")
                .eq("slug", slug)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        records = self._local_read("platforms")
        for r in records:
            if r.get("slug") == slug:
                return r
        return None

    async def update_platform(self, slug: str, data: dict) -> None:
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        if self.connected:
            self.client.table("platforms").update(data).eq("slug", slug).execute()
        else:
            records = self._local_read("platforms")
            for r in records:
                if r.get("slug") == slug:
                    r.update(data)
                    break
            self._local_write("platforms", records)
