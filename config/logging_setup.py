"""
Central logging configuration for Reel Engine V2.

Every module should do:
    import logging
    logger = logging.getLogger(__name__)

and call `configure_logging()` once (main.py does this at startup) rather
than each module configuring its own handlers.

Log tags used across the engine (per spec): [COLLECT] [ANALYZE] [IDEA]
[SCRIPT] [RENDER] [ERROR] [PERFORMANCE]. Modules should prefix their log
messages with the relevant tag, e.g. logger.info("[COLLECT] ...").
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from config.settings import Settings, get_settings


_configured = False


def configure_logging(settings: Settings | None = None) -> None:
    """
    Configure the root logger once. Safe to call multiple times —
    subsequent calls are no-ops.

    Never logs secrets: callers must not pass API keys/tokens into log
    messages. This function only sets up handlers/formatting.
    """
    global _configured
    if _configured:
        return

    settings = settings or get_settings()

    log_file: Path = settings.logging.log_file
    log_file.parent.mkdir(parents=True, exist_ok=True)

    level = getattr(logging, settings.logging.level.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    if settings.logging.console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    _configured = True
