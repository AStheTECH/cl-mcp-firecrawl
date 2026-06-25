"""Upstream API client for MewCP Firecrawl MCP Server."""

import logging
from typing import Any

import requests
from fastmcp_credentials import get_credentials

from .config import FIRECRAWL_API_BASE, CONNECT_TIMEOUT, READ_TIMEOUT, POLL_TIMEOUT

logger = logging.getLogger("firecrawl-mcp.service")


def _get_api_key() -> str:
    cred = get_credentials()
    key = cred.fields.get("api_key") if cred.fields else None
    if not key:
        raise ValueError(
            'Missing api_key credential ensure X-MCP-Cred-Fields header contains {"api_key": "fc-..."}'
        )
    return key


def _auth_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_get_api_key()}",
        "Content-Type": "application/json",
    }


def map_retriable(
    status: int, retry_after_header: str | None = None
) -> tuple[bool, int | None]:
    """Returns (retriable, retry_after_seconds) from HTTP status."""
    retry_after: int | None = None
    if retry_after_header:
        try:
            retry_after = int(retry_after_header)
        except ValueError:
            pass

    if status in (500, 502, 503):
        return True, None
    if status == 429:
        return True, retry_after
    return False, None


def firecrawl_request(
    method: str,
    endpoint: str,
    body: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    timeout: tuple[int, int] | None = None,
) -> tuple[dict[str, Any], int, int | None]:
    """Make a Firecrawl API request.

    Returns (response_dict, status_code, retry_after_seconds).
    """
    if timeout is None:
        timeout = (CONNECT_TIMEOUT, READ_TIMEOUT)
    url = f"{FIRECRAWL_API_BASE}{endpoint}"
    resp = requests.request(
        method=method,
        url=url,
        headers=_auth_headers(),
        json=body,
        params=params,
        timeout=timeout,
    )
    try:
        data = resp.json()
    except Exception:
        data = {"success": False, "error": resp.text or "Empty response body"}

    retry_after_hdr = resp.headers.get("Retry-After")
    retriable, retry_after = map_retriable(resp.status_code, retry_after_hdr)
    return data, resp.status_code, retry_after


def firecrawl_multipart(
    endpoint: str,
    file_bytes: bytes,
    file_name: str,
    options_json: str,
    timeout: tuple[int, int] | None = None,
) -> tuple[dict[str, Any], int, int | None]:
    """POST multipart/form-data for /parse endpoint.

    Returns (response_dict, status_code, retry_after_seconds).
    """
    if timeout is None:
        timeout = (CONNECT_TIMEOUT, READ_TIMEOUT)
    url = f"{FIRECRAWL_API_BASE}{endpoint}"
    key = _get_api_key()
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {key}"},
        data={"options": options_json},
        files={"file": (file_name, file_bytes)},
        timeout=timeout,
    )
    try:
        data = resp.json()
    except Exception:
        data = {"success": False, "error": resp.text or "Empty response body"}

    retry_after_hdr = resp.headers.get("Retry-After")
    _, retry_after = map_retriable(resp.status_code, retry_after_hdr)
    return data, resp.status_code, retry_after
