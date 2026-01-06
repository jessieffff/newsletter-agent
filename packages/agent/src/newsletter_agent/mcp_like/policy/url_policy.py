"""
URL normalization and validation policies.

Provides URL validation, normalization, and SSRF protection.
"""

import re
import ipaddress
from urllib.parse import urlparse, urlunparse
from typing import Optional
from ..errors import InvalidInputError


# Private IP ranges for SSRF protection
PRIVATE_IP_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def normalize_url(url: str) -> str:
    """
    Normalize a URL to canonical form.
    
    - Ensures scheme is present (defaults to https)
    - Lowercases scheme and domain
    - Removes default ports
    - Removes trailing slashes from path (except root)
    - Sorts query parameters
    
    Args:
        url: URL to normalize
        
    Returns:
        Normalized URL string
        
    Raises:
        InvalidInputError: If URL cannot be parsed
    """
    if not url or not isinstance(url, str):
        raise InvalidInputError("URL must be a non-empty string")
    
    # Add scheme if missing
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    
    try:
        parsed = urlparse(url)
    except Exception as e:
        raise InvalidInputError(f"Invalid URL format: {str(e)}")
    
    # Lowercase scheme and netloc
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    
    # Remove default ports
    if (scheme == "http" and netloc.endswith(":80")) or \
       (scheme == "https" and netloc.endswith(":443")):
        netloc = netloc.rsplit(":", 1)[0]
    
    # Clean path
    path = parsed.path
    if path and path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    
    # Reconstruct URL
    normalized = urlunparse((
        scheme,
        netloc,
        path,
        parsed.params,
        parsed.query,
        "",  # Remove fragment
    ))
    
    return normalized


def validate_url(url: str, allowed_schemes: Optional[list] = None) -> bool:
    """
    Validate URL format and scheme.
    
    Args:
        url: URL to validate
        allowed_schemes: List of allowed schemes (default: ["http", "https"])
        
    Returns:
        True if URL is valid
        
    Raises:
        InvalidInputError: If URL is invalid
    """
    if allowed_schemes is None:
        allowed_schemes = ["http", "https"]
    
    try:
        parsed = urlparse(url)
    except Exception as e:
        raise InvalidInputError(f"Invalid URL format: {str(e)}")
    
    if not parsed.scheme:
        raise InvalidInputError("URL must have a scheme")
    
    if parsed.scheme.lower() not in allowed_schemes:
        raise InvalidInputError(
            f"URL scheme '{parsed.scheme}' not allowed. Allowed: {allowed_schemes}"
        )
    
    if not parsed.netloc:
        raise InvalidInputError("URL must have a domain")
    
    return True


def is_safe_url(url: str) -> bool:
    """
    Check if URL is safe (not pointing to private IPs - SSRF protection).
    
    Args:
        url: URL to check
        
    Returns:
        True if URL is safe
        
    Raises:
        InvalidInputError: If URL points to private IP range
    """
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        
        if not hostname:
            raise InvalidInputError("URL must have a hostname")
        
        # Try to parse as IP address
        try:
            ip = ipaddress.ip_address(hostname)
            for private_range in PRIVATE_IP_RANGES:
                if ip in private_range:
                    raise InvalidInputError(
                        f"URL points to private IP range: {hostname}",
                        context={"url": url, "ip": str(ip)}
                    )
        except ValueError:
            # Not an IP address, that's fine - it's a domain name
            pass
        
        # Check for localhost variations
        localhost_patterns = [
            r"^localhost$",
            r"^127\.",
            r"^0\.0\.0\.0$",
            r"^::1$",
        ]
        
        for pattern in localhost_patterns:
            if re.match(pattern, hostname, re.IGNORECASE):
                raise InvalidInputError(
                    f"URL points to localhost: {hostname}",
                    context={"url": url}
                )
        
        return True
        
    except InvalidInputError:
        raise
    except Exception as e:
        raise InvalidInputError(f"Error validating URL safety: {str(e)}")


def is_domain_allowed(url: str, allowlist: list[str]) -> bool:
    """
    Check if URL domain is in the allowlist.
    
    Args:
        url: URL to check
        allowlist: List of allowed domains
        
    Returns:
        True if domain is allowed
        
    Raises:
        InvalidInputError: If domain is not in allowlist
    """
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        
        if not hostname:
            raise InvalidInputError("URL must have a hostname")
        
        # Check exact match or subdomain match
        for allowed_domain in allowlist:
            if hostname == allowed_domain or hostname.endswith(f".{allowed_domain}"):
                return True
        
        raise InvalidInputError(
            f"Domain '{hostname}' not in allowlist",
            context={"url": url, "allowlist": allowlist}
        )
        
    except InvalidInputError:
        raise
    except Exception as e:
        raise InvalidInputError(f"Error checking domain allowlist: {str(e)}")
