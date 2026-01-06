# MCP-like Internal Infrastructure

This directory contains the MCP-like internal infrastructure for the newsletter agent. It provides standardized tool invocation, error handling, and integration with external services.

## Architecture

The MCP-like infrastructure consists of several layers:

```
┌─────────────────────────────────────┐
│         Graph Nodes                 │
│  (gather_candidates, rank, etc.)    │
└──────────────┬──────────────────────┘
               │
               │ invoke_tool()
               ▼
┌─────────────────────────────────────┐
│         Executor                    │
│  - Input validation                 │
│  - Error handling                   │
│  - Metadata tracking                │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│         Adapters                    │
│  - fetch_rss_items                  │
│  - search_web_fresh                 │
│  - search_web_custom_domains        │
│  - fetch_nyt_items                  │
│  - fetch_x_items                    │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│         Connectors                  │
│  - RSS fetching                     │
│  - Foundry grounding                │
│  - NYT API                          │
│  - X API                            │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│      External Services              │
└─────────────────────────────────────┘
```

## Components

### Types (`types.py`)

Defines standard data structures:

- **ToolItem**: Normalized item returned by all tools
  - title, url, published_at, snippet, source, raw_id

- **ToolResult**: Standard result shape
  - items: List of ToolItems
  - meta: Execution metadata
  - warnings: Non-fatal issues
  - errors: Partial errors

- **ToolError**: Standard error shape
  - tool, code, message, retryable, context

### Errors (`errors.py`)

Standard exception hierarchy:

- `ToolException` (base)
  - `InvalidInputError`
  - `FetchFailedError`
  - `TimeoutError`
  - `ParseFailedError`
  - `RateLimitedError`
  - `AuthFailedError`
  - `ProviderError`

### Registry (`registry.py`)

Global tool registry for managing available tools:

```python
register_tool(name, handler, input_schema, output_schema, description)
get_tool(name)
list_tools()
```

### Executor (`executor.py`)

Standardized tool invocation:

```python
result = invoke_tool("fetch_rss_items", {
    "feed_url": "https://example.com/feed",
    "max_items": 25
})
```

Features:
- Input validation
- Output validation
- Error handling and conversion
- Execution timing
- Metadata injection

### Adapters

Normalize external API responses to standard ToolResult shape:

- **rss_adapter.py**: Fetch and normalize RSS/Atom feeds
- **web_search_adapter.py**: Web search via Foundry grounding
- **custom_search_adapter.py**: Domain-restricted search
- **nyt_adapter.py**: NYT Article Search API
- **x_adapter.py**: X (Twitter) API

### Connectors

Low-level network calls to external services:

- **rss_connector.py**: RSS/Atom fetching and parsing
- **web_search_connector.py**: Foundry grounding service
- **nyt_connector.py**: NYT API client
- **x_connector.py**: X API client

### Policy Modules

Common validation and security:

- **url_policy.py**: URL normalization, validation, SSRF protection
- **rate_limit.py**: Rate limiting
- **content_policy.py**: HTML sanitization, text truncation

## Usage

### 1. Register Tools (at startup)

```python
from newsletter_agent.mcp_like import register_all_tools

# Register all available tools
register_all_tools()
```

### 2. Invoke Tools

```python
from newsletter_agent.mcp_like import invoke_tool

# Fetch RSS items
result = invoke_tool("fetch_rss_items", {
    "feed_url": "https://example.com/feed",
    "max_items": 25
})

# Check results
if result.is_success:
    for item in result.items:
        print(f"{item.title}: {item.url}")
else:
    for error in result.errors:
        print(f"Error: {error.message}")
```

### 3. Handle Results

```python
# Full success
if result.is_success:
    # All items, no errors
    pass

# Partial success
if result.is_partial_success:
    # Some items, some errors
    # Process what we got
    pass

# Complete failure
if not result.is_success and not result.is_partial_success:
    # No items, only errors
    pass

# Check warnings
for warning in result.warnings:
    logger.warning(warning)

# Check errors
for error in result.errors:
    if error.retryable:
        # Consider retrying
        pass
```

## Tool Specifications

### fetch_rss_items

Fetch items from RSS/Atom feed.

**Input:**
```python
{
    "feed_url": str,      # Required: RSS feed URL
    "max_items": int,     # Optional: Max items (default: 25, max: 100)
}
```

**Output:** ToolResult with ToolItems

**Features:**
- URL validation and SSRF protection
- HTML sanitization
- Date parsing
- Deduplication via URL normalization

### search_web_fresh

Search web for fresh results.

**Input:**
```python
{
    "query": str,         # Required: Search query
    "max_results": int,   # Optional: Max results (default: 10, max: 50)
    "freshness": str,     # Optional: "day", "week", "month" (default: "week")
}
```

**Output:** ToolResult with ToolItems

**Features:**
- Foundry grounding integration
- Freshness filtering
- Result normalization

### search_web_custom_domains

Search within allowed domains.

**Input:**
```python
{
    "query": str,             # Required: Search query
    "domains": list[str],     # Required: Allowed domains
    "max_results": int,       # Optional: Max results (default: 10, max: 50)
}
```

**Output:** ToolResult with ToolItems

**Features:**
- Domain allowlist enforcement
- Site-restricted search
- Result filtering

### fetch_nyt_items

Fetch NYT articles.

**Input:**
```python
{
    "query": str,         # Required: Search query
    "api_key": str,       # Required: NYT API key
    "max_results": int,   # Optional: Max results (default: 20, max: 50)
    "begin_date": str,    # Optional: Begin date (YYYYMMDD)
    "end_date": str,      # Optional: End date (YYYYMMDD)
}
```

**Output:** ToolResult with ToolItems

### fetch_x_items

Fetch X (Twitter) posts.

**Input:**
```python
{
    "query": str,           # Required: Search query
    "bearer_token": str,    # Required: X API bearer token
    "max_results": int,     # Optional: Max results (default: 20, max: 100)
    "start_time": str,      # Optional: Start time (ISO 8601)
    "end_time": str,        # Optional: End time (ISO 8601)
}
```

**Output:** ToolResult with ToolItems

## Testing

Run tests:

```bash
pytest tests/test_mcp_like.py
pytest tests/test_mcp_policy.py
pytest tests/test_rss_adapter.py
```

## Error Handling

All tools return ToolResult, never raise exceptions to the caller. Errors are captured and returned in the `errors` field:

```python
result = invoke_tool("fetch_rss_items", {"feed_url": "invalid"})

if result.errors:
    for error in result.errors:
        print(f"[{error.code}] {error.message}")
        if error.retryable:
            # Consider retry logic
            pass
```

## Security

- **SSRF Protection**: All URLs are validated against private IP ranges
- **URL Normalization**: Removes tracking parameters, normalizes format
- **HTML Sanitization**: Strips HTML tags from snippets
- **Rate Limiting**: Per-tool rate limiting support
- **Domain Allowlisting**: Custom search enforces domain restrictions

## Extension

To add a new tool:

1. Create adapter in `adapters/`
2. Create connector in `connectors/` (if needed)
3. Add to `bootstrap.py` registration
4. Write tests

Example:

```python
# adapters/my_adapter.py
from ..types import ToolResult, ToolItem

def fetch_my_items(payload: Dict[str, Any]) -> ToolResult:
    # Validate input
    # Call connector
    # Normalize results
    return ToolResult(items=[...])

# bootstrap.py
register_tool(
    name="fetch_my_items",
    handler=fetch_my_items,
    description="Fetch items from my service"
)
```
