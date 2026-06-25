"""MewCP Firecrawl tool registration."""

from fastmcp import FastMCP

from .agent import register_agent_tools
from .browser import register_browser_tools
from .crawl import register_crawl_tools
from .discover import register_discover_tools
from .parse import register_parse_tools
from .research import register_research_tools
from .scrape import register_scrape_tools


def register_tools(mcp: FastMCP) -> None:
    register_scrape_tools(mcp)
    register_crawl_tools(mcp)
    register_discover_tools(mcp)
    register_parse_tools(mcp)
    register_agent_tools(mcp)
    register_browser_tools(mcp)
    register_research_tools(mcp)
