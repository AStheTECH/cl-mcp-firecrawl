#!/usr/bin/env python3
"""MCP Server for Firecrawl API.

Curious Layer Firecrawl MCP Server - A stateless, multi-tenant MCP server
that exposes Firecrawl's web scraping, crawling, and search capabilities.
"""

import logging

from fastmcp import FastMCP
from fastmcp_credentials import CredentialMiddleware, HeaderCredentialBackend

from firecrawl_mcp.cli import parse_args
from firecrawl_mcp.config import configure_logging
from firecrawl_mcp.tools import register_tools

configure_logging()
logger = logging.getLogger("firecrawl-mcp-server")

backend = HeaderCredentialBackend()
mcp = FastMCP("MewCP Firecrawl MCP Server", middleware=[CredentialMiddleware(backend, "static")]
)
register_tools(mcp)

# Expose ASGI app for hosting platform's (e.g. Vercel) Python runtime.
app = mcp.http_app(path="/mcp", transport="streamable-http", stateless_http=True)

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Firecrawl MCP Server Starting")
    logger.info("=" * 60)

    args = parse_args()

    run_kwargs = {}
    if args.transport:
        run_kwargs["transport"] = args.transport
        logger.info(f"Transport: {args.transport}")
    if args.host:
        run_kwargs["host"] = args.host
        logger.info(f"Host: {args.host}")
    if args.port:
        run_kwargs["port"] = args.port
        logger.info(f"Port: {args.port}")

    try:
        mcp.run(**run_kwargs)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server crashed: {e}", exc_info=True)
        raise
