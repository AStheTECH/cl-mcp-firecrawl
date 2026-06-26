"""ToolLogger for structured per-tool logging."""

import logging
import time


class ToolLogger:
    def __init__(self, logger: logging.Logger, tool: str) -> None:
        self._logger = logger
        self._tool = tool
        self._start = time.monotonic()
        self._logger.info("tool=%s status=started", tool)

    def success(self) -> None:
        ms = round((time.monotonic() - self._start) * 1000)
        self._logger.info("tool=%s status=ok duration_ms=%d", self._tool, ms)

    def failure(self, code: str, message: str) -> None:
        ms = round((time.monotonic() - self._start) * 1000)
        self._logger.error(
            "tool=%s status=error error_code=%s message=%s duration_ms=%d",
            self._tool, code, message, ms,
        )
