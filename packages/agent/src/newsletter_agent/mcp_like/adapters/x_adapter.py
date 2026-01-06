"""
X (Twitter) API adapter.

Fetches X/Twitter posts and normalizes to standard ToolResult shape.
"""

from typing import Dict, Any
from ..types import ToolResult, ToolItem
from ..errors import InvalidInputError


def fetch_x_items(payload: Dict[str, Any]) -> ToolResult:
    """
    Fetch items from X (Twitter) API.
    
    Args:
        payload: Input parameters
            - query (str): Search query
            - bearer_token (str): X API bearer token
            - max_results (int, optional): Maximum results (default: 20)
            - start_time (str, optional): Start time in ISO 8601 format
            - end_time (str, optional): End time in ISO 8601 format
            
    Returns:
        ToolResult with tweets
    """
    # Validate and extract input
    query = payload.get("query")
    if not query or not isinstance(query, str) or not query.strip():
        raise InvalidInputError("Missing or invalid parameter: query")
    
    bearer_token = payload.get("bearer_token")
    if not bearer_token or not isinstance(bearer_token, str):
        raise InvalidInputError("Missing or invalid parameter: bearer_token")
    
    max_results = payload.get("max_results", 20)
    if not isinstance(max_results, int) or max_results < 1 or max_results > 100:
        raise InvalidInputError("max_results must be between 1 and 100")
    
    # Optional time filters
    start_time = payload.get("start_time")
    end_time = payload.get("end_time")
    
    # Import and call X fetcher
    from ...tools.x_twitter import fetch_x_recent
    
    try:
        # Call existing X fetcher
        # Note: fetch_x_recent is async, but we're in sync context
        import asyncio
        
        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run the async function
        candidates = loop.run_until_complete(
            fetch_x_recent(query, bearer_token, limit=max_results)
        )
        
        # Convert Candidates to ToolItems
        items = []
        for candidate in candidates:
            item = ToolItem(
                title=candidate.title,
                url=str(candidate.url),
                published_at=candidate.published_at,
                snippet=candidate.snippet,
                source="x",
                raw_id=candidate.id,
            )
            items.append(item)
        
        return ToolResult(items=items)
        
    except Exception as e:
        # Let the executor handle the error
        raise
