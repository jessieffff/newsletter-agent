"""Candidate fetching and filtering operations."""

from typing import List
import logging
from urllib.parse import urlparse

from .types import Subscription, Candidate, AgentState, Error
from .config import is_domain_allowed, is_candidate_reasonable
from .ranking import dedupe_candidates
from .tools.rss import fetch_rss
from .tools.nyt import fetch_nyt
from .tools.x_twitter import fetch_x_recent
from .tools.foundry_grounding import grounded_search_via_foundry
from .settings import get_external_api_settings, get_foundry_settings
from .safety import check_rss_feed_limit, check_external_search_limit


async def fetch_rss_candidates(
    subscription: Subscription, state: AgentState
) -> List[Candidate]:
    """Fetch candidates from RSS sources with domain validation and rate limiting."""
    logger = logging.getLogger("newsletter_agent")
    candidates: List[Candidate] = []
    
    rss_sources = [s for s in subscription.sources if s.kind == "rss"]
    
    # Check and enforce RSS feed limit
    is_within_limit, indices_to_fetch = check_rss_feed_limit(len(rss_sources), state)
    sources_to_fetch = [rss_sources[i] for i in indices_to_fetch]
    
    for source in sources_to_fetch:
        try:
            # Check domain allow-list before fetching
            parsed = urlparse(source.value)
            domain = parsed.netloc
            
            if not is_domain_allowed(domain):
                error = Error(
                    source="rss",
                    code="domain_not_allowed",
                    message=f"RSS feed domain '{domain}' is not in the allow-list",
                    details={"feed_url": source.value, "domain": domain}
                )
                state.setdefault("errors", []).append(error)
                continue
            
            topic_hint = subscription.topics[0] if subscription.topics else None
            fetched = fetch_rss(source.value, topic_hint=topic_hint)
            candidates.extend(fetched)
            
        except Exception as e:
            error = Error(
                source="rss",
                code="fetch_failure",
                message=str(e),
                details={"feed_url": source.value}
            )
            state.setdefault("errors", []).append(error)
    
    return candidates


async def fetch_nyt_candidates(
    subscription: Subscription, state: AgentState
) -> List[Candidate]:
    """Fetch candidates from NYT API if configured."""
    candidates: List[Candidate] = []
    external_apis = get_external_api_settings()
    
    if not external_apis.nyt_api_key or not subscription.topics:
        return candidates
    
    try:
        query = " OR ".join(subscription.topics[:3])
        candidates = await fetch_nyt(query, external_apis.nyt_api_key, limit=20)
    except Exception as e:
        error = Error(
            source="nyt",
            code="fetch_failure",
            message=str(e),
            details={"query": " OR ".join(subscription.topics[:3])}
        )
        state.setdefault("errors", []).append(error)
    
    return candidates


async def fetch_x_candidates(
    subscription: Subscription, state: AgentState
) -> List[Candidate]:
    """Fetch candidates from X (Twitter) API if configured."""
    candidates: List[Candidate] = []
    external_apis = get_external_api_settings()
    
    if not external_apis.x_bearer_token or not subscription.topics:
        return candidates
    
    try:
        query = " OR ".join(subscription.topics[:3])
        candidates = await fetch_x_recent(query, external_apis.x_bearer_token, limit=20)
    except Exception as e:
        error = Error(
            source="x",
            code="fetch_failure",
            message=str(e),
            details={"query": " OR ".join(subscription.topics[:3])}
        )
        state.setdefault("errors", []).append(error)
    
    return candidates


async def fetch_foundry_candidates(
    subscription: Subscription, state: AgentState
) -> List[Candidate]:
    """Fetch candidates from Foundry grounded search if configured."""
    candidates: List[Candidate] = []
    
    if not subscription.topics:
        return candidates
    
    # Check external search limit
    if not check_external_search_limit(state):
        return candidates
    
    foundry_settings = get_foundry_settings()
    if not foundry_settings:
        return candidates
    
    try:
        query = " OR ".join(subscription.topics[:3])
        candidates = await grounded_search_via_foundry(query, freshness="7d", count=10)
    except Exception as e:
        error = Error(
            source="foundry",
            code="grounded_search_failure",
            message=str(e),
            details={"query": " OR ".join(subscription.topics[:3])}
        )
        state.setdefault("errors", []).append(error)
    
    return candidates


def filter_and_dedupe_candidates(
    candidates: List[Candidate], state: AgentState
) -> List[Candidate]:
    """Apply deduplication and sanity checks to candidates."""
    # First dedupe
    deduped = dedupe_candidates(candidates)
    
    # Then filter with sanity checks
    reasonable = [c for c in deduped if is_candidate_reasonable(c)]
    
    filtered_count = len(deduped) - len(reasonable)
    if filtered_count > 0:
        error = Error(
            source="system",
            code="candidates_filtered",
            message=f"Filtered out {filtered_count} candidates that failed sanity checks",
            details={"original_count": len(deduped), "filtered_count": filtered_count}
        )
        state.setdefault("errors", []).append(error)
    
    return reasonable
