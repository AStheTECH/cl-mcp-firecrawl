"""Agent group: run_agent, get_agent_status, cancel_agent."""

import json
import logging

from fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .. import service
from ..config import CONNECT_TIMEOUT, POLL_TIMEOUT
from ..logging_utils import ToolLogger
from ..schemas import AgentJobData, AgentJobResult, CancelData, CancelResult
from ._helpers import _err, _handle_request_exc, _upstream_err

logger = logging.getLogger("firecrawl-mcp.tools.agent")


def register_agent_tools(mcp: FastMCP) -> None:

    @mcp.tool(
        name="run_agent",
        description=(
            "Starts an autonomous web research agent that searches, navigates, and extracts data "
            "based on a natural language prompt. No URLs required — the agent finds them. "
            "Use `schema` to get structured JSON output. Returns a job ID; use `get_agent_status` to poll. "
            "Use `spark-1-mini` (default, 60% cheaper) for most tasks; `spark-1-pro` for complex multi-domain research. "
            "Set `max_credits` to cap spending — the job fails without charges if the limit is hit."
        ),
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=True),
    )
    def run_agent(
        prompt: str = Field(
            description=(
                "Natural language description of the data to find (max 10000 chars). "
                "Be specific: 'Find the 5 most-funded AI startups in 2024 with founder names and total funding.'"
            ),
        ),
        urls: list[str] | None = Field(
            default=None,
            description="Optional seed URLs to focus the agent. Omit to let the agent search freely.",
        ),
        schema: str | None = Field(
            default=None,
            description="JSON schema string for structured output. Omit for free-form text.",
        ),
        model: str = Field(
            default="spark-1-mini",
            description="'spark-1-mini' (default, cheaper) or 'spark-1-pro' (higher accuracy).",
        ),
        max_credits: int | None = Field(
            default=None,
            description="Credit cap for this job (default 2500). Job fails without charges if exceeded.",
        ),
    ) -> AgentJobResult:
        tlog = ToolLogger(logger, "run_agent")
        if not prompt.strip():
            return _err(AgentJobResult, tlog, "VALIDATION_ERROR", "prompt cannot be empty", 400)
        if model not in ("spark-1-mini", "spark-1-pro"):
            return _err(AgentJobResult, tlog, "VALIDATION_ERROR",
                        "model must be 'spark-1-mini' or 'spark-1-pro'", 400)

        body: dict = {"prompt": prompt, "model": model}
        if urls:
            body["urls"] = urls
        if schema:
            try:
                body["schema"] = json.loads(schema)
            except json.JSONDecodeError as e:
                return _err(AgentJobResult, tlog, "VALIDATION_ERROR", f"schema is not valid JSON: {e}", 400)
        if max_credits is not None:
            body["maxCredits"] = max_credits

        try:
            data, status, retry_after = service.firecrawl_request(
                "POST", "/agent", body=body,
                timeout=(CONNECT_TIMEOUT, POLL_TIMEOUT),
            )
            if 200 <= status < 300:
                tlog.success()
                return AgentJobResult(
                    success=True, statusCode=status,
                    data=AgentJobData(
                        id=data.get("id"),
                        status=data.get("status"),
                        data=data.get("data"),
                        expiresAt=data.get("expiresAt"),
                        creditsUsed=data.get("creditsUsed"),
                    ),
                )
            return _upstream_err(AgentJobResult, tlog, status, data, retry_after)
        except Exception as exc:
            return _handle_request_exc(AgentJobResult, tlog, exc)

    @mcp.tool(
        name="get_agent_status",
        description=(
            "Polls the status of an agent job started by `run_agent`. "
            "Returns status (processing/completed/failed/cancelled), extracted data when done, "
            "and credit usage. Poll every 15–30 seconds; jobs typically complete in 1–5 minutes."
        ),
        annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    )
    def get_agent_status(
        job_id: str = Field(description="Agent job ID returned by `run_agent`."),
    ) -> AgentJobResult:
        tlog = ToolLogger(logger, "get_agent_status")
        if not job_id.strip():
            return _err(AgentJobResult, tlog, "VALIDATION_ERROR", "job_id cannot be empty", 400)
        try:
            data, status, retry_after = service.firecrawl_request(
                "GET", f"/agent/{job_id}",
                timeout=(CONNECT_TIMEOUT, POLL_TIMEOUT),
            )
            if 200 <= status < 300:
                tlog.success()
                return AgentJobResult(
                    success=True, statusCode=status,
                    data=AgentJobData(
                        id=data.get("id"),
                        status=data.get("status"),
                        data=data.get("data"),
                        expiresAt=data.get("expiresAt"),
                        creditsUsed=data.get("creditsUsed"),
                    ),
                )
            return _upstream_err(AgentJobResult, tlog, status, data, retry_after)
        except Exception as exc:
            return _handle_request_exc(AgentJobResult, tlog, exc)

    @mcp.tool(
        name="cancel_agent",
        description=(
            "DESTRUCTIVE — REQUIRES EXPLICIT USER CONFIRMATION BEFORE CALLING. "
            "Requests cancellation of a running agent job. "
            "Any in-progress reasoning steps complete before the job transitions to cancelled — "
            "credits for completed steps may still be charged and cannot be recovered. "
            "NEVER call this tool autonomously or as part of an automated flow. "
            "You MUST stop, tell the user which agent job will be cancelled and the credit implications, "
            "and wait for their explicit written confirmation before proceeding."
        ),
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True, openWorldHint=True),
    )
    def cancel_agent(
        job_id: str = Field(description="Agent job ID to cancel."),
    ) -> CancelResult:
        tlog = ToolLogger(logger, "cancel_agent")
        if not job_id.strip():
            return _err(CancelResult, tlog, "VALIDATION_ERROR", "job_id cannot be empty", 400)
        try:
            data, status, retry_after = service.firecrawl_request(
                "DELETE", f"/agent/{job_id}",
                timeout=(CONNECT_TIMEOUT, POLL_TIMEOUT),
            )
            if 200 <= status < 300:
                tlog.success()
                return CancelResult(
                    success=True, statusCode=status,
                    data=CancelData(status=data.get("status", "cancelled")),
                )
            return _upstream_err(CancelResult, tlog, status, data, retry_after)
        except Exception as exc:
            return _handle_request_exc(CancelResult, tlog, exc)
