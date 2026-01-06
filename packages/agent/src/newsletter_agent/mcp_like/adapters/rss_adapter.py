"""
RSS feed adapter.

Fetches RSS feeds and normalizes to standard ToolResult shape.
"""

from typing import Dict, Any
from datetime import datetime
from dateutil import parser as date_parser

from ..types import ToolResult, ToolItem, ToolMeta
from ..errors import InvalidInputError
from ..policy import normalize_url, validate_url, is_safe_url, clean_snippet
from ..connectors import fetch_and_parse_rss


def fetch_rss_items(payload: Dict[str, Any]) -> ToolResult:
    """
    Fetch items from an RSS/Atom feed.
    
    Args:
        payload: Input parameters
            - feed_url (str): RSS feed URL
            - max_items (int, optional): Maximum items to return (default: 25)
            
    Returns:
        ToolResult with normalized items
    """
    # Validate and extract input
    feed_url = payload.get("feed_url")
    if not feed_url:
        raise InvalidInputError("Missing required parameter: feed_url")
    
    max_items = payload.get("max_items", 25)
    if not isinstance(max_items, int) or max_items < 1 or max_items > 100:
        raise InvalidInputError("max_items must be between 1 and 100")
    
    # Normalize and validate URL
    try:
        feed_url = normalize_url(feed_url)
        validate_url(feed_url)
        is_safe_url(feed_url)
    except InvalidInputError:
        raise
    
    # Fetch and parse feed
    raw_entries = fetch_and_parse_rss(feed_url)
    
    # Normalize entries to ToolItem format
    items = []
    warnings = []
    
    for entry in raw_entries[:max_items * 2]:  # Fetch extra to account for filtering
        try:
            # Extract URL
            url = entry.get("link")
            if not url or not isinstance(url, str) or not url.strip():
                warnings.append(f"Skipping entry without URL: {entry.get('title', 'unknown')}")
                continue
            
            # Normalize and validate URL
            try:
                url = normalize_url(url)
                validate_url(url)
                is_safe_url(url)
            except InvalidInputError as e:
                warnings.append(f"Skipping entry with invalid URL: {e.message}")
                continue
            
            # Extract title
            title = entry.get("title", "").strip()
            if not title:
                warnings.append(f"Skipping entry without title: {url}")
                continue
            
            # Extract and parse published date
            published_at = None
            for date_field in ["published", "updated", "created"]:
                date_str = entry.get(date_field)
                if date_str:
                    try:
                        dt = date_parser.parse(date_str)
                        published_at = dt.isoformat()
                        break
                    except Exception:
                        continue
            
            # Extract and clean snippet
            snippet = None
            for snippet_field in ["summary", "description"]:
                snippet_raw = entry.get(snippet_field)
                if snippet_raw:
                    snippet = clean_snippet(snippet_raw, max_length=500)
                    break
            
            # Check if entry has content field (list of dicts)
            if not snippet and entry.get("content"):
                content_list = entry.get("content", [])
                if content_list and isinstance(content_list, list) and len(content_list) > 0:
                    content_value = content_list[0].get("value")
                    if content_value:
                        snippet = clean_snippet(content_value, max_length=500)
            
            # Create ToolItem
            item = ToolItem(
                title=title,
                url=url,
                published_at=published_at,
                snippet=snippet,
                source=f"rss:{feed_url}",
                raw_id=entry.get("id"),
            )
            
            items.append(item)
            
            # Stop if we have enough items
            if len(items) >= max_items:
                break
                
        except Exception as e:
            warnings.append(f"Error processing entry: {str(e)}")
            continue
    
    return ToolResult(
        items=items,
        warnings=warnings,
    )
