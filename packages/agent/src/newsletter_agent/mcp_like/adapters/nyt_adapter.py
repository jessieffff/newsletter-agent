"""
NYT API adapter.

Fetches NYT articles and normalizes to standard ToolResult shape.
"""

from typing import Dict, Any
from ..types import ToolResult, ToolItem
from ..errors import InvalidInputError


def fetch_nyt_items(payload: Dict[str, Any]) -> ToolResult:
    """
    Fetch items from NYT Article Search API.
    
    Args:
        payload: Input parameters
            - query (str): Search query
            - api_key (str): NYT API key
            - max_results (int, optional): Maximum results (default: 20)
            - begin_date (str, optional): Begin date in YYYYMMDD format
            - end_date (str, optional): End date in YYYYMMDD format
            
    Returns:
        ToolResult with NYT articles
    """
    # Validate and extract input
    query = payload.get("query")
    if not query or not isinstance(query, str) or not query.strip():
        raise InvalidInputError("Missing or invalid parameter: query")
    
    api_key = payload.get("api_key")
    if not api_key or not isinstance(api_key, str):
        raise InvalidInputError("Missing or invalid parameter: api_key")
    
    max_results = payload.get("max_results", 20)
    if not isinstance(max_results, int) or max_results < 1 or max_results > 50:
        raise InvalidInputError("max_results must be between 1 and 50")
    
    # Optional date filters
    begin_date = payload.get("begin_date")
    end_date = payload.get("end_date")
    
    # Import and call NYT fetcher
    from ...tools.nyt import fetch_nyt
    
    try:
        # Call existing NYT fetcher
        # Note: fetch_nyt is async, but we're in sync context
        # We need to handle this properly
        import asyncio
        
        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run the async function
        candidates = loop.run_until_complete(
            fetch_nyt(query, api_key, limit=max_results)
        )
        
        # Convert Candidates to ToolItems
        items = []
        for candidate in candidates:
            item = ToolItem(
                title=candidate.title,
                url=str(candidate.url),
                published_at=candidate.published_at,
                snippet=candidate.snippet,
                source="nyt",
                raw_id=candidate.id,
            )
            items.append(item)
        
        return ToolResult(items=items)
        
    except Exception as e:
        # Let the executor handle the error
        raise
