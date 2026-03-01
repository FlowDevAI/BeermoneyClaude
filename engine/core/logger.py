"""
BeermoneyClaude — Logging
Structured logging with loguru: console + daily rotating file.
"""

import sys

from loguru import logger

from .config import settings

# Remove default handler
logger.remove()

# Console handler
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{extra[plugin]:>12}</cyan> | {message}",
    level="INFO",
    colorize=True,
)

# File handler (daily rotation)
logger.add(
    str(settings.LOGS_DIR / "agent_{time:YYYY-MM-DD}.log"),
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {extra[plugin]:>12} | {message}",
    level="DEBUG",
    rotation="00:00",
    retention="30 days",
    compression="zip",
)

# Bind default extra field
logger = logger.bind(plugin="system")


def get_logger(plugin_name: str) -> "logger":
    """Get a logger instance bound to a specific plugin name."""
    return logger.bind(plugin=plugin_name)
