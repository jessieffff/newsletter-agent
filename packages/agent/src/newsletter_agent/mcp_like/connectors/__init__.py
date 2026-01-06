"""
Network connectors for external APIs.

These modules encapsulate the actual HTTP calls to external services.
"""

from .rss_connector import fetch_and_parse_rss
from .web_search_connector import search_bing, search_custom
from .nyt_connector import search_nyt
from .x_connector import search_x

__all__ = [
    "fetch_and_parse_rss",
    "search_bing",
    "search_custom",
    "search_nyt",
    "search_x",
]
