"""Newsletter generation workflow orchestration."""

from __future__ import annotations
from typing import Dict, Any
import logging
import time
from collections import Counter

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

from .types import (
    Subscription, Newsletter, AgentState, 
    CandidateForRanking, SelectedItemForDraft, SelectedItem, Error
)
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
from .tools import llm_rank_and_select, llm_draft_newsletter_items
from .observability import span as otel_span


async def node_fetch_candidates(state: AgentState) -> AgentState:
    """Fetch candidates from all configured sources."""
    logger = logging.getLogger("newsletter_agent")
    start_time = time.time()

    with otel_span(
        "agent.node.fetch_candidates",
        attributes={
            "app.component": "agent",
            "node.name": "fetch_candidates",
            "subscription_id": getattr(state.get("subscription"), "id", None),
        },
    ):
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
            },
        )

        return state



async def node_grounded_search(state: AgentState) -> AgentState:
    """Augment candidates with Foundry grounded search results."""
    logger = logging.getLogger("newsletter_agent")
    start_time = time.time()

    with otel_span(
        "agent.node.grounded_search",
        attributes={
            "app.component": "agent",
            "node.name": "grounded_search",
            "subscription_id": getattr(state.get("subscription"), "id", None),
        },
    ):
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
            },
        )

        return state



async def node_select_and_write(state: AgentState) -> AgentState:
    """Select top candidates and generate newsletter content."""
    logger = logging.getLogger("newsletter_agent")
    start_time = time.time()

    # Initialize telemetry variables
    used_llm_ranker = False
    used_llm_drafter = False
    llm_ranker_fallback_reason = None
    llm_drafter_fallback_reason = None
    max_per_domain_enforced = False

    with otel_span(
        "agent.node.select_and_write",
        attributes={
            "app.component": "agent",
            "node.name": "select_and_write",
            "subscription_id": getattr(state.get("subscription"), "id", None),
        },
    ):
        if not check_node_execution_limit(state, "select_and_write"):
            return state

        subscription = state["subscription"]

        # Filter and dedupe candidates
        candidates = filter_and_dedupe_candidates(state.get("candidates") or [], state)
        
        if not candidates:
            logger.warning("No candidates available for selection")
            state["selected"] = []
            state["newsletter"] = Newsletter(subject="No content available", html="", text="", items=[])
            state["status"] = "failed"
            return state

        # Assign stable IDs for LLM processing
        candidates_for_ranking = []
        for idx, candidate in enumerate(candidates):
            candidate_id = f"cand:{idx}"
            candidates_for_ranking.append(CandidateForRanking(
                id=candidate_id,
                title=candidate.title,
                url=str(candidate.url),
                source=candidate.source,
                published_at=candidate.published_at,
                snippet=candidate.snippet
            ))

        # Use LLM to rank and select candidates
        try:
            selected_ids, used_llm_ranker, llm_ranker_fallback_reason = await llm_rank_and_select(
                topics=subscription.topics,
                target_count=subscription.item_count,
                max_per_domain=2,  # Default from spec
                candidates=candidates_for_ranking,
                state=state
            )

            # Check if domain enforcement was needed
            if len(selected_ids) != subscription.item_count and len(candidates_for_ranking) >= subscription.item_count:
                max_per_domain_enforced = True

            # Map selected IDs back to original candidates
            id_to_candidate = {c.id: candidates[i] for i, c in enumerate(candidates_for_ranking)}
            picked = [id_to_candidate[sid] for sid in selected_ids if sid in id_to_candidate]

        except Exception as e:
            logger.error(f"LLM ranking failed: {e}")
            # Add error to state
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append(Error(
                source="llm",
                code="rank_and_select_failed", 
                message=f"LLM ranking failed: {str(e)}"
            ))
            
            # Fallback to simple ranking
            ranked = simple_rank(candidates)
            picked = ranked[:subscription.item_count]
            used_llm_ranker = False
            llm_ranker_fallback_reason = f"exception: {str(e)}"

        # Prepare items for drafting
        items_for_drafting = []
        for idx, candidate in enumerate(picked):
            items_for_drafting.append(SelectedItemForDraft(
                id=f"item:{idx}",
                title=candidate.title,
                url=str(candidate.url),
                source=candidate.source,
                published_at=candidate.published_at,
                snippet=candidate.snippet
            ))

        # Use LLM to draft newsletter content
        try:
            draft_output, used_llm_drafter, llm_drafter_fallback_reason = await llm_draft_newsletter_items(
                tone=subscription.tone,
                max_summary_sentences=3,
                items=items_for_drafting,
                state=state
            )

            # Convert draft output to final format
            if draft_output and "items" in draft_output:
                selected_items = []
                for draft_item in draft_output["items"]:
                    # Find corresponding picked candidate
                    item_id = draft_item["id"]
                    item_index = int(item_id.split(":")[1]) if ":" in item_id else 0
                    if item_index < len(picked):
                        original_candidate = picked[item_index]
                        selected_items.append(SelectedItem(
                            title=draft_item.get("title", original_candidate.title),
                            url=original_candidate.url,
                            source=draft_item.get("source", original_candidate.source),
                            published_at=original_candidate.published_at,
                            why_it_matters=draft_item.get("why_it_matters", "This story provides important updates."),
                            summary=draft_item.get("summary", "Summary not available.")
                        ))

                # Create newsletter
                from .render import render_newsletter  # Import here to avoid circular imports
                html_content = render_newsletter(
                    subject=draft_output.get("subject", "Newsletter Update"),
                    items=selected_items
                )
                
                newsletter = Newsletter(
                    subject=draft_output.get("subject", "Newsletter Update"),
                    html=html_content,
                    text="",  # Could implement text version
                    items=selected_items
                )

                state["selected"] = selected_items
                state["newsletter"] = newsletter
            else:
                raise ValueError("Invalid draft output format")

        except Exception as e:
            logger.error(f"LLM drafting failed: {e}")
            # Add error to state
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append(Error(
                source="llm",
                code="draft_newsletter_items_failed",
                message=f"LLM drafting failed: {str(e)}"
            ))

            # Fallback to existing generate_newsletter_content
            selected, newsletter = await generate_newsletter_content(
                subscription, picked, state
            )
            state["selected"] = selected
            state["newsletter"] = newsletter
            used_llm_drafter = False
            llm_drafter_fallback_reason = f"exception: {str(e)}"

        # Set status based on approval requirement
        if state.get("status") != "failed":  # Don't override failed status
            if subscription.require_approval:
                state["status"] = "draft"
            else:
                state["status"] = "approved"

        # Log metrics with telemetry
        elapsed_time = time.time() - start_time
        logger.info(
            "Node execution completed: select_and_write",
            extra={
                "node_name": "select_and_write",
                "latency_seconds": round(elapsed_time, 3),
                "selected_count": len(state.get("selected", [])),
                "status": state.get("status"),
                "used_llm_ranker": used_llm_ranker,
                "used_llm_drafter": used_llm_drafter,
                "llm_ranker_fallback_reason": llm_ranker_fallback_reason,
                "llm_drafter_fallback_reason": llm_drafter_fallback_reason,
                "max_per_domain_enforced": max_per_domain_enforced,
            },
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

    with otel_span(
        "agent.run",
        attributes={
            "app.component": "agent",
            "subscription_id": subscription.id,
            "user_id": subscription.user_id,
            "source_count": len(subscription.sources),
        },
    ):
        # Log start of workflow
        logger.info(
            "Starting newsletter generation",
            extra={
                "thread_id": f"sub:{subscription.id}",
                "subscription_id": subscription.id,
                "user_id": subscription.user_id,
                "topics": subscription.topics,
                "source_count": len(subscription.sources),
            },
        )

        graph = build_graph()
        out = await graph.ainvoke(
            {"subscription": subscription}, config={"thread_id": f"sub:{subscription.id}"}
        )
    
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
            },
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
