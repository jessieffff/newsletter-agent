"""
Tool executor for MCP-like infrastructure.

Provides standardized tool invocation with validation and error handling.
"""

import time
from typing import Any, Dict
from .types import ToolResult, ToolError, ToolMeta
from .errors import ToolException, InvalidInputError
from .registry import get_tool


def invoke_tool(name: str, payload: Dict[str, Any]) -> ToolResult:
    """
    Invoke a registered tool with standardized error handling.
    
    Args:
        name: Tool name to invoke
        payload: Input parameters for the tool
        
    Returns:
        ToolResult with items, metadata, warnings, and errors
        
    Raises:
        ValueError: If tool is not found
    """
    # Look up tool in registry
    tool_metadata = get_tool(name)
    if tool_metadata is None:
        raise ValueError(f"Tool '{name}' is not registered")
    
    start_time = time.time()
    
    try:
        # Validate input if schema is provided
        if tool_metadata.input_schema is not None:
            try:
                # For dataclass schemas, validate by instantiation
                if hasattr(tool_metadata.input_schema, '__dataclass_fields__'):
                    tool_metadata.input_schema(**payload)
            except (TypeError, ValueError) as e:
                raise InvalidInputError(
                    f"Input validation failed: {str(e)}",
                    context={"payload": payload}
                )
        
        # Invoke the tool handler
        result = tool_metadata.handler(payload)
        
        # Validate output if schema is provided
        if tool_metadata.output_schema is not None:
            # Basic validation that result is a ToolResult
            if not isinstance(result, ToolResult):
                raise InvalidInputError(
                    f"Tool '{name}' returned invalid output type: {type(result)}",
                    context={"expected": "ToolResult"}
                )
        
        # Add execution metadata
        execution_time_ms = (time.time() - start_time) * 1000
        if result.meta is None:
            result.meta = ToolMeta(
                tool_name=name,
                execution_time_ms=execution_time_ms,
                item_count=len(result.items),
            )
        else:
            result.meta.execution_time_ms = execution_time_ms
            result.meta.item_count = len(result.items)
        
        return result
        
    except ToolException as e:
        # Convert known tool exceptions to error results
        execution_time_ms = (time.time() - start_time) * 1000
        
        error = ToolError(
            tool=name,
            code=e.code,
            message=e.message,
            retryable=e.retryable,
            context=e.context,
        )
        
        result = ToolResult(
            items=[],
            meta=ToolMeta(
                tool_name=name,
                execution_time_ms=execution_time_ms,
                item_count=0,
            ),
            errors=[error],
        )
        
        return result
        
    except Exception as e:
        # Convert unexpected exceptions to error results
        execution_time_ms = (time.time() - start_time) * 1000
        
        error = ToolError(
            tool=name,
            code="PROVIDER_ERROR",
            message=f"Unexpected error: {str(e)}",
            retryable=False,
            context={"exception_type": type(e).__name__},
        )
        
        result = ToolResult(
            items=[],
            meta=ToolMeta(
                tool_name=name,
                execution_time_ms=execution_time_ms,
                item_count=0,
            ),
            errors=[error],
        )
        
        return result
