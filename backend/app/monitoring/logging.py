import logging
import os
from typing import Optional

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def configure_logging(force: bool = False, level_override: Optional[str] = None) -> None:
    """Configure application-wide logging with a consistent format."""
    level_name = level_override or os.getenv("LOG_LEVEL", "INFO")
    level = getattr(logging, level_name.upper(), logging.INFO)

    logging.basicConfig(level=level, format=LOG_FORMAT, force=force)

    # Reduce noise from verbose libraries
    logging.getLogger("httpx").setLevel(max(logging.WARNING, level))
    logging.getLogger("qdrant_client").setLevel(max(logging.INFO, level))
    logging.getLogger("uvicorn.error").setLevel(level)
