"""Research Index group: search_papers, get_paper, find_related_papers, search_github."""

import logging

from fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .. import service
from ..config import CONNECT_TIMEOUT, POLL_TIMEOUT
from ..logging_utils import ToolLogger
from ..schemas import (
    FindRelatedPapersData,
    FindRelatedPapersResult,
    GetPaperData,
    GetPaperResult,
    GitHubResultItem,
    PaperDetail,
    PaperItem,
    RelatedPaperItem,
    SearchGitHubData,
    SearchGitHubResult,
    SearchPapersData,
    SearchPapersResult,
)
from ._helpers import _err, _handle_request_exc, _upstream_err

logger = logging.getLogger("firecrawl-mcp.tools.research")


def register_research_tools(mcp: FastMCP) -> None:

    @mcp.tool(
        name="search_papers",
        description=(
            "Searches Firecrawl's academic research index by topic, method, benchmark, or author. "
            "Returns ranked papers with paperId, title, abstract, and relevance score. "
            "Use `paperId` from results to call `get_paper` or `find_related_papers`. "
            "Supports filtering by author name substring, category (e.g. 'cs.LG'), and date range."
        ),
        annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    )
    def search_papers(
        query: str = Field(description="Natural language search query (e.g. 'diffusion models image synthesis')."),
        k: int = Field(default=40, description="Maximum number of ranked papers to return (1–500)."),
        authors: str | None = Field(default=None, description="Filter by author name substring (e.g. 'LeCun'). Comma-separate for multiple."),
        categories: str | None = Field(default=None, description="Filter by paper category (e.g. 'cs.LG', 'cs.CV'). Comma-separate for multiple."),
        from_date: str | None = Field(default=None, description="Inclusive lower bound on paper date in YYYY-MM-DD format (e.g. '2023-01-01')."),
        to_date: str | None = Field(default=None, description="Inclusive upper bound on paper date in YYYY-MM-DD format."),
    ) -> SearchPapersResult:
        tlog = ToolLogger(logger, "search_papers")
        if not query.strip():
            return _err(SearchPapersResult, tlog, "VALIDATION_ERROR", "query cannot be empty", 400)
        if k < 1 or k > 500:
            return _err(SearchPapersResult, tlog, "VALIDATION_ERROR", "k must be 1–500", 400)

        params: dict = {"query": query, "k": k}
        if authors:
            params["authors"] = authors
        if categories:
            params["categories"] = categories
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date

        try:
            data, status, retry_after = service.firecrawl_request(
                "GET", "/search/research/papers", params=params,
                timeout=(CONNECT_TIMEOUT, POLL_TIMEOUT),
            )
            if 200 <= status < 300:
                results = [PaperItem(**p) for p in (data.get("results") or [])]
                tlog.success()
                return SearchPapersResult(
                    success=True, statusCode=status,
                    data=SearchPapersData(results=results),
                )
            return _upstream_err(SearchPapersResult, tlog, status, data, retry_after)
        except Exception as exc:
            return _handle_request_exc(SearchPapersResult, tlog, exc)

    @mcp.tool(
        name="get_paper",
        description=(
            "Retrieves full details for a specific research paper by its ID. "
            "Returns title, abstract, authors, categories, and dates. "
            "The `paper_id` can be a canonical paperId (e.g. '2014215642691656232') "
            "or a source-prefixed ID (e.g. 'arxiv:2105.05233') from `search_papers` results."
        ),
        annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    )
    def get_paper(
        paper_id: str = Field(description="Paper ID — either canonical paperId or source-prefixed ID like 'arxiv:2105.05233'."),
        k: int | None = Field(default=None, description="Number of related papers to include alongside the paper details."),
    ) -> GetPaperResult:
        tlog = ToolLogger(logger, "get_paper")
        if not paper_id.strip():
            return _err(GetPaperResult, tlog, "VALIDATION_ERROR", "paper_id cannot be empty", 400)

        params: dict = {}
        if k is not None:
            params["k"] = k

        try:
            data, status, retry_after = service.firecrawl_request(
                "GET", f"/search/research/papers/{paper_id}",
                params=params or None,
                timeout=(CONNECT_TIMEOUT, POLL_TIMEOUT),
            )
            if 200 <= status < 300:
                paper_raw = data.get("paper") or {}
                tlog.success()
                return GetPaperResult(
                    success=True, statusCode=status,
                    data=GetPaperData(paper=PaperDetail(**paper_raw)),
                )
            return _upstream_err(GetPaperResult, tlog, status, data, retry_after)
        except Exception as exc:
            return _handle_request_exc(GetPaperResult, tlog, exc)

    @mcp.tool(
        name="find_related_papers",
        description=(
            "Finds papers related to a seed paper, ranked by semantic relevance to an intent. "
            "Use `mode` to choose expansion strategy: 'similar' (semantically close), "
            "'citers' (papers that cite the seed), 'references' (papers cited by the seed). "
            "Returns ranked results with relevance scores. "
            "Ideal for literature review workflows: search_papers → find_related_papers → get_paper."
        ),
        annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    )
    def find_related_papers(
        paper_id: str = Field(description="Seed paper ID (canonical paperId or 'arxiv:XXXX.XXXXX')."),
        intent: str = Field(description="Natural language ranking intent (e.g. 'applications in medical imaging')."),
        mode: str = Field(default="similar", description="Expansion mode: 'similar' (default), 'citers', or 'references'."),
        k: int = Field(default=40, description="Maximum number of related papers to return (1–500)."),
        rerank: bool = Field(default=False, description="Apply an additional reranking pass over the fused candidate set."),
    ) -> FindRelatedPapersResult:
        tlog = ToolLogger(logger, "find_related_papers")
        if not paper_id.strip():
            return _err(FindRelatedPapersResult, tlog, "VALIDATION_ERROR", "paper_id cannot be empty", 400)
        if not intent.strip():
            return _err(FindRelatedPapersResult, tlog, "VALIDATION_ERROR", "intent cannot be empty", 400)
        if mode not in ("similar", "citers", "references"):
            return _err(FindRelatedPapersResult, tlog, "VALIDATION_ERROR",
                        "mode must be similar, citers, or references", 400)
        if k < 1 or k > 500:
            return _err(FindRelatedPapersResult, tlog, "VALIDATION_ERROR", "k must be 1–500", 400)

        params: dict = {"intent": intent, "mode": mode, "k": k, "rerank": rerank}

        try:
            data, status, retry_after = service.firecrawl_request(
                "GET", f"/search/research/papers/{paper_id}/similar", params=params,
                timeout=(CONNECT_TIMEOUT, POLL_TIMEOUT),
            )
            if 200 <= status < 300:
                results = [RelatedPaperItem(**p) for p in (data.get("results") or [])]
                tlog.success()
                return FindRelatedPapersResult(
                    success=True, statusCode=status,
                    data=FindRelatedPapersData(
                        results=results,
                        poolSize=data.get("poolSize"),
                        truncated=data.get("truncated"),
                    ),
                )
            return _upstream_err(FindRelatedPapersResult, tlog, status, data, retry_after)
        except Exception as exc:
            return _handle_request_exc(FindRelatedPapersResult, tlog, exc)

    @mcp.tool(
        name="search_github",
        description=(
            "Searches GitHub issue history, pull requests, discussions, and repository READMEs "
            "using natural language. Returns matched content with repository metadata, URLs, "
            "and markdown snippets. "
            "Useful for researching how a bug was fixed, what a library's maintainers have said, "
            "or finding prior art in open source projects."
        ),
        annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    )
    def search_github(
        query: str = Field(description="Natural language query (e.g. 'race condition in worker shutdown firecrawl')."),
        k: int = Field(default=20, description="Maximum number of results to return (1–100)."),
    ) -> SearchGitHubResult:
        tlog = ToolLogger(logger, "search_github")
        if not query.strip():
            return _err(SearchGitHubResult, tlog, "VALIDATION_ERROR", "query cannot be empty", 400)
        if k < 1 or k > 100:
            return _err(SearchGitHubResult, tlog, "VALIDATION_ERROR", "k must be 1–100", 400)

        try:
            data, status, retry_after = service.firecrawl_request(
                "GET", "/search/research/github",
                params={"query": query, "k": k},
                timeout=(CONNECT_TIMEOUT, POLL_TIMEOUT),
            )
            if 200 <= status < 300:
                results = [GitHubResultItem(**r) for r in (data.get("results") or [])]
                tlog.success()
                return SearchGitHubResult(
                    success=True, statusCode=status,
                    data=SearchGitHubData(results=results),
                )
            return _upstream_err(SearchGitHubResult, tlog, status, data, retry_after)
        except Exception as exc:
            return _handle_request_exc(SearchGitHubResult, tlog, exc)
