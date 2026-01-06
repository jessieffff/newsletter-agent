"""
Web search adapter for fresh results.

Uses Foundry grounding service for web search.
"""

from typing import Dict, Any
from ..types import ToolResult, ToolItem
from ..errors import InvalidInputError


def search_web_fresh(payload: Dict[str, Any]) -> ToolResult:
    """
    Search the web for fresh results.
    
    Args:
        payload: Input parameters
            - query (str): Search query
            - max_results (int, optional): Maximum results (default: 10)
            - freshness (str, optional): Freshness filter - "day", "week", "month" (default: "week")
            
    Returns:
        ToolResult with search results
    """
    # Validate and extract input
    query = payload.get("query")
    if not query or not isinstance(query, str) or not query.strip():
        raise InvalidInputError("Missing or invalid parameter: query")
    
    max_results = payload.get("max_results", 10)
    if not isinstance(max_results, int) or max_results < 1 or max_results > 50:
        raise InvalidInputError("max_results must be between 1 and 50")
    
    freshness = payload.get("freshness", "week")
    if freshness not in ["day", "week", "month"]:
        raise InvalidInputError("freshness must be one of: day, week, month")
    
    # Map freshness to Foundry format
    freshness_map = {
        "day": "1d",
        "week": "7d",
        "month": "30d",
    }
    foundry_freshness = freshness_map.get(freshness, "7d")
    
    # Import and call Foundry grounding
    from ...tools.foundry_grounding import grounded_search_via_foundry
    
    try:
        # Call existing Foundry grounding service
        # Note: This returns Candidate objects, we need to convert to ToolItems
        from ...types import Candidate
        
        candidates = grounded_search_via_foundry(
            query=query,
            freshness=foundry_freshness,
            count=max_results
        )
        
        # Convert Candidates to ToolItems
        items = []
        for candidate in candidates:
            item = ToolItem(
                title=candidate.title,
                url=str(candidate.url),
                published_at=candidate.published_at,
                snippet=candidate.snippet,
                source="web:bing",
                raw_id=candidate.id,
            )
            items.append(item)
        
        return ToolResult(items=items)
        
    except Exception as e:
        # Let the executor handle the error
        raise
