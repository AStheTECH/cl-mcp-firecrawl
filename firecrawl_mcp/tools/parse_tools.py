"""Parse group: parse_document."""

import base64
import json
import logging

from fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .. import service
from ..config import CONNECT_TIMEOUT, READ_TIMEOUT
from ..logging_utils import ToolLogger
from ..schemas import ParseData, ParseResult
from ._helpers import _err, _handle_request_exc, _upstream_err

logger = logging.getLogger("firecrawl-mcp.tools.parse")


def register_parse_tools(mcp: FastMCP) -> None:

    @mcp.tool(
        name="parse_document",
        description=(
            "Parses a local or private document (PDF, DOCX, XLSX, HTML, and more) into clean markdown "
            "or structured data. Use when the file is not publicly accessible by URL — for public URLs "
            "use `scrape_url` instead. "
            "The file must be provided as base64-encoded bytes, making this suitable for workflow "
            "chains where a previous step fetches and encodes the file content."
        ),
        annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    )
    def parse_document(
        file_content_b64: str = Field(description="Base64-encoded file bytes to parse."),
        file_name: str = Field(
            description="Filename including extension (e.g. 'report.pdf', 'data.docx'). Extension determines parser.",
        ),
        formats: list[str] = Field(
            default=["markdown"],
            description="Output formats: markdown, html, rawHtml, links, summary.",
        ),
        only_main_content: bool = Field(default=True, description="Strip headers, footers, and decorative content."),
    ) -> ParseResult:
        tlog = ToolLogger(logger, "parse_document")
        if not file_content_b64.strip():
            return _err(ParseResult, tlog, "VALIDATION_ERROR", "file_content_b64 cannot be empty", 400)
        if not file_name.strip():
            return _err(ParseResult, tlog, "VALIDATION_ERROR", "file_name cannot be empty", 400)

        try:
            file_bytes = base64.b64decode(file_content_b64)
        except Exception:
            return _err(ParseResult, tlog, "VALIDATION_ERROR", "file_content_b64 is not valid base64", 400)

        options = json.dumps({"formats": formats, "onlyMainContent": only_main_content})

        try:
            data, status, retry_after = service.firecrawl_multipart(
                "/parse", file_bytes, file_name, options,
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
            )
            if 200 <= status < 300:
                raw = data.get("data") or {}
                tlog.success()
                return ParseResult(success=True, statusCode=status, data=ParseData(**raw))
            return _upstream_err(ParseResult, tlog, status, data, retry_after)
        except Exception as exc:
            return _handle_request_exc(ParseResult, tlog, exc)
