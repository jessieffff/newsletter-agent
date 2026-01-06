"""
Bootstrap MCP-like tools.

Registers all available tools in the registry.
"""

from .registry import register_tool
from .types import ToolResult
from .adapters import (
    fetch_rss_items,
    search_web_fresh,
    search_web_custom_domains,
    fetch_nyt_items,
    fetch_x_items,
)


def register_all_tools() -> None:
    """
    Register all available tools in the global registry.
    
    This should be called once at application startup.
    """
    # Register RSS tool
    register_tool(
        name="fetch_rss_items",
        handler=fetch_rss_items,
        output_schema=ToolResult,
        description="Fetch and normalize RSS/Atom feed items",
    )
    
    # Register web search tool
    register_tool(
        name="search_web_fresh",
        handler=search_web_fresh,
        output_schema=ToolResult,
        description="Search the web for fresh results using Foundry grounding",
    )
    
    # Register custom domain search tool
    register_tool(
        name="search_web_custom_domains",
        handler=search_web_custom_domains,
        output_schema=ToolResult,
        description="Search within custom allowed domains",
    )
    
    # Register NYT tool
    register_tool(
        name="fetch_nyt_items",
        handler=fetch_nyt_items,
        output_schema=ToolResult,
        description="Fetch articles from NYT Article Search API",
    )
    
    # Register X (Twitter) tool
    register_tool(
        name="fetch_x_items",
        handler=fetch_x_items,
        output_schema=ToolResult,
        description="Fetch recent tweets from X (Twitter) API",
    )


# Auto-register on import (optional - can be called explicitly instead)
# register_all_tools()
