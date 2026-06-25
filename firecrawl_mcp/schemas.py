"""Pydantic output schemas for MewCP Firecrawl MCP Server."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


# ─── Base envelope ─────────────────────────────────────────────────────────────

class ToolError(BaseModel):
    code: str
    message: str
    details: dict = {}


class ToolResult(BaseModel):
    model_config = ConfigDict(extra="allow")
    success: bool
    statusCode: int
    retriable: bool = False
    retry_after_seconds: int | None = None
    error: ToolError | None = None


# ─── Shared sub-models ────────────────────────────────────────────────────────

class DocumentMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")
    title: str | None = None
    description: str | None = None
    language: str | None = None
    sourceURL: str | None = None
    url: str | None = None
    keywords: str | None = None
    statusCode: int | None = None
    contentType: str | None = None
    error: str | None = None
    scrapeId: str | None = None  # used as jobId for browser_interact


class ScrapeDocument(BaseModel):
    model_config = ConfigDict(extra="allow")
    markdown: str | None = None
    summary: str | None = None
    html: str | None = None
    rawHtml: str | None = None
    screenshot: str | None = None
    links: list[str] | None = None
    metadata: DocumentMetadata | None = None
    warning: str | None = None


# ─── 1. scrape_url ────────────────────────────────────────────────────────────

class ScrapeData(BaseModel):
    model_config = ConfigDict(extra="allow")
    markdown: str | None = None
    summary: str | None = None
    html: str | None = None
    rawHtml: str | None = None
    screenshot: str | None = None
    links: list[str] | None = None
    metadata: DocumentMetadata | None = None
    warning: str | None = None


class ScrapeResult(ToolResult):
    data: ScrapeData | None = None


# ─── 2. batch_scrape_urls ─────────────────────────────────────────────────────

class BatchScrapeStartData(BaseModel):
    id: str
    url: str | None = None
    invalidURLs: list[str] | None = None


class BatchScrapeStartResult(ToolResult):
    data: BatchScrapeStartData | None = None


# ─── 3. get_batch_scrape_status ───────────────────────────────────────────────

class BatchScrapeStatusData(BaseModel):
    model_config = ConfigDict(extra="allow")
    status: str
    total: int | None = None
    completed: int | None = None
    creditsUsed: int | None = None
    expiresAt: str | None = None
    next: str | None = None
    data: list[ScrapeDocument] | None = None


class BatchScrapeStatusResult(ToolResult):
    data: BatchScrapeStatusData | None = None


# ─── cancel (batch scrape, crawl, agent) ──────────────────────────────────────

class CancelData(BaseModel):
    status: str


class CancelResult(ToolResult):
    data: CancelData | None = None


# ─── 5. crawl_url ─────────────────────────────────────────────────────────────

class CrawlStartData(BaseModel):
    id: str
    url: str | None = None


class CrawlStartResult(ToolResult):
    data: CrawlStartData | None = None


# ─── 6. get_crawl_status ──────────────────────────────────────────────────────

class CrawlStatusData(BaseModel):
    model_config = ConfigDict(extra="allow")
    status: str
    total: int | None = None
    completed: int | None = None
    creditsUsed: int | None = None
    expiresAt: str | None = None
    createdAt: str | None = None
    completedAt: str | None = None
    duration: int | None = None
    next: str | None = None
    data: list[ScrapeDocument] | None = None


class CrawlStatusResult(ToolResult):
    data: CrawlStatusData | None = None


# ─── 8. map_url ───────────────────────────────────────────────────────────────

class MapLink(BaseModel):
    url: str
    title: str | None = None
    description: str | None = None


class MapData(BaseModel):
    links: list[MapLink]


class MapResult(ToolResult):
    data: MapData | None = None


# ─── 9. search_web ────────────────────────────────────────────────────────────

class WebSearchItem(BaseModel):
    model_config = ConfigDict(extra="allow")
    title: str | None = None
    description: str | None = None
    url: str | None = None
    markdown: str | None = None
    html: str | None = None
    rawHtml: str | None = None
    category: str | None = None


class ImageSearchItem(BaseModel):
    title: str | None = None
    imageUrl: str | None = None
    imageWidth: int | None = None
    imageHeight: int | None = None
    url: str | None = None
    position: int | None = None


class NewsSearchItem(BaseModel):
    model_config = ConfigDict(extra="allow")
    title: str | None = None
    snippet: str | None = None
    url: str | None = None
    date: str | None = None
    imageUrl: str | None = None
    position: int | None = None
    markdown: str | None = None


class SearchResultsData(BaseModel):
    web: list[WebSearchItem] | None = None
    images: list[ImageSearchItem] | None = None
    news: list[NewsSearchItem] | None = None


class SearchData(BaseModel):
    results: SearchResultsData | None = None
    warning: str | None = None
    id: str | None = None
    creditsUsed: int | None = None


class SearchResult(ToolResult):
    data: SearchData | None = None


# ─── 10. parse_document ───────────────────────────────────────────────────────

class ParseData(BaseModel):
    model_config = ConfigDict(extra="allow")
    markdown: str | None = None
    summary: str | None = None
    html: str | None = None
    rawHtml: str | None = None
    links: list[str] | None = None
    metadata: DocumentMetadata | None = None
    warning: str | None = None


class ParseResult(ToolResult):
    data: ParseData | None = None


# ─── 11-13. run_agent / get_agent_status / cancel_agent ──────────────────────

class AgentJobData(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str | None = None
    status: str | None = None
    data: dict | None = None  # user-defined schema output; shape not pre-declared
    expiresAt: str | None = None
    creditsUsed: int | None = None


class AgentJobResult(ToolResult):
    data: AgentJobData | None = None


# ─── 14. browser_interact ─────────────────────────────────────────────────────

class BrowserInteractData(BaseModel):
    model_config = ConfigDict(extra="allow")
    cdpUrl: str | None = None
    liveViewUrl: str | None = None
    interactiveLiveViewUrl: str | None = None
    output: str | None = None      # AI prompt response
    stdout: str | None = None
    result: str | None = None
    stderr: str | None = None
    exitCode: int | None = None
    killed: bool | None = None


class BrowserInteractResult(ToolResult):
    data: BrowserInteractData | None = None


# ─── 16. search_papers ────────────────────────────────────────────────────────

class PaperIds(BaseModel):
    model_config = ConfigDict(extra="allow")
    arxiv: list[str] | None = None


class PaperItem(BaseModel):
    model_config = ConfigDict(extra="allow")
    paperId: str | None = None
    primaryId: str | None = None
    ids: PaperIds | None = None
    title: str | None = None
    abstract: str | None = None
    score: float | None = None


class SearchPapersData(BaseModel):
    results: list[PaperItem]


class SearchPapersResult(ToolResult):
    data: SearchPapersData | None = None


# ─── 17. get_paper ────────────────────────────────────────────────────────────

class PaperDetail(BaseModel):
    model_config = ConfigDict(extra="allow")
    paperId: str | None = None
    primaryId: str | None = None
    ids: PaperIds | None = None
    title: str | None = None
    abstract: str | None = None
    authors: str | None = None
    categories: list[str] | None = None
    createdDate: str | None = None
    updateDate: str | None = None


class GetPaperData(BaseModel):
    paper: PaperDetail


class GetPaperResult(ToolResult):
    data: GetPaperData | None = None


# ─── 18. find_related_papers ──────────────────────────────────────────────────

class RelatedPaperItem(BaseModel):
    model_config = ConfigDict(extra="allow")
    paperId: str | None = None
    primaryId: str | None = None
    title: str | None = None
    abstract: str | None = None
    score: float | None = None


class FindRelatedPapersData(BaseModel):
    results: list[RelatedPaperItem]
    poolSize: int | None = None
    truncated: bool | None = None


class FindRelatedPapersResult(ToolResult):
    data: FindRelatedPapersData | None = None


# ─── 19. search_github ────────────────────────────────────────────────────────

class GitHubResultItem(BaseModel):
    model_config = ConfigDict(extra="allow")
    resultType: str | None = None
    repo: str | None = None
    url: str | None = None
    pageType: str | None = None
    number: int | None = None
    title: str | None = None
    snippet: str | None = None
    contentMd: str | None = None


class SearchGitHubData(BaseModel):
    results: list[GitHubResultItem]


class SearchGitHubResult(ToolResult):
    data: SearchGitHubData | None = None
