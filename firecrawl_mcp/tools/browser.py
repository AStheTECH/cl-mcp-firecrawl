"""Browser group: browser_interact, browser_close."""

import logging

from fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .. import service
from ..config import CONNECT_TIMEOUT, POLL_TIMEOUT, READ_TIMEOUT
from ..logging_utils import ToolLogger
from ..schemas import BrowserInteractData, BrowserInteractResult, CancelData, CancelResult
from ._helpers import _err, _handle_request_exc, _upstream_err

logger = logging.getLogger("firecrawl-mcp.tools.browser")


def register_browser_tools(mcp: FastMCP) -> None:

    @mcp.tool(
        name="browser_interact",
        description=(
            "Executes code or a natural language prompt in the live browser session bound to a previous scrape job. "
            "The `scrape_id` comes from `data.metadata.scrapeId` in a `scrape_url` response. "
            "First call creates the browser session at the same page state as the scrape. "
            "Subsequent calls on the same `scrape_id` reuse the live session. "
            "Provide either `code` (Playwright/Node/Python/Bash to run) or `prompt_text` (AI-driven navigation), not both. "
            "Returns CDP URL, live view URL, stdout, and AI output. "
            "Call `browser_close` when done to release the session."
        ),
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=True),
    )
    def browser_interact(
        scrape_id: str = Field(description="Scrape job ID from `data.metadata.scrapeId` in a `scrape_url` response."),
        code: str | None = Field(
            default=None,
            description="Code to execute in the browser sandbox (1–100000 chars). Provide this OR prompt_text, not both.",
        ),
        prompt_text: str | None = Field(
            default=None,
            description="Natural language task for the AI browser agent (1–10000 chars). Provide this OR code, not both.",
        ),
        language: str = Field(
            default="node",
            description="Code language when using `code`: 'node' (default), 'python', or 'bash'.",
        ),
        timeout: int = Field(default=30, description="Execution timeout in seconds (1–300)."),
    ) -> BrowserInteractResult:
        tlog = ToolLogger(logger, "browser_interact")
        if not scrape_id.strip():
            return _err(BrowserInteractResult, tlog, "VALIDATION_ERROR", "scrape_id cannot be empty", 400)
        if code and prompt_text:
            return _err(BrowserInteractResult, tlog, "VALIDATION_ERROR",
                        "Provide either code or prompt_text, not both", 400)
        if not code and not prompt_text:
            return _err(BrowserInteractResult, tlog, "VALIDATION_ERROR",
                        "Either code or prompt_text must be provided", 400)
        if language not in ("node", "python", "bash"):
            return _err(BrowserInteractResult, tlog, "VALIDATION_ERROR",
                        "language must be node, python, or bash", 400)
        if timeout < 1 or timeout > 300:
            return _err(BrowserInteractResult, tlog, "VALIDATION_ERROR", "timeout must be 1–300 seconds", 400)

        body: dict = {"timeout": timeout}
        if code:
            body["code"] = code
            body["language"] = language
        if prompt_text:
            body["prompt"] = prompt_text

        try:
            data, status, retry_after = service.firecrawl_request(
                "POST", f"/scrape/{scrape_id}/interact", body=body,
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
            )
            if 200 <= status < 300:
                tlog.success()
                return BrowserInteractResult(
                    success=True, statusCode=status,
                    data=BrowserInteractData(**{k: v for k, v in data.items() if k != "success"}),
                )
            return _upstream_err(BrowserInteractResult, tlog, status, data, retry_after)
        except Exception as exc:
            return _handle_request_exc(BrowserInteractResult, tlog, exc)

    @mcp.tool(
        name="browser_close",
        description=(
            "DESTRUCTIVE — REQUIRES EXPLICIT USER CONFIRMATION BEFORE CALLING. "
            "Destroys the browser session attached to a scrape job. "
            "All browser state, cookies, and session data are permanently lost and the session cannot be resumed — "
            "this cannot be undone. "
            "Always call this when done interacting to avoid leaking browser resources and credits. "
            "NEVER call this tool autonomously or as part of an automated flow. "
            "You MUST stop, confirm with the user that the browser session is no longer needed, "
            "and wait for their explicit written confirmation before proceeding."
        ),
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True, openWorldHint=True),
    )
    def browser_close(
        scrape_id: str = Field(description="Scrape job ID whose browser session to close (same ID used in browser_interact)."),
    ) -> CancelResult:
        tlog = ToolLogger(logger, "browser_close")
        if not scrape_id.strip():
            return _err(CancelResult, tlog, "VALIDATION_ERROR", "scrape_id cannot be empty", 400)
        try:
            data, status, retry_after = service.firecrawl_request(
                "DELETE", f"/scrape/{scrape_id}/interact",
                timeout=(CONNECT_TIMEOUT, POLL_TIMEOUT),
            )
            if 200 <= status < 300:
                tlog.success()
                return CancelResult(
                    success=True, statusCode=status,
                    data=CancelData(status=data.get("status", "closed")),
                )
            return _upstream_err(CancelResult, tlog, status, data, retry_after)
        except Exception as exc:
            return _handle_request_exc(CancelResult, tlog, exc)
