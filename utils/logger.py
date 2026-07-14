"""
Application logger configuration.
"""

import sys

from loguru import logger

from config import settings


logger.remove()

logger.add(
    sys.stdout,
    level=settings.LOG_LEVEL,
    enqueue=True,
    backtrace=True,
    diagnose=True,
)

logger.add(
    settings.LOG_DIR / "app.log",
    level=settings.LOG_LEVEL,
    rotation=settings.LOG_ROTATION,
    retention=settings.LOG_RETENTION,
    compression="zip",
    enqueue=True,
    backtrace=True,
    diagnose=True,
)

logger.info("Logger initialized.")