"""ToolLogger for structured per-tool logging."""

import logging
import time


class ToolLogger:
    def __init__(self, logger: logging.Logger, tool: str) -> None:
        self._rid: str | None = None
        try:
            from fastmcp_credentials import get_credentials
            cred = get_credentials()
            # OAuth: request_id comes via cred.extra (X-MCP-Cred-Extra header).
            # Static: library leaves extra empty — request_id comes via cred.fields instead.
            self._rid = (cred.extra or {}).get("request_id") or (cred.fields or {}).get("request_id")
        except Exception:
            pass
        self._logger = logger
        self._tool = tool
        self._start = time.monotonic()
        self._logger.info("tool=%s status=started request_id=%s", tool, self._rid)

    def success(self) -> None:
        ms = round((time.monotonic() - self._start) * 1000)
        self._logger.info(
            "tool=%s status=ok request_id=%s duration_ms=%d",
            self._tool, self._rid, ms,
        )

    def failure(self, code: str, message: str) -> None:
        ms = round((time.monotonic() - self._start) * 1000)
        self._logger.error(
            "tool=%s status=error error_code=%s message=%s request_id=%s duration_ms=%d",
            self._tool, code, message, self._rid, ms,
        )
