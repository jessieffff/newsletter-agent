"""
JSON Schemas for tool inputs and outputs.
"""

# Standard tool result schema
TOOL_RESULT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "url": {"type": "string", "format": "uri"},
                    "published_at": {"type": ["string", "null"], "format": "date-time"},
                    "snippet": {"type": ["string", "null"]},
                    "source": {"type": "string"},
                    "raw_id": {"type": ["string", "null"]},
                },
                "required": ["title", "url"],
            },
        },
        "meta": {
            "type": ["object", "null"],
            "properties": {
                "tool_name": {"type": "string"},
                "execution_time_ms": {"type": "number"},
                "item_count": {"type": "integer"},
                "provider_metadata": {"type": "object"},
            },
        },
        "warnings": {
            "type": "array",
            "items": {"type": "string"},
        },
        "errors": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "tool": {"type": "string"},
                    "code": {
                        "type": "string",
                        "enum": [
                            "INVALID_INPUT",
                            "FETCH_FAILED",
                            "TIMEOUT",
                            "PARSE_FAILED",
                            "RATE_LIMITED",
                            "AUTH_FAILED",
                            "PROVIDER_ERROR",
                        ],
                    },
                    "message": {"type": "string"},
                    "retryable": {"type": "boolean"},
                    "context": {"type": "object"},
                },
                "required": ["tool", "code", "message", "retryable"],
            },
        },
    },
    "required": ["items"],
}

# RSS fetch input schema
FETCH_RSS_INPUT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "feed_url": {"type": "string", "format": "uri"},
        "max_items": {"type": "integer", "minimum": 1, "maximum": 100},
    },
    "required": ["feed_url"],
}

# Web search input schema
WEB_SEARCH_INPUT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "query": {"type": "string", "minLength": 1},
        "max_results": {"type": "integer", "minimum": 1, "maximum": 50},
        "freshness": {"type": "string", "enum": ["day", "week", "month"]},
    },
    "required": ["query"],
}

# Custom search input schema
CUSTOM_SEARCH_INPUT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "query": {"type": "string", "minLength": 1},
        "domains": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
        },
        "max_results": {"type": "integer", "minimum": 1, "maximum": 50},
    },
    "required": ["query", "domains"],
}

# NYT search input schema
NYT_SEARCH_INPUT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "query": {"type": "string", "minLength": 1},
        "max_results": {"type": "integer", "minimum": 1, "maximum": 50},
        "begin_date": {"type": "string", "format": "date"},
        "end_date": {"type": "string", "format": "date"},
    },
    "required": ["query"],
}

# X (Twitter) search input schema
X_SEARCH_INPUT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "query": {"type": "string", "minLength": 1},
        "max_results": {"type": "integer", "minimum": 1, "maximum": 100},
        "start_time": {"type": "string", "format": "date-time"},
        "end_time": {"type": "string", "format": "date-time"},
    },
    "required": ["query"],
}
