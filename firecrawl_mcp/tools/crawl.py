"""Crawl group: crawl_url, get_crawl_status, cancel_crawl."""

import logging

from fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .. import service
from ..config import CONNECT_TIMEOUT, POLL_TIMEOUT
from ..logging_utils import ToolLogger
from ..schemas import (
    CancelData,
    CancelResult,
    CrawlStartData,
    CrawlStartResult,
    CrawlStatusData,
    CrawlStatusResult,
)
from ._helpers import _err, _handle_request_exc, _upstream_err, _SCRAPE_FORMATS_NOTE, _PROXY_NOTE

logger = logging.getLogger("firecrawl-mcp.tools.crawl")


def register_crawl_tools(mcp: FastMCP) -> None:

    @mcp.tool(
        name="crawl_url",
        description=(
            "Starts an async crawl job from a seed URL, following internal links up to the specified depth and page limit. "
            "Returns a job ID immediately. Use `get_crawl_status` to poll for progress and results. "
            "Use `include_paths`/`exclude_paths` regex patterns to control which URLs are visited. "
            "Ideal for extracting all content from a site, documentation, or blog."
        ),
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=True),
    )
    def crawl_url(
        url: str = Field(description="Seed URL to start crawling from."),
        limit: int = Field(default=10000, description="Maximum number of pages to crawl (1–10000)."),
        max_discovery_depth: int | None = Field(default=None, description="Maximum link depth from the seed URL. Omit for unlimited."),
        include_paths: list[str] | None = Field(default=None, description="Regex patterns — only URLs matching at least one pattern are crawled."),
        exclude_paths: list[str] | None = Field(default=None, description="Regex patterns — URLs matching any pattern are skipped."),
        sitemap: str = Field(
            default="include",
            description="Sitemap usage: 'include' (use sitemap + crawl), 'skip' (crawl only), 'only' (sitemap only).",
        ),
        allow_subdomains: bool = Field(default=False, description="Follow links to subdomains of the seed URL."),
        allow_external_links: bool = Field(default=False, description="Follow links to entirely different domains."),
        ignore_query_parameters: bool = Field(default=False, description="Treat URLs that differ only in query parameters as duplicates."),
        formats: list[str] = Field(default=["markdown"], description=_SCRAPE_FORMATS_NOTE),
        only_main_content: bool = Field(default=True, description="Strip navigation, headers, footers, and ads from each page."),
        proxy: str = Field(default="auto", description=_PROXY_NOTE),
        block_ads: bool = Field(default=True, description="Block ads and cookie banners."),
    ) -> CrawlStartResult:
        tlog = ToolLogger(logger, "crawl_url")
        if limit < 1 or limit > 10000:
            return _err(CrawlStartResult, tlog, "VALIDATION_ERROR", "limit must be 1–10000", 400)
        if sitemap not in ("include", "skip", "only"):
            return _err(CrawlStartResult, tlog, "VALIDATION_ERROR", "sitemap must be include, skip, or only", 400)

        body: dict = {
            "url": url,
            "limit": limit,
            "sitemap": sitemap,
            "allowSubdomains": allow_subdomains,
            "allowExternalLinks": allow_external_links,
            "ignoreQueryParameters": ignore_query_parameters,
            "scrapeOptions": {
                "formats": formats,
                "onlyMainContent": only_main_content,
                "proxy": proxy,
                "blockAds": block_ads,
            },
        }
        if max_discovery_depth is not None:
            body["maxDiscoveryDepth"] = max_discovery_depth
        if include_paths:
            body["includePaths"] = include_paths
        if exclude_paths:
            body["excludePaths"] = exclude_paths

        try:
            data, status, retry_after = service.firecrawl_request(
                "POST", "/crawl", body=body,
                timeout=(CONNECT_TIMEOUT, POLL_TIMEOUT),
            )
            if 200 <= status < 300:
                tlog.success()
                return CrawlStartResult(
                    success=True, statusCode=status,
                    data=CrawlStartData(id=data.get("id", ""), url=data.get("url")),
                )
            return _upstream_err(CrawlStartResult, tlog, status, data, retry_after)
        except Exception as exc:
            return _handle_request_exc(CrawlStartResult, tlog, exc)

    @mcp.tool(
        name="get_crawl_status",
        description=(
            "Polls the status of a crawl job started by `crawl_url`. "
            "Returns status (scraping/completed/failed/cancelled), progress counters, and crawled pages. "
            "If `data.next` is present, call again to retrieve the next page of results."
        ),
        annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    )
    def get_crawl_status(
        job_id: str = Field(description="Crawl job ID returned by `crawl_url`."),
    ) -> CrawlStatusResult:
        tlog = ToolLogger(logger, "get_crawl_status")
        if not job_id.strip():
            return _err(CrawlStatusResult, tlog, "VALIDATION_ERROR", "job_id cannot be empty", 400)
        try:
            data, status, retry_after = service.firecrawl_request(
                "GET", f"/crawl/{job_id}",
                timeout=(CONNECT_TIMEOUT, POLL_TIMEOUT),
            )
            if 200 <= status < 300:
                tlog.success()
                return CrawlStatusResult(
                    success=True, statusCode=status,
                    data=CrawlStatusData(**{k: v for k, v in data.items() if k != "success"}),
                )
            return _upstream_err(CrawlStatusResult, tlog, status, data, retry_after)
        except Exception as exc:
            return _handle_request_exc(CrawlStatusResult, tlog, exc)

    @mcp.tool(
        name="cancel_crawl",
        description=(
            "DESTRUCTIVE — REQUIRES EXPLICIT USER CONFIRMATION BEFORE CALLING. "
            "Stops a running crawl job. "
            "All in-progress crawling is terminated and any unfinished pages are permanently lost — "
            "this cannot be undone. "
            "NEVER call this tool autonomously or as part of an automated flow. "
            "You MUST stop, tell the user which crawl job will be cancelled and that unfinished "
            "pages will be permanently lost, and wait for their explicit written confirmation before proceeding."
        ),
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True, openWorldHint=True),
    )
    def cancel_crawl(
        job_id: str = Field(description="Crawl job ID to cancel."),
    ) -> CancelResult:
        tlog = ToolLogger(logger, "cancel_crawl")
        if not job_id.strip():
            return _err(CancelResult, tlog, "VALIDATION_ERROR", "job_id cannot be empty", 400)
        try:
            data, status, retry_after = service.firecrawl_request(
                "DELETE", f"/crawl/{job_id}",
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
