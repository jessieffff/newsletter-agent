from __future__ import annotations
import hashlib
import feedparser
from typing import List, Optional, Dict
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from ..types import Candidate

def _stable_id(url: str) -> str:
    """Generate a stable ID from a URL using SHA-256 hash."""
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]

def _canonicalize_url(url: str) -> str:
    """
    Extract canonical URL by removing common tracking parameters.
    Keeps the core URL for deduplication purposes.
    """
    try:
        parsed = urlparse(url)
        
        # Common tracking parameters to remove
        tracking_params = {
            'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
            'fbclid', 'gclid', 'msclkid', 'mc_cid', 'mc_eid',
            'ref', 'source', '_hsenc', '_hsmi', 'mkt_tok'
        }
        
        # Parse query string and filter out tracking params
        query_params = parse_qs(parsed.query, keep_blank_values=False)
        cleaned_params = {
            k: v for k, v in query_params.items() 
            if k.lower() not in tracking_params
        }
        
        # Reconstruct query string
        new_query = urlencode(cleaned_params, doseq=True) if cleaned_params else ''
        
        # Reconstruct URL without fragment and with cleaned query
        canonical = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path.rstrip('/') or '/',  # Normalize trailing slash
            parsed.params,
            new_query,
            ''  # Remove fragment
        ))
        
        return canonical
    except Exception:
        # If canonicalization fails, return original URL
        return url

def _deduplicate_candidates(candidates: List[Candidate]) -> List[Candidate]:
    """
    Deduplicate candidates by canonical URL.
    Keeps the most recent entry when duplicates are found.
    """
    seen: Dict[str, Candidate] = {}
    
    for candidate in candidates:
        canonical = _canonicalize_url(str(candidate.url))
        
        # Keep if not seen, or if this one is more recent
        if canonical not in seen:
            seen[canonical] = candidate
        else:
            # Compare published_at dates if available
            existing = seen[canonical]
            if candidate.published_at and existing.published_at:
                if candidate.published_at > existing.published_at:
                    seen[canonical] = candidate
            elif candidate.published_at and not existing.published_at:
                # Prefer entries with publication dates
                seen[canonical] = candidate
    
    return list(seen.values())

def fetch_rss(feed_url: str, topic_hint: Optional[str] = None, limit: int = 25) -> List[Candidate]:
    """
    Fetch and normalize RSS feed items.
    
    Args:
        feed_url: RSS feed URL to fetch
        topic_hint: Optional topic tag to add to all items
        limit: Maximum number of items to fetch
    
    Returns:
        List of deduplicated Candidate objects with normalized schema
    """
    try:
        feed = feedparser.parse(feed_url)
        
        # Check if feed was successfully parsed
        if hasattr(feed, 'bozo') and feed.bozo:
            # Feed has issues, but we'll try to continue with what we got
            if not hasattr(feed, 'entries') or not feed.entries:
                # Feed is completely broken
                return []
        
        out: List[Candidate] = []
        
        # Get source name from feed or fallback to "rss"
        source_name = "rss"
        if hasattr(feed, 'feed'):
            source_name = (feed.feed.get("title") or "rss").strip()
        
        for entry in (feed.entries or [])[:limit * 2]:  # Fetch extra to account for deduplication
            try:
                # Skip entries without URLs
                url = entry.get("link")
                if not url or not url.strip():
                    continue
                
                # Skip entries without titles
                title = (entry.get("title") or "").strip()
                if not title:
                    continue
                
                # Get published date (try multiple fields)
                published_at = (
                    entry.get("published") or 
                    entry.get("updated") or 
                    entry.get("created")
                )
                
                # Get snippet/description
                snippet = (
                    entry.get("summary") or 
                    entry.get("description") or 
                    entry.get("content", [{}])[0].get("value") if entry.get("content") else None
                )
                
                # Clean snippet if exists
                if snippet:
                    snippet = snippet.strip()
                
                out.append(Candidate(
                    id=_stable_id(url),
                    title=title,
                    url=url,
                    source=source_name,
                    published_at=published_at,
                    author=entry.get("author"),
                    snippet=snippet,
                    topic_tags=[topic_hint] if topic_hint else [],
                    raw={"feed_url": feed_url},
                ))
            except Exception:
                # Skip individual malformed entries but continue processing
                continue
        
        # Deduplicate and apply limit
        deduplicated = _deduplicate_candidates(out)
        return deduplicated[:limit]
        
    except Exception:
        # Handle completely failed feed fetches gracefully
        return []
