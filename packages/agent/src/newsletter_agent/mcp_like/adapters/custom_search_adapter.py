"""
Custom domain search adapter.

Searches within specified domains using Foundry grounding.
"""

from typing import Dict, Any
from ..types import ToolResult, ToolItem
from ..errors import InvalidInputError
from ..policy import is_domain_allowed


def search_web_custom_domains(payload: Dict[str, Any]) -> ToolResult:
    """
    Search within custom domains.
    
    Args:
        payload: Input parameters
            - query (str): Search query
            - domains (list[str]): List of allowed domains
            - max_results (int, optional): Maximum results (default: 10)
            
    Returns:
        ToolResult with search results
    """
    # Validate and extract input
    query = payload.get("query")
    if not query or not isinstance(query, str) or not query.strip():
        raise InvalidInputError("Missing or invalid parameter: query")
    
    domains = payload.get("domains")
    if not domains or not isinstance(domains, list) or len(domains) == 0:
        raise InvalidInputError("Missing or invalid parameter: domains (must be non-empty list)")
    
    # Validate domains
    for domain in domains:
        if not isinstance(domain, str) or not domain.strip():
            raise InvalidInputError(f"Invalid domain in list: {domain}")
    
    max_results = payload.get("max_results", 10)
    if not isinstance(max_results, int) or max_results < 1 or max_results > 50:
        raise InvalidInputError("max_results must be between 1 and 50")
    
    # Build site-restricted query
    # Example: "query site:example.com OR site:another.com"
    site_operators = " OR ".join([f"site:{domain}" for domain in domains])
    custom_query = f"{query} {site_operators}"
    
    # Import and call Foundry grounding
    from ...tools.foundry_grounding import grounded_search_via_foundry
    
    try:
        # Call existing Foundry grounding service
        from ...types import Candidate
        
        candidates = grounded_search_via_foundry(
            query=custom_query,
            freshness="30d",  # 30 days for custom domain search
            count=max_results
        )
        
        # Filter results to ensure they're from allowed domains
        # (in case Foundry returns results from other domains)
        filtered_candidates = []
        warnings = []
        
        for candidate in candidates:
            url = str(candidate.url)
            
            # Check if URL is from allowed domains
            try:
                from urllib.parse import urlparse
                hostname = urlparse(url).hostname or ""
                
                is_allowed = False
                for domain in domains:
                    if hostname == domain or hostname.endswith(f".{domain}"):
                        is_allowed = True
                        break
                
                if is_allowed:
                    filtered_candidates.append(candidate)
                else:
                    warnings.append(f"Filtered out result from non-allowed domain: {hostname}")
                    
            except Exception as e:
                warnings.append(f"Error checking domain for URL {url}: {str(e)}")
                continue
        
        # Convert Candidates to ToolItems
        items = []
        for candidate in filtered_candidates:
            item = ToolItem(
                title=candidate.title,
                url=str(candidate.url),
                published_at=candidate.published_at,
                snippet=candidate.snippet,
                source=f"web:custom:{','.join(domains[:3])}",  # Indicate custom domain search
                raw_id=candidate.id,
            )
            items.append(item)
        
        return ToolResult(items=items, warnings=warnings)
        
    except Exception as e:
        # Let the executor handle the error
        raise
