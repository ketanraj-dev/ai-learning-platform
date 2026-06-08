"""
app/core/logging.py
-------------------
Centralised logging setup for the entire application.

WHY NOT JUST USE print()?
  - print() gives you no timestamp, no severity level, no module name
  - Logging gives you: 2024-01-15 10:23:45 | INFO | auth_service | User logged in
  - You can filter by level: show only ERRORs in production
  - You can redirect to a file later without changing any other code

USAGE IN ANY FILE:
  from app.core.logging import get_logger
  logger = get_logger(__name__)   # __name__ = current module name

  logger.info("User registered successfully")
  logger.warning("Face recognition failed, falling back to password")
  logger.error("OpenAI API call failed: %s", str(error))
"""

import logging
import sys


def setup_logging(debug: bool = False) -> None:
    """
    Configure application-wide logging.
    Call this ONCE in main.py on startup.

    Format example:
        2024-01-15 10:23:45 | INFO     | app.services.auth_service | User registered
    """
    level = logging.DEBUG if debug else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout)  # print to terminal
        ],
        force=True,  # override any existing logging config
    )

    # Silence noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger for a specific module.

    Always call with __name__ so the log shows which file it came from:
        logger = get_logger(__name__)

    Args:
        name: typically __name__ (e.g. "app.services.auth_service")

    Returns:
        A configured Logger instance
    """
    return logging.getLogger(name)