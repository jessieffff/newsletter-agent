"""
RSS feed connector.

Low-level RSS fetching and parsing.
"""

import feedparser
from typing import Dict, Any, List, Optional
from ..errors import FetchFailedError, ParseFailedError


def fetch_and_parse_rss(feed_url: str) -> List[Dict[str, Any]]:
    """
    Fetch and parse RSS/Atom feed.
    
    Args:
        feed_url: URL of the RSS/Atom feed
        
    Returns:
        List of raw feed entries (dicts)
        
    Raises:
        FetchFailedError: If feed cannot be fetched
        ParseFailedError: If feed cannot be parsed
    """
    try:
        feed = feedparser.parse(feed_url)
        
        # Check for parsing errors
        if hasattr(feed, 'bozo') and feed.bozo:
            if hasattr(feed, 'bozo_exception'):
                raise ParseFailedError(
                    f"Feed parsing error: {str(feed.bozo_exception)}",
                    context={"feed_url": feed_url}
                )
        
        # Check if feed has entries
        if not hasattr(feed, 'entries') or not feed.entries:
            raise ParseFailedError(
                "Feed has no entries",
                context={"feed_url": feed_url}
            )
        
        # Return raw entries
        return [dict(entry) for entry in feed.entries]
        
    except ParseFailedError:
        raise
    except Exception as e:
        raise FetchFailedError(
            f"Failed to fetch RSS feed: {str(e)}",
            context={"feed_url": feed_url}
        )
