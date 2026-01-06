"""
Rate limiting policies.
"""

import time
from typing import Dict, Optional
from collections import defaultdict
from ..errors import RateLimitedError


class RateLimiter:
    """
    Simple token bucket rate limiter.
    
    Tracks requests per key (e.g., tool name, API endpoint).
    """
    
    def __init__(self, requests_per_minute: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum requests allowed per minute per key
        """
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = defaultdict(list)
    
    def check_limit(self, key: str) -> bool:
        """
        Check if request is within rate limit.
        
        Args:
            key: Rate limit key (e.g., tool name)
            
        Returns:
            True if within limit
            
        Raises:
            RateLimitedError: If rate limit exceeded
        """
        now = time.time()
        window_start = now - 60  # 1 minute window
        
        # Remove old requests outside the window
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if req_time > window_start
        ]
        
        # Check if limit exceeded
        if len(self.requests[key]) >= self.requests_per_minute:
            raise RateLimitedError(
                f"Rate limit exceeded for '{key}': {self.requests_per_minute} requests per minute",
                context={
                    "key": key,
                    "limit": self.requests_per_minute,
                    "current_count": len(self.requests[key]),
                }
            )
        
        # Add current request
        self.requests[key].append(now)
        return True
    
    def reset(self, key: Optional[str] = None) -> None:
        """
        Reset rate limit counters.
        
        Args:
            key: Optional key to reset. If None, resets all keys.
        """
        if key is None:
            self.requests.clear()
        else:
            self.requests.pop(key, None)


# Global rate limiter instance
_global_rate_limiter = RateLimiter()


def check_rate_limit(key: str, limiter: Optional[RateLimiter] = None) -> bool:
    """
    Check rate limit for a key.
    
    Args:
        key: Rate limit key
        limiter: Optional custom rate limiter (uses global if not provided)
        
    Returns:
        True if within limit
        
    Raises:
        RateLimitedError: If rate limit exceeded
    """
    if limiter is None:
        limiter = _global_rate_limiter
    
    return limiter.check_limit(key)
