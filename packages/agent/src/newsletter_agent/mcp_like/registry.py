"""
Tool registry for MCP-like infrastructure.
"""

from typing import Any, Callable, Dict, Optional, Type
from dataclasses import dataclass
from .types import ToolResult


@dataclass
class ToolMetadata:
    """Metadata about a registered tool."""
    name: str
    handler: Callable[[Dict[str, Any]], ToolResult]
    input_schema: Optional[Type] = None
    output_schema: Optional[Type] = None
    description: str = ""


# Global tool registry
_TOOL_REGISTRY: Dict[str, ToolMetadata] = {}


def register_tool(
    name: str,
    handler: Callable[[Dict[str, Any]], ToolResult],
    input_schema: Optional[Type] = None,
    output_schema: Optional[Type] = None,
    description: str = "",
) -> ToolMetadata:
    """
    Register a tool in the global registry.
    
    Args:
        name: Unique tool identifier
        handler: Function that implements the tool logic
        input_schema: Optional input validation schema
        output_schema: Optional output validation schema
        description: Human-readable tool description
        
    Returns:
        ToolMetadata for the registered tool
        
    Raises:
        ValueError: If tool name is already registered
    """
    if name in _TOOL_REGISTRY:
        raise ValueError(f"Tool '{name}' is already registered")
    
    metadata = ToolMetadata(
        name=name,
        handler=handler,
        input_schema=input_schema,
        output_schema=output_schema,
        description=description,
    )
    
    _TOOL_REGISTRY[name] = metadata
    return metadata


def get_tool(name: str) -> Optional[ToolMetadata]:
    """
    Get tool metadata by name.
    
    Args:
        name: Tool name to look up
        
    Returns:
        ToolMetadata if found, None otherwise
    """
    return _TOOL_REGISTRY.get(name)


def list_tools() -> Dict[str, ToolMetadata]:
    """
    List all registered tools.
    
    Returns:
        Dictionary mapping tool names to their metadata
    """
    return _TOOL_REGISTRY.copy()


def clear_registry() -> None:
    """Clear all registered tools (mainly for testing)."""
    _TOOL_REGISTRY.clear()
