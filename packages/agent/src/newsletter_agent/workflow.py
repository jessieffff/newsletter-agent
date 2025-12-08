from __future__ import annotations
from typing import TypedDict, List, Optional, Dict, Any
import asyncio

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from .types import Subscription, Candidate, SelectedItem, Newsletter
from .ranking import dedupe_candidates, simple_rank
from .render import render_newsletter
from .tools.rss import fetch_rss
from .tools.nyt import fetch_nyt
from .tools.x_twitter import fetch_x_recent
from .tools.foundry_grounding import grounded_search_via_foundry

class AgentState(TypedDict, total=False):
    subscription: Subscription
    candidates: List[Candidate]
    selected: List[SelectedItem]
    newsletter: Newsletter
    errors: List[str]

def build_llm() -> AzureChatOpenAI:
    return AzureChatOpenAI(
        azure_endpoint = __import__("os").environ.get("AZURE_OPENAI_ENDPOINT"),
        api_key = __import__("os").environ.get("AZURE_OPENAI_API_KEY"),
        api_version = __import__("os").environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21"),
        azure_deployment = __import__("os").environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"),
        temperature=0.2,
        timeout=45,
    )

async def node_fetch_candidates(state: AgentState) -> AgentState:
    sub = state["subscription"]
    candidates: List[Candidate] = []
    # RSS sources explicitly provided
    for s in sub.sources:
        if s.kind == "rss":
            try:
                candidates += fetch_rss(s.value, topic_hint=sub.topics[0] if sub.topics else None)
            except Exception as e:
                state.setdefault("errors", []).append(f"rss:{s.value}:{e}")

    # Optional NYT
    import os
    nyt_key = os.environ.get("NYT_API_KEY")
    if nyt_key and sub.topics:
        try:
            candidates += await fetch_nyt(" OR ".join(sub.topics[:3]), nyt_key, limit=20)
        except Exception as e:
            state.setdefault("errors", []).append(f"nyt:{e}")

    # Optional X
    x_token = os.environ.get("X_BEARER_TOKEN")
    if x_token and sub.topics:
        try:
            candidates += await fetch_x_recent(" OR ".join(sub.topics[:3]), x_token, limit=20)
        except Exception as e:
            state.setdefault("errors", []).append(f"x:{e}")

    state["candidates"] = candidates
    return state

async def node_grounded_search(state: AgentState) -> AgentState:
    sub = state["subscription"]
    if not sub.topics:
        return state
    # Best-effort: if Foundry env vars are present, augment candidates.
    import os
    if os.environ.get("FOUNDRY_PROJECT_ENDPOINT") and os.environ.get("FOUNDRY_BING_CONNECTION_ID"):
        try:
            extra = await grounded_search_via_foundry(" OR ".join(sub.topics[:3]), freshness="7d", count=10)
            state["candidates"] = (state.get("candidates") or []) + extra
        except Exception as e:
            state.setdefault("errors", []).append(f"foundry:{e}")
    return state

async def node_select_and_write(state: AgentState) -> AgentState:
    sub = state["subscription"]
    llm = build_llm()

    candidates = dedupe_candidates(state.get("candidates") or [])
    ranked = simple_rank(candidates)
    picked = ranked[: sub.item_count]

    # Ask LLM to turn each candidate into a newsletter item.
    # IMPORTANT: we never invent URLs—only use candidate URLs.
    sys = SystemMessage(content=(
        "You are an expert newsletter editor. "
        "Given a list of headlines+snippets+links, produce crisp newsletter entries. "
        "Do NOT invent facts. If you lack context, say so briefly. "
        "Always keep the URL exactly as given."
    ))
    lines = []
    for c in picked:
        lines.append(f"- title: {c.title}\n  source: {c.source}\n  url: {c.url}\n  snippet: {c.snippet or ''}\n  published_at: {c.published_at or ''}")
    prompt = HumanMessage(content=(
        f"Tone: {sub.tone}\n"
        f"Create {len(picked)} newsletter items. For each, return:\n"
        f"1) why_it_matters (1 sentence)\n"
        f"2) summary (2-3 sentences)\n"
        f"Use the snippets; do not add unverified claims.\n\n"
        f"Candidates:\n" + "\n".join(lines)
    ))

    resp = await llm.ainvoke([sys, prompt])

    # Minimal parsing: we will package the whole response, then optionally refine later.
    # For MVP, create items with LLM text chunked by candidate order.
    text = resp.content if isinstance(resp.content, str) else str(resp.content)

    selected: List[SelectedItem] = []
    chunks = [c.strip() for c in text.split("\n- ") if c.strip()]
    for idx, c in enumerate(picked):
        chunk = chunks[idx] if idx < len(chunks) else text
        selected.append(SelectedItem(
            title=c.title,
            url=c.url,
            source=c.source,
            published_at=c.published_at,
            why_it_matters=_extract_field(chunk, "why") or "Why it matters: (not provided)",
            summary=_extract_field(chunk, "summary") or chunk[:400],
        ))

    subject = f"Your news digest: {', '.join(sub.topics[:2]) or 'Latest'}"
    state["selected"] = selected
    state["newsletter"] = render_newsletter(subject, selected)
    return state

def _extract_field(chunk: str, kind: str) -> str | None:
    # super-lightweight parsing; you can replace with structured outputs later
    lower = chunk.lower()
    if kind == "why":
        m = __import__("re").search(r"why[^:]*:\s*(.+)", chunk, flags=__import__("re").I)
        return m.group(1).strip() if m else None
    if kind == "summary":
        m = __import__("re").search(r"summary[^:]*:\s*(.+)", chunk, flags=__import__("re").I | __import__("re").S)
        return m.group(1).strip() if m else None
    return None

def build_graph():
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
    graph = build_graph()
    out = await graph.ainvoke({"subscription": subscription}, config={"thread_id": f"sub:{subscription.id}"})
    return out["newsletter"]
