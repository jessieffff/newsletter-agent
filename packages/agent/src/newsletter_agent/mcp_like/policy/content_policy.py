"""
Content sanitization and processing policies.
"""

import re
from html import unescape
from typing import Optional


def sanitize_html(text: str) -> str:
    """
    Remove HTML tags and decode entities.
    
    Args:
        text: HTML text to sanitize
        
    Returns:
        Plain text with HTML removed
    """
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Decode HTML entities
    text = unescape(text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def truncate_text(text: str, max_length: int = 500, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length (including suffix)
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    # Truncate at word boundary if possible
    truncate_at = max_length - len(suffix)
    
    # Find last space before truncate point
    last_space = text.rfind(' ', 0, truncate_at)
    
    if last_space > 0 and last_space > truncate_at * 0.8:
        # Truncate at word boundary if it's not too far back
        return text[:last_space] + suffix
    else:
        # Truncate at exact position
        return text[:truncate_at] + suffix


def clean_snippet(text: Optional[str], max_length: int = 500) -> Optional[str]:
    """
    Clean and truncate a snippet.
    
    Combines HTML sanitization and truncation.
    
    Args:
        text: Snippet text (may contain HTML)
        max_length: Maximum length
        
    Returns:
        Cleaned and truncated snippet, or None if input is None/empty
    """
    if not text:
        return None
    
    # Sanitize HTML
    cleaned = sanitize_html(text)
    
    if not cleaned:
        return None
    
    # Truncate
    return truncate_text(cleaned, max_length)
