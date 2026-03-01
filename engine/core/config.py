"""
BeermoneyClaude — Configuration
Loads settings from .env file using pydantic-settings.
"""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = Path(__file__).resolve().parent.parent / "data"
    SESSIONS_DIR: Path = Path(__file__).resolve().parent.parent / "data" / "sessions"
    SCREENSHOTS_DIR: Path = Path(__file__).resolve().parent.parent / "data" / "screenshots"
    LOGS_DIR: Path = Path(__file__).resolve().parent.parent.parent / "logs"

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    # Gmail
    GMAIL_ADDRESS: str = ""
    GMAIL_APP_PASSWORD: str = ""

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # Captcha
    TWOCAPTCHA_API_KEY: str = ""

    # Encryption
    ENCRYPTION_KEY: str = ""

    # Agent
    AGENT_MODE: str = "night"  # night | standby | manual
    NIGHT_START_HOUR: int = 23
    NIGHT_END_HOUR: int = 7
    HEADLESS: bool = True
    CHECK_INTERVAL_TIER1: int = 900
    CHECK_INTERVAL_TIER2: int = 1800
    CHECK_INTERVAL_TIER3: int = 3600
    CHECK_INTERVAL_TIER4: int = 3600
    MIN_SCORE_THRESHOLD: int = 30
    SCREENSHOT_RETENTION_DAYS: int = 7

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()

# Create directories if they don't exist
for d in [settings.DATA_DIR, settings.SESSIONS_DIR, settings.SCREENSHOTS_DIR, settings.LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)
