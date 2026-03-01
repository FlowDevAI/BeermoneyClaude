"""
BeermoneyClaude — Plugin Base
Abstract base class and data models for all platform plugins.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Page


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

    def __post_init__(self) -> None:
        if self.estimated_minutes > 0 and self.estimated_pay > 0:
            self.effective_hourly_rate = round(
                (self.estimated_pay / self.estimated_minutes) * 60, 2
            )


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
    status: str  # completed | failed | queued
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
    async def login(self, page: "Page") -> LoginResult:
        ...

    @abstractmethod
    async def is_logged_in(self, page: "Page") -> bool:
        ...

    @abstractmethod
    async def scan_available_tasks(self, page: "Page") -> list[DetectedTask]:
        ...

    @abstractmethod
    async def accept_task(self, page: "Page", task: DetectedTask) -> AcceptResult:
        ...

    @abstractmethod
    async def classify_task(self, task: DetectedTask) -> TaskDifficulty:
        ...

    async def auto_complete(self, page: "Page", task: DetectedTask) -> TaskResult:
        """Override in plugins that support auto-completion."""
        raise NotImplementedError(f"{self.name} does not support auto_complete")

    async def get_balance(self, page: "Page") -> float | None:
        """Override to fetch current account balance."""
        return None

    def __repr__(self) -> str:
        return f"<Plugin:{self.name} tier={self.tier}>"
