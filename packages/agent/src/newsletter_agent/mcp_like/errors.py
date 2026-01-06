"""
Standard error types for MCP-like tool infrastructure.
"""

from typing import Any, Dict, Optional


class ToolException(Exception):
    """Base exception for all tool errors."""
    
    def __init__(
        self,
        message: str,
        code: str,
        retryable: bool = False,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.retryable = retryable
        self.context = context or {}


class InvalidInputError(ToolException):
    """Raised when tool input validation fails."""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="INVALID_INPUT",
            retryable=False,
            context=context,
        )


class FetchFailedError(ToolException):
    """Raised when fetching data from provider fails."""
    
    def __init__(
        self,
        message: str,
        retryable: bool = True,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="FETCH_FAILED",
            retryable=retryable,
            context=context,
        )


class TimeoutError(ToolException):
    """Raised when a tool operation times out."""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="TIMEOUT",
            retryable=True,
            context=context,
        )


class ParseFailedError(ToolException):
    """Raised when parsing provider response fails."""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="PARSE_FAILED",
            retryable=False,
            context=context,
        )


class RateLimitedError(ToolException):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="RATE_LIMITED",
            retryable=True,
            context=context,
        )


class AuthFailedError(ToolException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="AUTH_FAILED",
            retryable=False,
            context=context,
        )


class ProviderError(ToolException):
    """Raised when provider returns an error."""
    
    def __init__(
        self,
        message: str,
        retryable: bool = False,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="PROVIDER_ERROR",
            retryable=retryable,
            context=context,
        )
