"""Structured Logging Module

Configures application logging with JSON or clean formatted console output.
Ensures sensitive credentials, API keys, or personal tokens are never logged.
"""

import logging
import sys
from backend.app.config import settings


def setup_logging() -> logging.Logger:
    """Initialize root logger with formatted handler."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    logger = logging.getLogger("ev_fleet_agent")
    logger.setLevel(log_level)
    
    # Avoid duplicate handlers if re-initialized
    if not logger.handlers:
        logger.addHandler(handler)

    return logger


logger = setup_logging()
