"""Tests for all 19 MewCP Firecrawl MCP tools.

Mocks firecrawl_request / firecrawl_multipart so no real API key is needed.
Covers: input validation, success response mapping, upstream errors, auth errors.
"""

import sys
import types
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
import requests as req_lib

# ── Stub fastmcp_credentials before importing server modules ─────────────────
# Must be at module top-level so the import is resolved before any server code loads.
# ToolLogger calls get_credentials() internally — without this stub the import fails.
_cred_mod = types.ModuleType("fastmcp_credentials")
_mock_cred = MagicMock()
_mock_cred.fields = {"api_key": "fc-test-key"}
_mock_cred.extra = {"request_id": "test-req-id"}
_cred_mod.get_credentials = lambda: _mock_cred
_cred_mod.CredentialMiddleware = MagicMock()
_cred_mod.HeaderCredentialBackend = MagicMock()
sys.modules["fastmcp_credentials"] = _cred_mod

from fastmcp import FastMCP
from fastmcp.client import Client

from firecrawl_mcp.config import configure_logging
configure_logging()
from firecrawl_mcp.tools import register_tools

mcp = FastMCP("test")
register_tools(mcp)

# Marks all async def test_* functions in this module as asyncio tests.
# Requires pytest-asyncio. Eliminates the need for @pytest.mark.asyncio on every test.
pytestmark = pytest.mark.asyncio

SERVICE = "firecrawl_mcp.service.firecrawl_request"
MULTIPART = "firecrawl_mcp.service.firecrawl_multipart"


@pytest_asyncio.fixture
async def client():
    async with Client(mcp) as c:
        yield c


def ok(body: dict, status: int = 200):
    return (body, status, None)

def upstream_err(status: int = 429, body: dict | None = None):
    return (body or {"error": "rate limited"}, status, 60)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. scrape_url
# ═══════════════════════════════════════════════════════════════════════════════

class TestScrapeUrl:
    async def test_success_returns_markdown(self, client):
        with patch(SERVICE, return_value=ok({
            "success": True,
            "data": {"markdown": "# Hello", "metadata": {"scrapeId": "abc123"}}
        })):
            result = await client.call_tool("scrape_url", {"url": "https://example.com"})
        assert result.data["success"] is True
        assert result.data["statusCode"] == 200
        assert result.data["data"]["markdown"] == "# Hello"
        assert result.data["data"]["metadata"]["scrapeId"] == "abc123"

    async def test_validation_wait_for_out_of_range(self, client):
        result = await client.call_tool("scrape_url", {"url": "https://example.com", "wait_for": 99999})
        assert result.data["success"] is False
        assert result.data["statusCode"] == 400
        assert result.data["error"]["code"] == "VALIDATION_ERROR"

    async def test_validation_timeout_too_low(self, client):
        result = await client.call_tool("scrape_url", {"url": "https://example.com", "timeout_ms": 100})
        assert result.data["success"] is False
        assert result.data["statusCode"] == 400

    async def test_upstream_429(self, client):
        with patch(SERVICE, return_value=upstream_err(429)):
            result = await client.call_tool("scrape_url", {"url": "https://example.com"})
        assert result.data["success"] is False
        assert result.data["statusCode"] == 429
        assert result.data["retriable"] is True
        assert result.data["retry_after_seconds"] == 60
        assert result.data["error"]["code"] == "UPSTREAM_ERROR"

    async def test_connect_timeout(self, client):
        with patch(SERVICE, side_effect=req_lib.ConnectTimeout()):
            result = await client.call_tool("scrape_url", {"url": "https://example.com"})
        assert result.data["success"] is False
        assert result.data["statusCode"] == 408
        assert result.data["retriable"] is False

    async def test_read_timeout(self, client):
        with patch(SERVICE, side_effect=req_lib.ReadTimeout()):
            result = await client.call_tool("scrape_url", {"url": "https://example.com"})
        assert result.data["success"] is False
        assert result.data["statusCode"] == 504
        assert result.data["retriable"] is False

    async def test_auth_error(self, client):
        with patch(SERVICE, side_effect=ValueError("Missing api_key")):
            result = await client.call_tool("scrape_url", {"url": "https://example.com"})
        assert result.data["success"] is False
        assert result.data["statusCode"] == 401
        assert result.data["error"]["code"] == "AUTH_ERROR"


# ═══════════════════════════════════════════════════════════════════════════════
# 2. batch_scrape_urls
# ═══════════════════════════════════════════════════════════════════════════════

class TestBatchScrapeUrls:
    async def test_success_returns_job_id(self, client):
        with patch(SERVICE, return_value=ok({"success": True, "id": "job-1", "invalidURLs": []})):
            result = await client.call_tool("batch_scrape_urls", {"urls": ["https://a.com", "https://b.com"]})
        assert result.data["success"] is True
        assert result.data["data"]["id"] == "job-1"

    async def test_empty_urls_validation(self, client):
        result = await client.call_tool("batch_scrape_urls", {"urls": []})
        assert result.data["success"] is False
        assert result.data["error"]["code"] == "VALIDATION_ERROR"

    async def test_upstream_500_retriable(self, client):
        with patch(SERVICE, return_value=upstream_err(500, {"error": "server error"})):
            result = await client.call_tool("batch_scrape_urls", {"urls": ["https://a.com"]})
        assert result.data["success"] is False
        assert result.data["retriable"] is True


# ═══════════════════════════════════════════════════════════════════════════════
# 3. get_batch_scrape_status
# ═══════════════════════════════════════════════════════════════════════════════

class TestGetBatchScrapeStatus:
    async def test_success_completed(self, client):
        with patch(SERVICE, return_value=ok({
            "status": "completed", "total": 2, "completed": 2,
            "data": [{"markdown": "page1"}, {"markdown": "page2"}]
        })):
            result = await client.call_tool("get_batch_scrape_status", {"job_id": "job-1"})
        assert result.data["success"] is True
        assert result.data["data"]["status"] == "completed"
        assert result.data["data"]["total"] == 2
        assert len(result.data["data"]["data"]) == 2

    async def test_empty_job_id_validation(self, client):
        result = await client.call_tool("get_batch_scrape_status", {"job_id": "   "})
        assert result.data["success"] is False
        assert result.data["error"]["code"] == "VALIDATION_ERROR"

    async def test_still_processing(self, client):
        with patch(SERVICE, return_value=ok({"status": "scraping", "total": 10, "completed": 3})):
            result = await client.call_tool("get_batch_scrape_status", {"job_id": "job-1"})
        assert result.data["success"] is True
        assert result.data["data"]["status"] == "scraping"


# ═══════════════════════════════════════════════════════════════════════════════
# 4. cancel_batch_scrape
# ═══════════════════════════════════════════════════════════════════════════════

class TestCancelBatchScrape:
    async def test_success(self, client):
        with patch(SERVICE, return_value=ok({"status": "cancelled"})):
            result = await client.call_tool("cancel_batch_scrape", {"job_id": "job-1"})
        assert result.data["success"] is True
        assert result.data["data"]["status"] == "cancelled"

    async def test_empty_job_id(self, client):
        result = await client.call_tool("cancel_batch_scrape", {"job_id": ""})
        assert result.data["success"] is False
        assert result.data["error"]["code"] == "VALIDATION_ERROR"


# ═══════════════════════════════════════════════════════════════════════════════
# 5. crawl_url
# ═══════════════════════════════════════════════════════════════════════════════

class TestCrawlUrl:
    async def test_success_returns_job_id(self, client):
        with patch(SERVICE, return_value=ok({"success": True, "id": "crawl-1", "url": "https://status/crawl-1"})):
            result = await client.call_tool("crawl_url", {"url": "https://example.com"})
        assert result.data["success"] is True
        assert result.data["data"]["id"] == "crawl-1"

    async def test_invalid_limit(self, client):
        result = await client.call_tool("crawl_url", {"url": "https://example.com", "limit": 0})
        assert result.data["success"] is False
        assert result.data["error"]["code"] == "VALIDATION_ERROR"

    async def test_invalid_sitemap_value(self, client):
        result = await client.call_tool("crawl_url", {"url": "https://example.com", "sitemap": "bad"})
        assert result.data["success"] is False
        assert result.data["error"]["code"] == "VALIDATION_ERROR"

    async def test_upstream_402_payment(self, client):
        with patch(SERVICE, return_value=upstream_err(402, {"error": "Payment required"})):
            result = await client.call_tool("crawl_url", {"url": "https://example.com"})
        assert result.data["success"] is False
        assert result.data["statusCode"] == 402
        assert result.data["retriable"] is False


# ═══════════════════════════════════════════════════════════════════════════════
# 6. get_crawl_status
# ═══════════════════════════════════════════════════════════════════════════════

class TestGetCrawlStatus:
    async def test_success_with_pages(self, client):
        with patch(SERVICE, return_value=ok({
            "status": "completed", "total": 5, "completed": 5,
            "creditsUsed": 10, "data": [{"markdown": "p1"}]
        })):
            result = await client.call_tool("get_crawl_status", {"job_id": "crawl-1"})
        assert result.data["success"] is True
        assert result.data["data"]["creditsUsed"] == 10

    async def test_empty_job_id(self, client):
        result = await client.call_tool("get_crawl_status", {"job_id": ""})
        assert result.data["success"] is False


# ═══════════════════════════════════════════════════════════════════════════════
# 7. cancel_crawl
# ═══════════════════════════════════════════════════════════════════════════════

class TestCancelCrawl:
    async def test_success(self, client):
        with patch(SERVICE, return_value=ok({"status": "cancelled"})):
            result = await client.call_tool("cancel_crawl", {"job_id": "crawl-1"})
        assert result.data["success"] is True

    async def test_404_not_found(self, client):
        with patch(SERVICE, return_value=upstream_err(404, {"error": "Crawl job not found."})):
            result = await client.call_tool("cancel_crawl", {"job_id": "nonexistent"})
        assert result.data["success"] is False
        assert result.data["statusCode"] == 404
        assert result.data["retriable"] is False


# ═══════════════════════════════════════════════════════════════════════════════
# 8. map_url
# ═══════════════════════════════════════════════════════════════════════════════

class TestMapUrl:
    async def test_success_object_links(self, client):
        with patch(SERVICE, return_value=ok({
            "success": True,
            "links": [
                {"url": "https://a.com/page1", "title": "Page 1"},
                {"url": "https://a.com/page2"},
            ]
        })):
            result = await client.call_tool("map_url", {"url": "https://a.com"})
        assert result.data["success"] is True
        assert len(result.data["data"]["links"]) == 2
        assert result.data["data"]["links"][0]["url"] == "https://a.com/page1"
        assert result.data["data"]["links"][0]["title"] == "Page 1"
        assert result.data["data"]["links"][1]["title"] is None

    async def test_success_string_links(self, client):
        with patch(SERVICE, return_value=ok({
            "success": True,
            "links": ["https://a.com/page1", "https://a.com/page2"]
        })):
            result = await client.call_tool("map_url", {"url": "https://a.com"})
        assert result.data["success"] is True
        assert result.data["data"]["links"][0]["url"] == "https://a.com/page1"

    async def test_invalid_limit(self, client):
        result = await client.call_tool("map_url", {"url": "https://a.com", "limit": 200000})
        assert result.data["success"] is False
        assert result.data["error"]["code"] == "VALIDATION_ERROR"


# ═══════════════════════════════════════════════════════════════════════════════
# 9. search_web
# ═══════════════════════════════════════════════════════════════════════════════

class TestSearchWeb:
    async def test_success_web_results(self, client):
        with patch(SERVICE, return_value=ok({
            "success": True,
            "data": {
                "web": [{"url": "https://x.com", "title": "X", "description": "desc"}],
                "images": [],
                "news": []
            },
            "creditsUsed": 5
        })):
            result = await client.call_tool("search_web", {"query": "python web scraping"})
        assert result.data["success"] is True
        assert len(result.data["data"]["results"]["web"]) == 1
        assert result.data["data"]["results"]["web"][0]["url"] == "https://x.com"
        assert result.data["data"]["creditsUsed"] == 5

    async def test_invalid_limit(self, client):
        result = await client.call_tool("search_web", {"query": "test", "limit": 200})
        assert result.data["success"] is False
        assert result.data["error"]["code"] == "VALIDATION_ERROR"

    async def test_mutually_exclusive_domains(self, client):
        result = await client.call_tool("search_web", {
            "query": "test", "include_domains": ["a.com"], "exclude_domains": ["b.com"]
        })
        assert result.data["success"] is False
        assert result.data["error"]["code"] == "VALIDATION_ERROR"

    async def test_news_results(self, client):
        with patch(SERVICE, return_value=ok({
            "success": True,
            "data": {
                "web": [],
                "news": [{"title": "Breaking", "url": "https://news.com", "date": "2024-01-01"}]
            }
        })):
            result = await client.call_tool("search_web", {"query": "AI news", "sources": ["news"]})
        assert result.data["success"] is True
        assert len(result.data["data"]["results"]["news"]) == 1
        assert result.data["data"]["results"]["news"][0]["title"] == "Breaking"


# ═══════════════════════════════════════════════════════════════════════════════
# 10. parse_document
# ═══════════════════════════════════════════════════════════════════════════════

class TestParseDocument:
    def _b64(self, content: str = "PDF content here") -> str:
        import base64
        return base64.b64encode(content.encode()).decode()

    async def test_success(self, client):
        with patch(MULTIPART, return_value=ok({
            "success": True,
            "data": {"markdown": "# Parsed Doc", "links": ["https://ref.com"]}
        })):
            result = await client.call_tool("parse_document", {
                "file_content_b64": self._b64(), "file_name": "report.pdf"
            })
        assert result.data["success"] is True
        assert result.data["data"]["markdown"] == "# Parsed Doc"
        assert result.data["data"]["links"] == ["https://ref.com"]

    async def test_empty_file_content(self, client):
        result = await client.call_tool("parse_document", {
            "file_content_b64": "   ", "file_name": "report.pdf"
        })
        assert result.data["success"] is False
        assert result.data["error"]["code"] == "VALIDATION_ERROR"

    async def test_empty_file_name(self, client):
        result = await client.call_tool("parse_document", {
            "file_content_b64": self._b64(), "file_name": ""
        })
        assert result.data["success"] is False
        assert result.data["error"]["code"] == "VALIDATION_ERROR"

    async def test_invalid_base64(self, client):
        result = await client.call_tool("parse_document", {
            "file_content_b64": "not-valid-base64!!!", "file_name": "doc.pdf"
        })
        assert result.data["success"] is False
        assert result.data["error"]["code"] == "VALIDATION_ERROR"


# ═══════════════════════════════════════════════════════════════════════════════
# 11. run_agent
# ═══════════════════════════════════════════════════════════════════════════════

class TestRunAgent:
    async def test_success_returns_job_id(self, client):
        with patch(SERVICE, return_value=ok({
            "success": True, "id": "agent-1", "status": "processing"
        })):
            result = await client.call_tool("run_agent", {"prompt": "Find the founders of Firecrawl"})
        assert result.data["success"] is True
        assert result.data["data"]["id"] == "agent-1"
        assert result.data["data"]["status"] == "processing"

    async def test_empty_prompt(self, client):
        result = await client.call_tool("run_agent", {"prompt": "   "})
        assert result.data["success"] is False
        assert result.data["error"]["code"] == "VALIDATION_ERROR"

    async def test_invalid_model(self, client):
        result = await client.call_tool("run_agent", {"prompt": "Find data", "model": "gpt-4"})
        assert result.data["success"] is False
        assert result.data["error"]["code"] == "VALIDATION_ERROR"

    async def test_invalid_schema_json(self, client):
        result = await client.call_tool("run_agent", {"prompt": "Find data", "schema": "{not valid json"})
        assert result.data["success"] is False
        assert result.data["error"]["code"] == "VALIDATION_ERROR"

    async def test_valid_schema(self, client):
        with patch(SERVICE, return_value=ok({"id": "agent-2", "status": "processing"})):
            result = await client.call_tool("run_agent", {
                "prompt": "Find data",
                "schema": '{"type": "object", "properties": {"name": {"type": "string"}}}'
            })
        assert result.data["success"] is True

    async def test_completed_response_includes_data(self, client):
        with patch(SERVICE, return_value=ok({
            "id": "agent-3", "status": "completed",
            "data": {"founders": [{"name": "Eric"}]},
            "creditsUsed": 15
        })):
            result = await client.call_tool("run_agent", {"prompt": "Find founders"})
        assert result.data["success"] is True
        assert result.data["data"]["status"] == "completed"
        assert result.data["data"]["data"]["founders"][0]["name"] == "Eric"
        assert result.data["data"]["creditsUsed"] == 15


# ═══════════════════════════════════════════════════════════════════════════════
# 12. get_agent_status
# ═══════════════════════════════════════════════════════════════════════════════

class TestGetAgentStatus:
    async def test_processing(self, client):
        with patch(SERVICE, return_value=ok({"status": "processing", "expiresAt": "2024-12-15T00:00:00Z"})):
            result = await client.call_tool("get_agent_status", {"job_id": "agent-1"})
        assert result.data["success"] is True
        assert result.data["data"]["status"] == "processing"

    async def test_empty_job_id(self, client):
        result = await client.call_tool("get_agent_status", {"job_id": ""})
        assert result.data["success"] is False


# ═══════════════════════════════════════════════════════════════════════════════
# 13. cancel_agent
# ═══════════════════════════════════════════════════════════════════════════════

class TestCancelAgent:
    async def test_success(self, client):
        with patch(SERVICE, return_value=ok({"status": "cancelled"})):
            result = await client.call_tool("cancel_agent", {"job_id": "agent-1"})
        assert result.data["success"] is True
        assert result.data["data"]["status"] == "cancelled"

    async def test_empty_job_id(self, client):
        result = await client.call_tool("cancel_agent", {"job_id": "  "})
        assert result.data["success"] is False


# ═══════════════════════════════════════════════════════════════════════════════
# 14. browser_interact
# ═══════════════════════════════════════════════════════════════════════════════

class TestBrowserInteract:
    async def test_success_with_code(self, client):
        with patch(SERVICE, return_value=ok({
            "success": True,
            "result": '{"title": "Example"}',
            "stdout": "",
            "exitCode": 0,
            "killed": False,
            "cdpUrl": "wss://browser.firecrawl.dev/...",
        })):
            result = await client.call_tool("browser_interact", {
                "scrape_id": "scrape-abc",
                "code": "const t = await page.title(); JSON.stringify({title: t});",
            })
        assert result.data["success"] is True
        assert result.data["data"]["exitCode"] == 0
        assert result.data["data"]["cdpUrl"].startswith("wss://")

    async def test_success_with_prompt(self, client):
        with patch(SERVICE, return_value=ok({
            "success": True,
            "output": "The Pro plan costs $49/month.",
            "exitCode": 0,
        })):
            result = await client.call_tool("browser_interact", {
                "scrape_id": "scrape-abc", "prompt_text": "Find the Pro plan price"
            })
        assert result.data["success"] is True
        assert result.data["data"]["output"] == "The Pro plan costs $49/month."

    async def test_both_code_and_prompt_rejected(self, client):
        result = await client.call_tool("browser_interact", {
            "scrape_id": "abc", "code": "some code", "prompt_text": "some prompt"
        })
        assert result.data["success"] is False
        assert result.data["error"]["code"] == "VALIDATION_ERROR"

    async def test_neither_code_nor_prompt_rejected(self, client):
        result = await client.call_tool("browser_interact", {"scrape_id": "abc"})
        assert result.data["success"] is False
        assert result.data["error"]["code"] == "VALIDATION_ERROR"

    async def test_invalid_language(self, client):
        result = await client.call_tool("browser_interact", {
            "scrape_id": "abc", "code": "x", "language": "ruby"
        })
        assert result.data["success"] is False
        assert result.data["error"]["code"] == "VALIDATION_ERROR"

    async def test_empty_scrape_id(self, client):
        result = await client.call_tool("browser_interact", {"scrape_id": "  ", "code": "x"})
        assert result.data["success"] is False

    async def test_timeout_out_of_range(self, client):
        result = await client.call_tool("browser_interact", {
            "scrape_id": "abc", "code": "x", "timeout": 999
        })
        assert result.data["success"] is False
        assert result.data["error"]["code"] == "VALIDATION_ERROR"


# ═══════════════════════════════════════════════════════════════════════════════
# 15. browser_close
# ═══════════════════════════════════════════════════════════════════════════════

class TestBrowserClose:
    async def test_success(self, client):
        with patch(SERVICE, return_value=ok({"status": "closed"})):
            result = await client.call_tool("browser_close", {"scrape_id": "scrape-abc"})
        assert result.data["success"] is True
        assert result.data["data"]["status"] == "closed"

    async def test_empty_scrape_id(self, client):
        result = await client.call_tool("browser_close", {"scrape_id": ""})
        assert result.data["success"] is False


# ═══════════════════════════════════════════════════════════════════════════════
# 16. search_papers
# ═══════════════════════════════════════════════════════════════════════════════

class TestSearchPapers:
    async def test_success(self, client):
        with patch(SERVICE, return_value=ok({
            "success": True,
            "results": [{
                "paperId": "123",
                "primaryId": "arxiv:2105.05233",
                "title": "Diffusion Models Beat GANs",
                "abstract": "We show that...",
                "score": 0.016,
            }]
        })):
            result = await client.call_tool("search_papers", {"query": "diffusion models image synthesis"})
        assert result.data["success"] is True
        assert len(result.data["data"]["results"]) == 1
        assert result.data["data"]["results"][0]["paperId"] == "123"
        assert result.data["data"]["results"][0]["score"] == pytest.approx(0.016)

    async def test_empty_query(self, client):
        result = await client.call_tool("search_papers", {"query": "  "})
        assert result.data["success"] is False
        assert result.data["error"]["code"] == "VALIDATION_ERROR"

    async def test_k_out_of_range(self, client):
        result = await client.call_tool("search_papers", {"query": "test", "k": 0})
        assert result.data["success"] is False

    async def test_with_filters(self, client):
        with patch(SERVICE, return_value=ok({"success": True, "results": []})):
            result = await client.call_tool("search_papers", {
                "query": "LLMs", "authors": "Vaswani", "categories": "cs.LG", "from_date": "2023-01-01"
            })
        assert result.data["success"] is True
        assert result.data["data"]["results"] == []


# ═══════════════════════════════════════════════════════════════════════════════
# 17. get_paper
# ═══════════════════════════════════════════════════════════════════════════════

class TestGetPaper:
    async def test_success(self, client):
        with patch(SERVICE, return_value=ok({
            "success": True,
            "paper": {
                "paperId": "123",
                "title": "Diffusion Models Beat GANs",
                "authors": "Dhariwal, Nichol",
                "categories": ["cs.LG"],
                "createdDate": "Wed, 11 May 2021 18:01:01 GMT",
            }
        })):
            result = await client.call_tool("get_paper", {"paper_id": "arxiv:2105.05233"})
        assert result.data["success"] is True
        assert result.data["data"]["paper"]["authors"] == "Dhariwal, Nichol"
        assert "cs.LG" in result.data["data"]["paper"]["categories"]

    async def test_empty_paper_id(self, client):
        result = await client.call_tool("get_paper", {"paper_id": "  "})
        assert result.data["success"] is False

    async def test_404_not_found(self, client):
        with patch(SERVICE, return_value=upstream_err(404, {"error": "Paper not found"})):
            result = await client.call_tool("get_paper", {"paper_id": "nonexistent"})
        assert result.data["success"] is False
        assert result.data["statusCode"] == 404
        assert result.data["retriable"] is False


# ═══════════════════════════════════════════════════════════════════════════════
# 18. find_related_papers
# ═══════════════════════════════════════════════════════════════════════════════

class TestFindRelatedPapers:
    async def test_success_similar_mode(self, client):
        with patch(SERVICE, return_value=ok({
            "success": True,
            "results": [{"paperId": "456", "title": "DDPM", "score": 0.032}],
            "poolSize": 40,
            "truncated": False,
        })):
            result = await client.call_tool("find_related_papers", {
                "paper_id": "123", "intent": "image synthesis improvements"
            })
        assert result.data["success"] is True
        assert result.data["data"]["poolSize"] == 40
        assert result.data["data"]["truncated"] is False
        assert result.data["data"]["results"][0]["title"] == "DDPM"

    async def test_empty_paper_id(self, client):
        result = await client.call_tool("find_related_papers", {"paper_id": "", "intent": "test"})
        assert result.data["success"] is False

    async def test_empty_intent(self, client):
        result = await client.call_tool("find_related_papers", {"paper_id": "123", "intent": "  "})
        assert result.data["success"] is False
        assert result.data["error"]["code"] == "VALIDATION_ERROR"

    async def test_invalid_mode(self, client):
        result = await client.call_tool("find_related_papers", {
            "paper_id": "123", "intent": "test", "mode": "backwards"
        })
        assert result.data["success"] is False
        assert result.data["error"]["code"] == "VALIDATION_ERROR"

    async def test_citers_mode(self, client):
        with patch(SERVICE, return_value=ok({"success": True, "results": [], "poolSize": 0, "truncated": False})):
            result = await client.call_tool("find_related_papers", {
                "paper_id": "123", "intent": "test", "mode": "citers"
            })
        assert result.data["success"] is True

    async def test_k_out_of_range(self, client):
        result = await client.call_tool("find_related_papers", {
            "paper_id": "123", "intent": "test", "k": 999
        })
        assert result.data["success"] is False


# ═══════════════════════════════════════════════════════════════════════════════
# 19. search_github
# ═══════════════════════════════════════════════════════════════════════════════

class TestSearchGitHub:
    async def test_success(self, client):
        with patch(SERVICE, return_value=ok({
            "success": True,
            "results": [{
                "resultType": "issue",
                "repo": "firecrawl/firecrawl",
                "url": "https://github.com/firecrawl/firecrawl/issues/123",
                "number": 123,
                "title": "Worker shutdown race",
                "snippet": "Queue worker shutdown can lose...",
            }]
        })):
            result = await client.call_tool("search_github", {"query": "race condition worker shutdown"})
        assert result.data["success"] is True
        assert len(result.data["data"]["results"]) == 1
        assert result.data["data"]["results"][0]["repo"] == "firecrawl/firecrawl"
        assert result.data["data"]["results"][0]["number"] == 123

    async def test_empty_query(self, client):
        result = await client.call_tool("search_github", {"query": ""})
        assert result.data["success"] is False
        assert result.data["error"]["code"] == "VALIDATION_ERROR"

    async def test_k_out_of_range(self, client):
        result = await client.call_tool("search_github", {"query": "test", "k": 200})
        assert result.data["success"] is False

    async def test_empty_results(self, client):
        with patch(SERVICE, return_value=ok({"success": True, "results": []})):
            result = await client.call_tool("search_github", {"query": "obscure query no results"})
        assert result.data["success"] is True
        assert result.data["data"]["results"] == []

    async def test_network_error_retriable(self, client):
        with patch(SERVICE, side_effect=req_lib.ConnectionError("Network down")):
            result = await client.call_tool("search_github", {"query": "test"})
        assert result.data["success"] is False
        assert result.data["retriable"] is True
        assert result.data["statusCode"] == 503


# ═══════════════════════════════════════════════════════════════════════════════
# Tool annotation checks
# ═══════════════════════════════════════════════════════════════════════════════

class TestAnnotations:
    """Verify every tool has correct MewCP tier annotations."""

    READ_ONLY = {
        "scrape_url", "get_batch_scrape_status", "get_crawl_status",
        "map_url", "search_web", "parse_document", "get_agent_status",
        "search_papers", "get_paper", "find_related_papers", "search_github",
    }
    DESTRUCTIVE = {
        "cancel_batch_scrape", "cancel_crawl", "cancel_agent", "browser_close",
    }
    CREATE = {
        "batch_scrape_urls", "crawl_url", "run_agent",
    }
    UPDATE = {
        "browser_interact",
    }

    async def test_read_only_tools_have_correct_annotations(self):
        for name in self.READ_ONLY:
            t = await mcp.get_tool(name)
            ann = t.annotations
            assert ann.readOnlyHint is True, f"{name}: expected readOnlyHint=True"
            assert ann.openWorldHint is True, f"{name}: expected openWorldHint=True"

    async def test_destructive_tools_have_correct_annotations(self):
        for name in self.DESTRUCTIVE:
            t = await mcp.get_tool(name)
            ann = t.annotations
            assert ann.destructiveHint is True, f"{name}: expected destructiveHint=True"
            assert ann.openWorldHint is True, f"{name}: expected openWorldHint=True"

    async def test_create_tools_have_correct_annotations(self):
        for name in self.CREATE:
            t = await mcp.get_tool(name)
            ann = t.annotations
            assert ann.readOnlyHint is False, f"{name}: expected readOnlyHint=False"
            assert ann.destructiveHint is False, f"{name}: expected destructiveHint=False"
            assert ann.openWorldHint is True, f"{name}: expected openWorldHint=True"

    async def test_all_19_tools_registered(self, client):
        tools = await client.list_tools()
        names = {t.name for t in tools}
        expected = self.READ_ONLY | self.DESTRUCTIVE | self.CREATE | self.UPDATE
        assert names == expected, f"Missing: {expected - names}, Extra: {names - expected}"
