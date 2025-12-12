"""Newsletter generation workflow orchestration."""

from __future__ import annotations
from typing import Dict, Any
import logging
import time
from collections import Counter

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

from .types import Subscription, Newsletter, AgentState
from .ranking import simple_rank
from .safety import check_node_execution_limit
from .fetchers import (
    fetch_rss_candidates,
    fetch_nyt_candidates,
    fetch_x_candidates,
    fetch_foundry_candidates,
    filter_and_dedupe_candidates,
)
from .llm_ops import generate_newsletter_content


async def node_fetch_candidates(state: AgentState) -> AgentState:
    """Fetch candidates from all configured sources."""
    logger = logging.getLogger("newsletter_agent")
    start_time = time.time()
    
    if not check_node_execution_limit(state, "fetch_candidates"):
        return state
    
    subscription = state["subscription"]
    
    # Fetch from RSS sources
    rss_candidates = await fetch_rss_candidates(subscription, state)
    
    # Fetch from NYT
    nyt_candidates = await fetch_nyt_candidates(subscription, state)
    
    # Fetch from X (Twitter)
    x_candidates = await fetch_x_candidates(subscription, state)
    
    # Combine all candidates
    all_candidates = rss_candidates + nyt_candidates + x_candidates
    state["candidates"] = all_candidates
    
    # Log metrics
    elapsed_time = time.time() - start_time
    error_count = len(state.get("errors", []))
    logger.info(
        "Node execution completed: fetch_candidates",
        extra={
            "node_name": "fetch_candidates",
            "latency_seconds": round(elapsed_time, 3),
            "candidates_fetched": len(all_candidates),
            "error_count": error_count,
        }
    )
    
    return state



async def node_grounded_search(state: AgentState) -> AgentState:
    """Augment candidates with Foundry grounded search results."""
    logger = logging.getLogger("newsletter_agent")
    start_time = time.time()
    
    if not check_node_execution_limit(state, "grounded_search"):
        return state
    
    subscription = state["subscription"]
    
    # Fetch from Foundry
    foundry_candidates = await fetch_foundry_candidates(subscription, state)
    
    # Add to existing candidates
    if foundry_candidates:
        state["candidates"] = (state.get("candidates") or []) + foundry_candidates
    
    # Log metrics
    elapsed_time = time.time() - start_time
    error_count = len([e for e in state.get("errors", []) if e.source == "foundry"])
    logger.info(
        "Node execution completed: grounded_search",
        extra={
            "node_name": "grounded_search",
            "latency_seconds": round(elapsed_time, 3),
            "candidates_added": len(foundry_candidates),
            "error_count": error_count,
        }
    )
    
    return state



async def node_select_and_write(state: AgentState) -> AgentState:
    """Select top candidates and generate newsletter content."""
    logger = logging.getLogger("newsletter_agent")
    start_time = time.time()
    
    if not check_node_execution_limit(state, "select_and_write"):
        return state
    
    subscription = state["subscription"]
    
    # Filter and dedupe candidates
    candidates = filter_and_dedupe_candidates(
        state.get("candidates") or [], state
    )
    
    # Rank and pick top N
    ranked = simple_rank(candidates)
    picked = ranked[:subscription.item_count]
    
    # Generate newsletter content (handles all fallback cases)
    selected, newsletter = await generate_newsletter_content(
        subscription, picked, state
    )
    
    state["selected"] = selected
    state["newsletter"] = newsletter
    
    # Set status based on approval requirement
    if state.get("status") != "failed":  # Don't override failed status
        if subscription.require_approval:
            state["status"] = "draft"
        else:
            state["status"] = "approved"
    
    # Log metrics
    elapsed_time = time.time() - start_time
    logger.info(
        "Node execution completed: select_and_write",
        extra={
            "node_name": "select_and_write",
            "latency_seconds": round(elapsed_time, 3),
            "selected_count": len(selected),
            "status": state.get("status"),
        }
    )
    
    return state



def build_graph():
    """Build the newsletter generation workflow graph."""
    g = StateGraph(AgentState)
    g.add_node("fetch_candidates", node_fetch_candidates)
    g.add_node("grounded_search", node_grounded_search)
    g.add_node("select_and_write", node_select_and_write)

    g.add_edge(START, "fetch_candidates")
    g.add_edge("fetch_candidates", "grounded_search")
    g.add_edge("grounded_search", "select_and_write")
    g.add_edge("select_and_write", END)

    # For local dev we use InMemorySaver. Swap to a real checkpointer (Redis/Postgres/Cosmos) later.
    cp = InMemorySaver()
    return g.compile(checkpointer=cp)


async def run_once(subscription: Subscription) -> Newsletter:
    """
    Run the newsletter generation workflow once for a subscription.
    Includes structured logging for monitoring and debugging.
    """
    logger = logging.getLogger("newsletter_agent")
    
    # Log start of workflow
    logger.info(
        "Starting newsletter generation",
        extra={
            "thread_id": f"sub:{subscription.id}",
            "subscription_id": subscription.id,
            "user_id": subscription.user_id,
            "topics": subscription.topics,
            "source_count": len(subscription.sources),
        }
    )
    
    graph = build_graph()
    out = await graph.ainvoke({"subscription": subscription}, config={"thread_id": f"sub:{subscription.id}"})
    
    # Log completion with metrics
    errors = out.get("errors", [])
    error_summary = Counter(f"{e.source}:{e.code}" for e in errors)
    
    used_fallback = any(
        e.code in ["no_candidates", "invoke_failure", "token_limit_exceeded"] 
        for e in errors
    )
    
    logger.info(
        "Newsletter generation completed",
        extra={
            "thread_id": f"sub:{subscription.id}",
            "subscription_id": subscription.id,
            "candidate_count": len(out.get("candidates", [])),
            "selected_count": len(out.get("selected", [])),
            "error_count": len(errors),
            "errors_by_type": dict(error_summary),
            "used_fallback": used_fallback,
            "node_execution_count": out.get("node_execution_count", 0),
        }
    )
    
    return out["newsletter"]

async def run_once_draft(subscription: Subscription) -> Dict[str, Any]:
    """
    Run the newsletter generation workflow in draft mode (no sending).
    Returns the newsletter along with metadata for review.
    
    Use this when subscription.require_approval is True.
    
    Returns:
        Dict containing:
            - newsletter: The generated Newsletter object
            - errors: List of Error objects encountered
            - candidates: List of candidate articles considered
            - selected: List of selected items in the newsletter
            - metadata: Additional metadata for review
    """
    logger = logging.getLogger("newsletter_agent")
    
    logger.info(
        "Starting newsletter generation (DRAFT MODE)",
        extra={
            "thread_id": f"sub:{subscription.id}",
            "subscription_id": subscription.id,
            "user_id": subscription.user_id,
            "require_approval": True,
        }
    )
    
    graph = build_graph()
    out = await graph.ainvoke({"subscription": subscription}, config={"thread_id": f"sub:{subscription.id}"})
    
    # Log completion
    errors = out.get("errors", [])
    logger.info(
        "Newsletter draft generation completed",
        extra={
            "thread_id": f"sub:{subscription.id}",
            "subscription_id": subscription.id,
            "candidate_count": len(out.get("candidates", [])),
            "selected_count": len(out.get("selected", [])),
            "error_count": len(errors),
            "require_approval": True,
        }
    )
    
    # Return full state for review
    return {
        "newsletter": out.get("newsletter"),
        "errors": errors,
        "candidates": out.get("candidates", []),
        "selected": out.get("selected", []),
        "metadata": {
            "subscription_id": subscription.id,
            "user_id": subscription.user_id,
            "topics": subscription.topics,
            "node_execution_count": out.get("node_execution_count", 0),
        }
    }
