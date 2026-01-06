"""
Unit tests for MCP-like infrastructure.
"""

import pytest
from newsletter_agent.mcp_like import (
    ToolResult,
    ToolItem,
    ToolError,
    InvalidInputError,
    register_tool,
    get_tool,
    invoke_tool,
    clear_registry,
)


@pytest.fixture(autouse=True)
def clean_registry():
    """Clear registry before and after each test."""
    from newsletter_agent.mcp_like.registry import clear_registry
    clear_registry()
    yield
    clear_registry()


def test_tool_item_creation():
    """Test creating a ToolItem."""
    item = ToolItem(
        title="Test Article",
        url="https://example.com/article",
        published_at="2025-01-01T00:00:00Z",
        snippet="Test snippet",
        source="test",
        raw_id="123",
    )
    
    assert item.title == "Test Article"
    assert item.url == "https://example.com/article"
    assert item.published_at == "2025-01-01T00:00:00Z"
    assert item.snippet == "Test snippet"
    assert item.source == "test"
    assert item.raw_id == "123"


def test_tool_result_creation():
    """Test creating a ToolResult."""
    item = ToolItem(title="Test", url="https://example.com")
    result = ToolResult(items=[item])
    
    assert len(result.items) == 1
    assert result.items[0].title == "Test"
    assert result.is_success is True
    assert result.is_partial_success is False


def test_tool_result_with_errors():
    """Test ToolResult with errors."""
    error = ToolError(
        tool="test_tool",
        code="FETCH_FAILED",
        message="Test error",
        retryable=True,
    )
    
    result = ToolResult(errors=[error])
    
    assert len(result.errors) == 1
    assert result.is_success is False
    assert result.is_partial_success is False


def test_tool_result_partial_success():
    """Test ToolResult with both items and errors."""
    item = ToolItem(title="Test", url="https://example.com")
    error = ToolError(
        tool="test_tool",
        code="FETCH_FAILED",
        message="Partial failure",
        retryable=True,
    )
    
    result = ToolResult(items=[item], errors=[error])
    
    assert result.is_success is False
    assert result.is_partial_success is True


def test_register_tool():
    """Test tool registration."""
    def dummy_handler(payload):
        return ToolResult()
    
    metadata = register_tool(
        name="test_tool",
        handler=dummy_handler,
        description="Test tool",
    )
    
    assert metadata.name == "test_tool"
    assert metadata.handler == dummy_handler
    assert metadata.description == "Test tool"


def test_register_duplicate_tool():
    """Test that registering duplicate tool raises error."""
    def dummy_handler(payload):
        return ToolResult()
    
    register_tool("test_tool", dummy_handler)
    
    with pytest.raises(ValueError, match="already registered"):
        register_tool("test_tool", dummy_handler)


def test_get_tool():
    """Test getting tool from registry."""
    def dummy_handler(payload):
        return ToolResult()
    
    register_tool("test_tool", dummy_handler)
    
    metadata = get_tool("test_tool")
    assert metadata is not None
    assert metadata.name == "test_tool"
    
    # Test getting non-existent tool
    assert get_tool("nonexistent") is None


def test_invoke_tool():
    """Test invoking a registered tool."""
    def dummy_handler(payload):
        name = payload.get("name", "Unknown")
        item = ToolItem(title=f"Hello {name}", url="https://example.com")
        return ToolResult(items=[item])
    
    register_tool("test_tool", dummy_handler)
    
    result = invoke_tool("test_tool", {"name": "World"})
    
    assert len(result.items) == 1
    assert result.items[0].title == "Hello World"
    assert result.meta is not None
    assert result.meta.tool_name == "test_tool"
    assert result.meta.item_count == 1


def test_invoke_nonexistent_tool():
    """Test invoking a tool that doesn't exist."""
    with pytest.raises(ValueError, match="not registered"):
        invoke_tool("nonexistent_tool", {})


def test_invoke_tool_with_exception():
    """Test invoking a tool that raises an exception."""
    def failing_handler(payload):
        raise InvalidInputError("Test error")
    
    register_tool("failing_tool", failing_handler)
    
    result = invoke_tool("failing_tool", {})
    
    assert len(result.items) == 0
    assert len(result.errors) == 1
    assert result.errors[0].code == "INVALID_INPUT"
    assert result.errors[0].message == "Test error"
    assert result.errors[0].retryable is False


def test_invoke_tool_with_unexpected_exception():
    """Test invoking a tool that raises an unexpected exception."""
    def failing_handler(payload):
        raise RuntimeError("Unexpected error")
    
    register_tool("failing_tool", failing_handler)
    
    result = invoke_tool("failing_tool", {})
    
    assert len(result.items) == 0
    assert len(result.errors) == 1
    assert result.errors[0].code == "PROVIDER_ERROR"
    assert "Unexpected error" in result.errors[0].message


def test_tool_result_serialization():
    """Test ToolResult serialization to dict."""
    item = ToolItem(
        title="Test",
        url="https://example.com",
        snippet="Test snippet",
        source="test",
    )
    
    error = ToolError(
        tool="test_tool",
        code="TEST_ERROR",
        message="Test error",
        retryable=False,
    )
    
    result = ToolResult(
        items=[item],
        warnings=["Warning 1"],
        errors=[error],
    )
    
    data = result.to_dict()
    
    assert "items" in data
    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == "Test"
    assert data["items"][0]["url"] == "https://example.com"
    
    assert "warnings" in data
    assert len(data["warnings"]) == 1
    
    assert "errors" in data
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == "TEST_ERROR"
