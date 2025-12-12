"""Configuration module for newsletter agent security settings."""

from typing import List
from datetime import datetime, timedelta

# Allow-list of RSS feed domains
# Only feeds from these domains will be fetched
ALLOWED_RSS_DOMAINS: List[str] = [
    "techcrunch.com",
    "theverge.com",
    "arstechnica.com",
    "wired.com",
    "engadget.com",
    "cnet.com",
    "zdnet.com",
    "reuters.com",
    "bbc.co.uk",
    "cnn.com",
    "nytimes.com",
    "wsj.com",
    "bloomberg.com",
    "ft.com",
    "economist.com",
    "forbes.com",
    "medium.com",
    "dev.to",
    "hackernoon.com",
    "smashingmagazine.com",
    # Add more trusted domains as needed
]

# Content sanity check limits
MAX_TITLE_LENGTH = 500
MAX_DESCRIPTION_LENGTH = 5000
MAX_ARTICLE_AGE_DAYS = 90  # Articles older than this are considered stale
MIN_ARTICLE_AGE_DAYS = -7  # Articles with future dates beyond this are suspicious

# Spam detection patterns (simple keyword-based)
SPAM_KEYWORDS = [
    "click here now",
    "act now",
    "limited time offer",
    "buy now",
    "free money",
    "you won",
    "congratulations you",
]

def is_domain_allowed(domain: str) -> bool:
    """
    Check if a domain is in the allow-list.
    Supports both exact matches and subdomain matches.
    
    Args:
        domain: The domain to check (e.g., "blog.techcrunch.com")
    
    Returns:
        True if the domain or its parent domain is allowed, False otherwise
    """
    domain_lower = domain.lower().strip()
    
    # Check exact match
    if domain_lower in ALLOWED_RSS_DOMAINS:
        return True
    
    # Check if any allowed domain is a suffix (for subdomains)
    for allowed in ALLOWED_RSS_DOMAINS:
        if domain_lower.endswith("." + allowed):
            return True
    
    return False

def is_candidate_reasonable(candidate) -> bool:
    """
    Check if a candidate article passes basic sanity checks.
    
    Args:
        candidate: A Candidate object to validate
    
    Returns:
        True if the candidate is reasonable, False otherwise
    """
    # Check title length
    if len(candidate.title) > MAX_TITLE_LENGTH:
        return False
    
    # Check description/snippet length
    if candidate.snippet and len(candidate.snippet) > MAX_DESCRIPTION_LENGTH:
        return False
    
    # Check publication date if available
    if candidate.published_at:
        try:
            # Parse ISO8601 string
            pub_date = datetime.fromisoformat(candidate.published_at.replace('Z', '+00:00'))
            now = datetime.now(pub_date.tzinfo) if pub_date.tzinfo else datetime.now()
            age_days = (now - pub_date).days
            
            # Check if article is too old
            if age_days > MAX_ARTICLE_AGE_DAYS:
                return False
            
            # Check if article has suspicious future date
            if age_days < MIN_ARTICLE_AGE_DAYS:
                return False
        except (ValueError, AttributeError):
            # If date parsing fails, skip date check
            pass
    
    # Check for obvious spam patterns in title
    title_lower = candidate.title.lower()
    for spam_keyword in SPAM_KEYWORDS:
        if spam_keyword in title_lower:
            return False
    
    return True

