"""Shared error helpers and format constants for all tool modules."""

import requests

from ..logging_utils import ToolLogger
from ..schemas import ToolError

_SCRAPE_FORMATS_NOTE = (
    "Output formats to request: markdown (default), html, rawHtml, links, screenshot, "
    "summary, json, audio, video, branding, product, menu. "
    "Use ['markdown'] for text content, add 'screenshot' for visual capture."
)

_PROXY_NOTE = "Proxy tier: 'auto' (default), 'basic', or 'enhanced' (stealth, higher credit cost)."


def _err(result_class, tlog: ToolLogger, code: str, message: str, status: int,
         retriable: bool = False, retry_after: int | None = None):
    tlog.failure(code, message)
    return result_class(
        success=False,
        statusCode=status,
        retriable=retriable,
        retry_after_seconds=retry_after,
        error=ToolError(code=code, message=message),
    )


def _handle_request_exc(result_class, tlog: ToolLogger, exc: Exception):
    if isinstance(exc, requests.ConnectTimeout):
        tlog.failure("UPSTREAM_ERROR", "Connection timeout")
        return result_class(
            success=False, statusCode=408, retriable=False,
            error=ToolError(code="UPSTREAM_ERROR", message="Connection timeout — upstream unreachable"),
        )
    if isinstance(exc, requests.ReadTimeout):
        tlog.failure("UPSTREAM_ERROR", "Read timeout")
        return result_class(
            success=False, statusCode=504, retriable=False,
            error=ToolError(code="UPSTREAM_ERROR", message="Read timeout — upstream did not respond in time"),
        )
    if isinstance(exc, requests.RequestException):
        tlog.failure("UPSTREAM_ERROR", "Network error")
        return result_class(
            success=False, statusCode=503, retriable=True,
            error=ToolError(code="UPSTREAM_ERROR", message=str(exc)),
        )
    if isinstance(exc, ValueError):
        tlog.failure("AUTH_ERROR", str(exc))
        return result_class(
            success=False, statusCode=401, retriable=False,
            error=ToolError(code="AUTH_ERROR", message=str(exc)),
        )
    tlog.failure("SERVER_ERROR", str(exc))
    return result_class(
        success=False, statusCode=500, retriable=False,
        error=ToolError(code="SERVER_ERROR", message=str(exc)),
    )


def _upstream_err(result_class, tlog: ToolLogger, status: int, data: dict,
                  retry_after: int | None = None):
    retriable = status in (429, 500, 502, 503)
    tlog.failure("UPSTREAM_ERROR", f"HTTP {status}")
    msg = data.get("error") or data.get("message") or f"HTTP {status}"
    return result_class(
        success=False, statusCode=status, retriable=retriable,
        retry_after_seconds=retry_after,
        error=ToolError(code="UPSTREAM_ERROR", message=str(msg)),
    )
