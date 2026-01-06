"""
Tool adapters for standardized integrations.

Adapters normalize external API responses to the standard ToolResult shape.
"""

from .rss_adapter import fetch_rss_items
from .web_search_adapter import search_web_fresh
from .custom_search_adapter import search_web_custom_domains
from .nyt_adapter import fetch_nyt_items
from .x_adapter import fetch_x_items

__all__ = [
    "fetch_rss_items",
    "search_web_fresh",
    "search_web_custom_domains",
    "fetch_nyt_items",
    "fetch_x_items",
]
