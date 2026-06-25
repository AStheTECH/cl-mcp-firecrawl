"""Configuration for MewCP Firecrawl MCP Server."""

import logging
import os

SERVER_VERSION = "v1.1.0"
BREAKING_CHANGES: list = []

FIRECRAWL_API_BASE = "https://api.firecrawl.dev/v2"

CONNECT_TIMEOUT = 5  # fail fast if TCP cannot be established
READ_TIMEOUT = 60  # sync ops: scrape, map, search, parse, browser interact
POLL_TIMEOUT = 30  # async job starts and status polls


def configure_logging() -> None:
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    try:
        from pythonjsonlogger import jsonlogger

        handler = logging.StreamHandler()
        handler.setFormatter(
            jsonlogger.JsonFormatter(
                fmt="%(asctime)s %(name)s %(levelname)s %(message)s"
            )
        )
    except ImportError:
        handler = logging.StreamHandler()

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(log_level)
