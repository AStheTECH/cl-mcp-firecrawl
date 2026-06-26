"""Scrape group: scrape_url, batch_scrape_urls, get_batch_scrape_status, cancel_batch_scrape."""

import logging

from fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .. import service
from ..config import CONNECT_TIMEOUT, POLL_TIMEOUT, READ_TIMEOUT
from ..logging_utils import ToolLogger
from ..schemas import (
    BatchScrapeStartData,
    BatchScrapeStartResult,
    BatchScrapeStatusData,
    BatchScrapeStatusResult,
    CancelData,
    CancelResult,
    ScrapeData,
    ScrapeResult,
)
from ._helpers import (
    _err,
    _handle_request_exc,
    _upstream_err,
    _SCRAPE_FORMATS_NOTE,
    _PROXY_NOTE,
)

logger = logging.getLogger("firecrawl-mcp.tools.scrape")


def register_scrape_tools(mcp: FastMCP) -> None:

    @mcp.tool(
        name="scrape_url",
        description=(
            "Scrapes a single URL and returns its content in the requested formats. "
            "Returns the page as markdown, HTML, screenshot, links, or a summary. "
            "For public document URLs (PDF, DOCX) Firecrawl auto-detects and parses them. "
            "The response includes `data.metadata.scrapeId` which can be passed to "
            "`browser_interact` to continue interacting with the same live browser session."
        ),
        annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    )
    def scrape_url(
        url: str = Field(description="Full URL to scrape, including https://."),
        formats: list[str] = Field(
            default=["markdown"], description=_SCRAPE_FORMATS_NOTE
        ),
        only_main_content: bool = Field(
            default=True,
            description="Strip navigation, headers, footers, and ads — keep the article/content body.",
        ),
        wait_for: int = Field(
            default=0,
            description="Milliseconds to wait after page load before capturing (0–30000). Use for JS-rendered pages.",
        ),
        timeout_ms: int = Field(
            default=30000,
            description="Maximum time the page load may take in milliseconds (1000–300000).",
        ),
        mobile: bool = Field(default=False, description="Emulate a mobile viewport."),
        proxy: str = Field(default="auto", description=_PROXY_NOTE),
        block_ads: bool = Field(
            default=True,
            description="Block ads and cookie consent banners before capturing.",
        ),
        include_tags: list[str] | None = Field(
            default=None,
            description="HTML tags to include in output (e.g. ['article', 'main']). Omit to include all.",
        ),
        exclude_tags: list[str] | None = Field(
            default=None,
            description="HTML tags to strip from output (e.g. ['nav', 'footer', 'aside']).",
        ),
        remove_base64_images: bool = Field(
            default=True,
            description="Drop inline base64 images from markdown output to reduce token usage.",
        ),
    ) -> ScrapeResult:
        tlog = ToolLogger(logger, "scrape_url")
        if wait_for < 0 or wait_for > 30000:
            return _err(
                ScrapeResult,
                tlog,
                "VALIDATION_ERROR",
                "wait_for must be 0–30000 ms",
                400,
            )
        if timeout_ms < 1000 or timeout_ms > 300000:
            return _err(
                ScrapeResult,
                tlog,
                "VALIDATION_ERROR",
                "timeout_ms must be 1000–300000",
                400,
            )

        body: dict = {
            "url": url,
            "formats": formats,
            "onlyMainContent": only_main_content,
            "waitFor": wait_for,
            "timeout": timeout_ms,
            "mobile": mobile,
            "proxy": proxy,
            "blockAds": block_ads,
            "removeBase64Images": remove_base64_images,
        }
        if include_tags:
            body["includeTags"] = include_tags
        if exclude_tags:
            body["excludeTags"] = exclude_tags

        try:
            data, status, retry_after = service.firecrawl_request(
                "POST",
                "/scrape",
                body=body,
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
            )
            if 200 <= status < 300:
                raw = data.get("data") or {}
                tlog.success()
                return ScrapeResult(
                    success=True, statusCode=status, data=ScrapeData(**raw)
                )
            return _upstream_err(ScrapeResult, tlog, status, data, retry_after)
        except Exception as exc:
            return _handle_request_exc(ScrapeResult, tlog, exc)

    @mcp.tool(
        name="batch_scrape_urls",
        description=(
            "Starts an async batch scrape job for a list of URLs. Returns a job ID immediately. "
            "Use `get_batch_scrape_status` to poll for completion and retrieve scraped content. "
            "Ideal for scraping 5–1000 URLs in parallel without blocking."
        ),
        annotations=ToolAnnotations(
            readOnlyHint=False, destructiveHint=False, openWorldHint=True
        ),
    )
    def batch_scrape_urls(
        urls: list[str] = Field(description="List of URLs to scrape."),
        formats: list[str] = Field(
            default=["markdown"], description=_SCRAPE_FORMATS_NOTE
        ),
        only_main_content: bool = Field(
            default=True,
            description="Strip navigation, headers, footers, and ads from each page.",
        ),
        proxy: str = Field(default="auto", description=_PROXY_NOTE),
        block_ads: bool = Field(
            default=True, description="Block ads and cookie banners."
        ),
        remove_base64_images: bool = Field(
            default=True,
            description="Drop inline base64 images to reduce response size.",
        ),
        ignore_invalid_urls: bool = Field(
            default=False,
            description="Skip invalid URLs instead of failing the entire job.",
        ),
        max_concurrency: int | None = Field(
            default=None,
            description="Maximum simultaneous scrapes (leave None for Firecrawl default).",
        ),
    ) -> BatchScrapeStartResult:
        tlog = ToolLogger(logger, "batch_scrape_urls")
        if not urls:
            return _err(
                BatchScrapeStartResult,
                tlog,
                "VALIDATION_ERROR",
                "urls list cannot be empty",
                400,
            )

        body: dict = {
            "urls": urls,
            "formats": formats,
            "onlyMainContent": only_main_content,
            "proxy": proxy,
            "blockAds": block_ads,
            "removeBase64Images": remove_base64_images,
            "ignoreInvalidURLs": ignore_invalid_urls,
        }
        if max_concurrency is not None:
            body["maxConcurrency"] = max_concurrency

        try:
            data, status, retry_after = service.firecrawl_request(
                "POST",
                "/batch/scrape",
                body=body,
                timeout=(CONNECT_TIMEOUT, POLL_TIMEOUT),
            )
            if 200 <= status < 300:
                tlog.success()
                return BatchScrapeStartResult(
                    success=True,
                    statusCode=status,
                    data=BatchScrapeStartData(
                        id=data.get("id", ""),
                        url=data.get("url"),
                        invalidURLs=data.get("invalidURLs"),
                    ),
                )
            return _upstream_err(
                BatchScrapeStartResult, tlog, status, data, retry_after
            )
        except Exception as exc:
            return _handle_request_exc(BatchScrapeStartResult, tlog, exc)

    @mcp.tool(
        name="get_batch_scrape_status",
        description=(
            "Polls the status of a batch scrape job started by `batch_scrape_urls`. "
            "Returns status (scraping/completed/failed), progress counters, and scraped pages when done. "
            "If `data.next` is present in the response, call again with the same job_id to get the next page of results."
        ),
        annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    )
    def get_batch_scrape_status(
        job_id: str = Field(
            description="Batch scrape job ID returned by `batch_scrape_urls`."
        ),
    ) -> BatchScrapeStatusResult:
        tlog = ToolLogger(logger, "get_batch_scrape_status")
        if not job_id.strip():
            return _err(
                BatchScrapeStatusResult,
                tlog,
                "VALIDATION_ERROR",
                "job_id cannot be empty",
                400,
            )
        try:
            data, status, retry_after = service.firecrawl_request(
                "GET",
                f"/batch/scrape/{job_id}",
                timeout=(CONNECT_TIMEOUT, POLL_TIMEOUT),
            )
            if 200 <= status < 300:
                tlog.success()
                return BatchScrapeStatusResult(
                    success=True,
                    statusCode=status,
                    data=BatchScrapeStatusData(
                        **{k: v for k, v in data.items() if k != "success"}
                    ),
                )
            return _upstream_err(
                BatchScrapeStatusResult, tlog, status, data, retry_after
            )
        except Exception as exc:
            return _handle_request_exc(BatchScrapeStatusResult, tlog, exc)

    @mcp.tool(
        name="cancel_batch_scrape",
        description=(
            "DESTRUCTIVE — REQUIRES EXPLICIT USER CONFIRMATION BEFORE CALLING. "
            "Stops a running batch scrape job. "
            "All in-progress scraping is terminated and any unfinished results are permanently lost — "
            "this cannot be undone. "
            "NEVER call this tool autonomously or as part of an automated flow. "
            "You MUST stop, tell the user exactly which batch scrape job will be cancelled and that "
            "unfinished results will be permanently lost, and wait for their explicit written confirmation before proceeding."
        ),
        annotations=ToolAnnotations(
            readOnlyHint=False, destructiveHint=True, openWorldHint=True
        ),
    )
    def cancel_batch_scrape(
        job_id: str = Field(description="Batch scrape job ID to cancel."),
    ) -> CancelResult:
        tlog = ToolLogger(logger, "cancel_batch_scrape")
        if not job_id.strip():
            return _err(
                CancelResult, tlog, "VALIDATION_ERROR", "job_id cannot be empty", 400
            )
        try:
            data, status, retry_after = service.firecrawl_request(
                "DELETE",
                f"/batch/scrape/{job_id}",
                timeout=(CONNECT_TIMEOUT, POLL_TIMEOUT),
            )
            if 200 <= status < 300:
                tlog.success()
                return CancelResult(
                    success=True,
                    statusCode=status,
                    data=CancelData(status=data.get("status", "cancelled")),
                )
            return _upstream_err(CancelResult, tlog, status, data, retry_after)
        except Exception as exc:
            return _handle_request_exc(CancelResult, tlog, exc)
