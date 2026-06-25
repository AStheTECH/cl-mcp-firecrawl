"""Discover group: map_url, search_web."""

import logging

from fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .. import service
from ..config import CONNECT_TIMEOUT, READ_TIMEOUT
from ..logging_utils import ToolLogger
from ..schemas import (
    ImageSearchItem,
    MapData,
    MapLink,
    MapResult,
    NewsSearchItem,
    SearchData,
    SearchResult,
    SearchResultsData,
    WebSearchItem,
)
from ._helpers import _err, _handle_request_exc, _upstream_err

logger = logging.getLogger("firecrawl-mcp.tools.discover")


def register_discover_tools(mcp: FastMCP) -> None:

    @mcp.tool(
        name="map_url",
        description=(
            "Discovers all URLs on a website without scraping their content. Returns a list of links "
            "with title and description. Use before `crawl_url` to understand site structure, "
            "or pass `search` to filter URLs by relevance to a topic. "
            "Much faster and cheaper than crawling when you only need the URL list."
        ),
        annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    )
    def map_url(
        url: str = Field(description="Root URL of the site to map."),
        search: str | None = Field(default=None, description="Filter and rank URLs by relevance to this search query."),
        sitemap: str = Field(
            default="include",
            description="'include' (sitemap + crawl), 'skip' (crawl only), 'only' (sitemap only).",
        ),
        include_subdomains: bool = Field(default=True, description="Include URLs from subdomains of the root URL."),
        ignore_query_parameters: bool = Field(default=True, description="Deduplicate URLs that differ only in query parameters."),
        ignore_cache: bool = Field(default=False, description="Bypass sitemap cache to get the freshest URL list."),
        limit: int = Field(default=5000, description="Maximum number of URLs to return (1–100000)."),
        country: str | None = Field(default=None, description="ISO 3166-1 alpha-2 country code for geo-targeting (e.g. 'US', 'DE')."),
    ) -> MapResult:
        tlog = ToolLogger(logger, "map_url")
        if limit < 1 or limit > 100000:
            return _err(MapResult, tlog, "VALIDATION_ERROR", "limit must be 1–100000", 400)

        body: dict = {
            "url": url,
            "sitemap": sitemap,
            "includeSubdomains": include_subdomains,
            "ignoreQueryParameters": ignore_query_parameters,
            "ignoreCache": ignore_cache,
            "limit": limit,
        }
        if search:
            body["search"] = search
        if country:
            body["location"] = {"country": country}

        try:
            data, status, retry_after = service.firecrawl_request(
                "POST", "/map", body=body,
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
            )
            if 200 <= status < 300:
                raw_links = data.get("links") or []
                links = [
                    MapLink(**lnk) if isinstance(lnk, dict) else MapLink(url=lnk)
                    for lnk in raw_links
                ]
                tlog.success()
                return MapResult(success=True, statusCode=status, data=MapData(links=links))
            return _upstream_err(MapResult, tlog, status, data, retry_after)
        except Exception as exc:
            return _handle_request_exc(MapResult, tlog, exc)

    @mcp.tool(
        name="search_web",
        description=(
            "Searches the web and optionally scrapes the full content of each result. "
            "Returns web pages, images, or news depending on `sources`. "
            "Set `scrape_formats` to ['markdown'] to get full page content alongside each result — "
            "omit to get only title, description, and URL. "
            "Supports operator syntax: site:, filetype:, intitle:, -exclude, \"exact phrase\"."
        ),
        annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    )
    def search_web(
        query: str = Field(
            description=(
                "Search query. Supports operators: site:domain.com, filetype:pdf, "
                "intitle:keyword, -exclude, \"exact phrase\", related:domain.com."
            ),
        ),
        limit: int = Field(default=10, description="Number of results to return (1–100)."),
        sources: list[str] = Field(
            default=["web"],
            description="Result types to return: 'web', 'images', 'news'. Combine as needed.",
        ),
        categories: list[str] | None = Field(
            default=None,
            description="Filter to specific result categories: 'github', 'research', 'pdf'.",
        ),
        country: str | None = Field(
            default=None,
            description="ISO country code for geo-targeted results (e.g. 'US', 'DE', 'JP'). Default: US.",
        ),
        location: str | None = Field(
            default=None,
            description="City/region for geo-targeted results (e.g. 'San Francisco,California,United States').",
        ),
        tbs: str | None = Field(
            default=None,
            description="Time-based filter: 'qdr:d' (past day), 'qdr:w' (past week), 'qdr:m' (past month).",
        ),
        include_domains: list[str] | None = Field(
            default=None,
            description="Restrict results to these domains (mutually exclusive with exclude_domains).",
        ),
        exclude_domains: list[str] | None = Field(
            default=None,
            description="Remove these domains from results (mutually exclusive with include_domains).",
        ),
        scrape_formats: list[str] | None = Field(
            default=None,
            description=(
                "If provided, each result page is scraped and content returned in these formats. "
                "Omit to return only title/description/URL without scraping."
            ),
        ),
        timeout_ms: int = Field(
            default=45000,
            description="Request timeout in milliseconds (1000–300000). Default 45000.",
        ),
    ) -> SearchResult:
        tlog = ToolLogger(logger, "search_web")
        if limit < 1 or limit > 100:
            return _err(SearchResult, tlog, "VALIDATION_ERROR", "limit must be 1–100", 400)
        if include_domains and exclude_domains:
            return _err(SearchResult, tlog, "VALIDATION_ERROR",
                        "include_domains and exclude_domains are mutually exclusive", 400)

        body: dict = {
            "query": query,
            "limit": limit,
            "sources": sources,
            "timeout": timeout_ms,
        }
        if categories:
            body["categories"] = [{"type": c} for c in categories]
        if country:
            body["country"] = country
        if location:
            body["location"] = location
        if tbs:
            body["tbs"] = tbs
        if include_domains:
            body["includeDomains"] = include_domains
        if exclude_domains:
            body["excludeDomains"] = exclude_domains
        if scrape_formats:
            body["scrapeOptions"] = {"formats": scrape_formats}

        try:
            data, status, retry_after = service.firecrawl_request(
                "POST", "/search", body=body,
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
            )
            if 200 <= status < 300:
                raw = data.get("data") or {}
                results_data = SearchResultsData(
                    web=[WebSearchItem(**i) for i in (raw.get("web") or [])],
                    images=[ImageSearchItem(**i) for i in (raw.get("images") or [])],
                    news=[NewsSearchItem(**i) for i in (raw.get("news") or [])],
                )
                search_data = SearchData(
                    results=results_data,
                    warning=data.get("warning"),
                    id=data.get("id"),
                    creditsUsed=data.get("creditsUsed"),
                )
                tlog.success()
                return SearchResult(success=True, statusCode=status, data=search_data)
            return _upstream_err(SearchResult, tlog, status, data, retry_after)
        except Exception as exc:
            return _handle_request_exc(SearchResult, tlog, exc)
