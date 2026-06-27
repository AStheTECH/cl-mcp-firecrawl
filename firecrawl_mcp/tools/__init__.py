"""MewCP Firecrawl tool registration."""

from fastmcp import FastMCP

from .agent_tools import register_agent_tools
from .browser_tools import register_browser_tools
from .crawl_tools import register_crawl_tools
from .discover_tools import register_discover_tools
from .parse_tools import register_parse_tools
from .research_tools import register_research_tools
from .scrape_tools import register_scrape_tools


def register_tools(mcp: FastMCP) -> None:
    register_scrape_tools(mcp)
    register_crawl_tools(mcp)
    register_discover_tools(mcp)
    register_parse_tools(mcp)
    register_agent_tools(mcp)
    register_browser_tools(mcp)
    register_research_tools(mcp)
