"""
MCP-like internal infrastructure for the newsletter agent.

Provides standardized tool invocation, registry, and error handling.
"""

from .types import ToolResult, ToolItem, ToolMeta, ToolError
from .errors import (
    ToolException,
    InvalidInputError,
    FetchFailedError,
    TimeoutError,
    ParseFailedError,
    RateLimitedError,
    AuthFailedError,
    ProviderError,
)
from .registry import register_tool, get_tool, list_tools
from .executor import invoke_tool
from .bootstrap import register_all_tools

__all__ = [
    "ToolResult",
    "ToolItem",
    "ToolMeta",
    "ToolError",
    "ToolException",
    "InvalidInputError",
    "FetchFailedError",
    "TimeoutError",
    "ParseFailedError",
    "RateLimitedError",
    "AuthFailedError",
    "ProviderError",
    "register_tool",
    "get_tool",
    "list_tools",
    "invoke_tool",
    "register_all_tools",
]
