"""Safety and rate limiting utilities for workflow execution."""

from typing import List, Optional
from .types import Error, AgentState, Candidate

# Safety constants
MAX_NODE_EXECUTIONS = 20  # Prevent infinite loops
MAX_TOKENS_PER_NEWSLETTER = 10000  # Token cap for LLM calls
CHARS_PER_TOKEN = 4  # Rough estimate: 1 token ~= 4 characters
MAX_RSS_FEEDS_PER_RUN = 10  # Limit RSS feed fetches
MAX_EXTERNAL_SEARCH_CALLS = 2  # Limit external search calls (Foundry, etc.)


def check_node_execution_limit(state: AgentState, node_name: str) -> bool:
    """
    Check and increment node execution counter.
    Returns True if execution should continue, False if limit exceeded.
    """
    count = state.get("node_execution_count", 0)
    if count >= MAX_NODE_EXECUTIONS:
        error = Error(
            source="system",
            code="execution_limit_exceeded",
            message=f"Maximum node execution limit ({MAX_NODE_EXECUTIONS}) exceeded",
            details={"node_name": node_name, "execution_count": count}
        )
        state.setdefault("errors", []).append(error)
        state["status"] = "failed"
        return False
    state["node_execution_count"] = count + 1
    return True


def estimate_tokens(text: str) -> int:
    """Estimate token count based on character length."""
    return len(text) // CHARS_PER_TOKEN


def check_token_limit(prompt_text: str) -> bool:
    """Check if estimated token count exceeds the limit."""
    estimated_tokens = estimate_tokens(prompt_text)
    return estimated_tokens <= MAX_TOKENS_PER_NEWSLETTER


def check_rss_feed_limit(
    feed_count: int, state: AgentState
) -> tuple[bool, List[int]]:
    """
    Check RSS feed limit and return (is_within_limit, indices_to_fetch).
    If over limit, logs error to state and returns truncated list of indices.
    """
    if feed_count > MAX_RSS_FEEDS_PER_RUN:
        error = Error(
            source="rss",
            code="rate_limit_exceeded",
            message=f"Number of RSS feeds ({feed_count}) exceeds limit of {MAX_RSS_FEEDS_PER_RUN}",
            details={"requested": feed_count, "max_allowed": MAX_RSS_FEEDS_PER_RUN}
        )
        state.setdefault("errors", []).append(error)
        return False, list(range(MAX_RSS_FEEDS_PER_RUN))
    return True, list(range(feed_count))


def check_external_search_limit(state: AgentState) -> bool:
    """
    Check external search call limit.
    Returns True if call can proceed, False otherwise.
    Logs error to state if limit exceeded.
    """
    search_count = state.get("external_search_count", 0)
    if search_count >= MAX_EXTERNAL_SEARCH_CALLS:
        error = Error(
            source="foundry",
            code="rate_limit_exceeded",
            message=f"External search call limit ({MAX_EXTERNAL_SEARCH_CALLS}) exceeded",
            details={"search_count": search_count}
        )
        state.setdefault("errors", []).append(error)
        return False
    state["external_search_count"] = search_count + 1
    return True
