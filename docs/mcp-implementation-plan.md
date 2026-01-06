Embedded Mini MCP Implementation Plan — Newsletter Agent

Scope
-----
Build a lightweight MCP-like infrastructure inside the newsletter agent backend that:
- Standardizes tool calls
- Centralizes external integrations (RSS, web search, NYT, X)
- Produces structured results for workflow nodes
- Supports error classification and merges

This gives benefits of MCP without deploying a separate server.

Repo Layout
-----------
newsletter/
  apps/
    newsletter-web/         # Next.js UI
    newsletter-api/         # Backend REST/GraphQL API
  packages/
    newsletter-agent/
      src/
        graph/
          state.py          # Typed state
          nodes/
            gather_candidates.py
            rank_and_select.py
            write_newsletter.py
            persist_run.py
        mcp_like/
          registry.py       # Tool registry
          executor.py       # Standardized tool invocation
          errors.py         # Standard error types
          types.py          # Shared tool result types
        tools/
          rss_adapter.py
          web_search_adapter.py
          custom_search_adapter.py
          nyt_adapter.py
          x_adapter.py
      tests/
        tools/
        mcp_like/
        graph/
    shared/
      src/
        schemas.py          # JSON Schemas for tool results
        constants.py

High-level Design
-----------------
Instead of a separate MCP server, we embed an internal registry of tools with:
- Tool metadata (name, input schema, output schema)
- Standard invocation entry point

Workflow nodes call the same interface:
    result = invoke_tool("fetch_rss_items", payload)

The executor:
- Validates input
- Calls the correct adapter
- Normalizes output to a shared shape
- Handles errors uniformly

Tool Result Shape (common)
---------------------------
{
  "items": [
    {
      "title": "string",
      "url": "string",             // canonical, validated
      "published_at": "ISO8601|null",
      "snippet": "string|null",
      "source": "string",          // e.g. rss:<feed>, web:bing, nyt, x
      "raw_id": "string|null"
    }
  ],
  "meta": { ... },
  "warnings": [ ... ],            // non-fatal issues
  "errors": [ ... ]               // partial errors
}

Standard Error Shape
--------------------
{
  "tool": "string",
  "code": "INVALID_INPUT|FETCH_FAILED|TIMEOUT|PARSE_FAILED|RATE_LIMITED|AUTH_FAILED|PROVIDER_ERROR",
  "message": "string",
  "retryable": bool,
  "context": { ... }
}

1) Registry (registry.py)
-------------------------
- register_tool(name, handler_fn, input_schema, output_schema)
- returns tool metadata

Example:
register_tool("fetch_rss_items", rss_adapter.fetch_rss_items, FetchRSSInput, ToolOutput)

2) Executor (executor.py)
-------------------------
invoke_tool(name, payload):
  - Look up handler
  - Validate payload against schema
  - Try:
      result = handler(payload)
    Catch expected exceptions:
      convert to standard error shape
  - Validate result against output schema
  - Return result

Retries for retryable failures can be orchestrated here if desired.

3) Tools / Adapters (tools/*.py)
--------------------------------
Each adapter:
- Implements provider logic
- Normalizes responses to shared item shape
- Raises well-typed exceptions for known failure modes
- Reports warnings

Adapters:
- rss_adapter.py
  fetch_rss_items(payload)
- web_search_adapter.py
  search_web_fresh(payload)
- custom_search_adapter.py
  search_web_custom_domains(payload)
- nyt_adapter.py
  fetch_nyt_items(payload)
- x_adapter.py
  fetch_x_items(payload)

Each adheres to:
input → validated → connector calls → normalization

4) Connectors (called inside adapters)
--------------------------------------
Encapsulate actual network calls:
- RSS fetch + parse
- Bing grounding / custom search
- NYT API
- X API

5) Policy Modules
-----------------
Common validators:
- URL normalization and SSRF guard
- Allowlist enforcement (for custom domains)
- Rate limiting
- Caching
- Content sanitization (strip HTML, etc.)

6) Graph Node Integration
-------------------------
Nodes call the executor:
state.candidates += invoke_tool(…)
provenance[url] = tool_name
tool_errors append on failure

Nodes do merging, dedupe, filtering — adapter returns pure results.

Implementation Steps
--------------------

Phase 0 — Foundation
--------------------
1. Create mcp_like registry + executor modules
2. Define types and error shapes
3. Add JSON Schemas in shared/schemas.py

Phase 1 — Tool Adapters
-----------------------
fetch_rss_items:
- validate URL
- fetch + parse RSS
- normalize items

search_web_fresh:
- build query from topics
- call bounding service (e.g., Foundry Bing)
- normalize results

search_web_custom_domains:
- validate domain allowlist
- call custom search
- normalize results

fetch_nyt_items:
- call NYT search
- normalize

fetch_x_items:
- call X API
- normalize

Phase 2 — Node Integration
--------------------------
- gather_candidates → calls each tool via executor
- merge results, dedupe, provenance
- rank_and_select → no external calls
- write_newsletter → guarded use of selected URLs
- persist_run → store results + errors

Testing Plan
------------

Unit Tests
----------
- Validator: URL normalization, SSRF guard
- Schema validation: input/output shape
- Adapter basics with fixtures

Adapter Tests
-------------
RSS:
- valid RSS, Atom
- missing dates
- invalid URLs dropped

Web search:
- duplicates
- empty results

NYT:
- basic mapping

X:
- tweet results

Contract Tests
--------------
- Ensure executor returns correct shape
- Schema conformance

Integration Tests
-----------------
- With mocked HTTP connectors
- Multiple tools returning and merging

E2E Tests
---------
- gather_candidates with all tools
- ensure candidates + provenance + tool_errors are correct

Performance & Reliability
-------------------------
- Rate limit response shaping
- Partial failure tolerance

Security
--------
- SSRF attempts
- oversized responses

Delivery Checklist
------------------
- Tools implemented
- Executor + registry completed
- Tests covering adapters + executor
- Node integration verified
- Schema docs written
- Logging + observability