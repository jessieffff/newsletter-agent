"""
Standard types for MCP-like tool infrastructure.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ToolItem:
    """
    Standardized item shape returned by all tools.
    
    Attributes:
        title: Item title/headline
        url: Canonical, validated URL
        published_at: ISO8601 datetime or None
        snippet: Brief description or None
        source: Tool/source identifier (e.g., "rss:feed_url", "web:bing", "nyt", "x")
        raw_id: Original item ID from provider, if available
    """
    title: str
    url: str
    published_at: Optional[str] = None
    snippet: Optional[str] = None
    source: str = ""
    raw_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "title": self.title,
            "url": self.url,
            "published_at": self.published_at,
            "snippet": self.snippet,
            "source": self.source,
            "raw_id": self.raw_id,
        }


@dataclass
class ToolMeta:
    """
    Metadata about tool execution.
    
    Attributes:
        tool_name: Name of the tool that was invoked
        execution_time_ms: Time taken to execute in milliseconds
        item_count: Number of items returned
        provider_metadata: Additional provider-specific metadata
    """
    tool_name: str
    execution_time_ms: float = 0.0
    item_count: int = 0
    provider_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "tool_name": self.tool_name,
            "execution_time_ms": self.execution_time_ms,
            "item_count": self.item_count,
            "provider_metadata": self.provider_metadata,
        }


@dataclass
class ToolError:
    """
    Standard error shape for tool failures.
    
    Attributes:
        tool: Tool name that produced the error
        code: Error classification code
        message: Human-readable error message
        retryable: Whether the error is retryable
        context: Additional error context
    """
    tool: str
    code: str
    message: str
    retryable: bool = False
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "tool": self.tool,
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
            "context": self.context,
        }


@dataclass
class ToolResult:
    """
    Common result shape returned by all tools.
    
    Attributes:
        items: List of standardized items
        meta: Execution metadata
        warnings: Non-fatal issues encountered
        errors: Partial errors (tool may still return some items)
    """
    items: List[ToolItem] = field(default_factory=list)
    meta: Optional[ToolMeta] = None
    warnings: List[str] = field(default_factory=list)
    errors: List[ToolError] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "items": [item.to_dict() for item in self.items],
            "meta": self.meta.to_dict() if self.meta else None,
            "warnings": self.warnings,
            "errors": [error.to_dict() for error in self.errors],
        }
    
    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)
    
    def add_error(self, error: ToolError) -> None:
        """Add an error."""
        self.errors.append(error)
    
    @property
    def is_success(self) -> bool:
        """Check if the tool execution was successful (has items and no fatal errors)."""
        return len(self.items) > 0 and len(self.errors) == 0
    
    @property
    def is_partial_success(self) -> bool:
        """Check if the tool execution was partially successful (has items but also errors)."""
        return len(self.items) > 0 and len(self.errors) > 0
