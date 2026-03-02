"""
BeermoneyClaude — Email Monitor
Gmail IMAP daemon that detects platform invitation emails.
Uses only stdlib (imaplib + email) — no extra dependencies.
"""

from __future__ import annotations

import asyncio
import email
import imaplib
import re
from dataclasses import dataclass, field
from datetime import datetime
from email.header import decode_header
from typing import Callable

from core.config import settings
from core.logger import get_logger

log = get_logger("email")

# Platform sender patterns (from address or subject keywords)
PLATFORM_PATTERNS: dict[str, list[str]] = {
    "prolific": ["prolific.co", "prolific.ac", "prolificacademic"],
    "respondent": ["respondent.io", "respondent"],
    "usertesting": ["usertesting.com", "usertesting"],
    "userinterviews": ["userinterviews.com", "user interviews"],
    "clickworker": ["clickworker.com", "clickworker"],
    "appen": ["appen.com", "connect.appen"],
    "mturk": ["mturk.com", "mechanical turk", "amazon mechanical"],
    "testingtime": ["testingtime.com", "testingtime"],
    "intellizoom": ["intellizoom.com", "intellizoom"],
    "userlytics": ["userlytics.com", "userlytics"],
    "trymyui": ["trymyui.com", "trymyui"],
    "testbirds": ["testbirds.com", "testbirds"],
    "utest": ["utest.com", "applause"],
    "dscout": ["dscout.com", "dscout"],
    "validately": ["validately.com", "validately"],
}

# Subject keywords that indicate an actionable invitation
ACTION_KEYWORDS: list[str] = [
    "new study",
    "new task",
    "invitation",
    "invited",
    "available",
    "opportunity",
    "qualify",
    "selected",
    "new project",
    "action required",
    "nuevo estudio",
    "nueva tarea",
    "invitacion",
]


@dataclass
class ParsedEmail:
    """Structured data extracted from a platform email."""

    platform: str
    subject: str
    sender: str
    action_needed: str = ""
    deadline: str | None = None
    received_at: str = field(default_factory=lambda: datetime.now().isoformat())


class EmailMonitor:
    """Monitors Gmail IMAP for platform invitation emails."""

    CHECK_INTERVAL: int = 300  # 5 minutes

    def __init__(self) -> None:
        self.address: str = settings.GMAIL_ADDRESS
        self.password: str = settings.GMAIL_APP_PASSWORD
        self.enabled: bool = bool(self.address and self.password)
        self._mail: imaplib.IMAP4_SSL | None = None
        self._running: bool = False

        if self.enabled:
            log.info("Email monitor enabled")
        else:
            log.warning("Gmail not configured — email monitoring disabled")

    def _connect(self) -> bool:
        """Connect to Gmail IMAP."""
        try:
            self._mail = imaplib.IMAP4_SSL("imap.gmail.com")
            self._mail.login(self.address, self.password)
            log.info("Gmail IMAP connected")
            return True
        except Exception as e:
            log.error(f"Gmail connection failed: {e}")
            self._mail = None
            return False

    def _disconnect(self) -> None:
        """Disconnect from IMAP."""
        if self._mail:
            try:
                self._mail.logout()
            except Exception:
                pass
            self._mail = None

    async def start_monitoring(
        self, callback: Callable[[ParsedEmail], None]
    ) -> None:
        """Start the email monitoring loop. Calls callback for each detected invitation."""
        if not self.enabled:
            log.warning("Email monitor not started — not configured")
            return

        self._running = True
        log.info("Email monitoring started")

        while self._running:
            try:
                emails = await asyncio.to_thread(self.check_inbox)
                for parsed in emails:
                    callback(parsed)
            except Exception as e:
                log.error(f"Email check error: {e}")
                self._disconnect()

            await asyncio.sleep(self.CHECK_INTERVAL)

    def stop(self) -> None:
        """Signal the monitor to stop."""
        self._running = False
        self._disconnect()
        log.info("Email monitoring stopped")

    def check_inbox(self) -> list[ParsedEmail]:
        """Check for unread platform emails. Returns list of parsed emails."""
        if not self._mail:
            if not self._connect():
                return []

        results: list[ParsedEmail] = []

        try:
            self._mail.select("INBOX")
            _, message_ids = self._mail.search(None, "UNSEEN")

            if not message_ids[0]:
                return []

            ids = message_ids[0].split()
            log.debug(f"Found {len(ids)} unread emails")

            for msg_id in ids:
                _, msg_data = self._mail.fetch(msg_id, "(RFC822)")
                if not msg_data or not msg_data[0]:
                    continue

                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                parsed = self._parse_email(msg)

                if parsed:
                    results.append(parsed)
                    # Mark as read
                    self._mail.store(msg_id, "+FLAGS", "\\Seen")
                    log.info(f"Platform email detected: [{parsed.platform}] {parsed.subject}")

        except imaplib.IMAP4.abort:
            log.warning("IMAP connection lost, will reconnect next cycle")
            self._disconnect()
        except Exception as e:
            log.error(f"Inbox check error: {e}")

        return results

    def _parse_email(self, msg: email.message.Message) -> ParsedEmail | None:
        """Parse an email and check if it's from a known platform."""
        sender = self._decode_header(msg.get("From", ""))
        subject = self._decode_header(msg.get("Subject", ""))

        sender_lower = sender.lower()
        subject_lower = subject.lower()

        # Identify platform
        platform = self._identify_platform(sender_lower, subject_lower)
        if not platform:
            return None

        # Check if subject indicates an actionable invitation
        is_actionable = any(kw in subject_lower for kw in ACTION_KEYWORDS)
        if not is_actionable:
            return None

        # Extract deadline if mentioned
        deadline = self._extract_deadline(subject)

        return ParsedEmail(
            platform=platform,
            subject=subject,
            sender=sender,
            action_needed="Check platform for new opportunity",
            deadline=deadline,
        )

    @staticmethod
    def _identify_platform(sender: str, subject: str) -> str | None:
        """Match sender/subject against known platform patterns."""
        combined = f"{sender} {subject}"
        for platform, patterns in PLATFORM_PATTERNS.items():
            for pattern in patterns:
                if pattern in combined:
                    return platform
        return None

    @staticmethod
    def _decode_header(header: str) -> str:
        """Decode email header, handling encoded words."""
        if not header:
            return ""
        decoded_parts = decode_header(header)
        result = []
        for part, charset in decoded_parts:
            if isinstance(part, bytes):
                result.append(part.decode(charset or "utf-8", errors="replace"))
            else:
                result.append(part)
        return " ".join(result)

    @staticmethod
    def _extract_deadline(subject: str) -> str | None:
        """Try to extract a deadline from the subject line."""
        # Common patterns: "expires in 2 hours", "deadline: March 5", "ends today"
        patterns = [
            r"expires?\s+in\s+(\d+\s+\w+)",
            r"deadline:?\s*(.+?)(?:\s*[-|]|$)",
            r"ends?\s+(today|tonight|tomorrow)",
            r"until\s+(.+?)(?:\s*[-|]|$)",
        ]
        for pattern in patterns:
            match = re.search(pattern, subject, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
