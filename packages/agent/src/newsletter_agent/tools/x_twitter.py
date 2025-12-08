from __future__ import annotations
import hashlib
from typing import List, Optional
import httpx
from ..types import Candidate

def _stable_id(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]

# NOTE: X API access/tiers vary; the Recent Search endpoint is commonly limited to ~7 days.
# This connector is intentionally minimal: supply a Bearer token and a query string.
async def fetch_x_recent(query: str, bearer_token: str, limit: int = 25) -> List[Candidate]:
    endpoint = "https://api.x.com/2/tweets/search/recent"
    headers = {"Authorization": f"Bearer {bearer_token}"}
    params = {
        "query": query,
        "max_results": min(limit, 100),
        "tweet.fields": "created_at,author_id",
    }
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(endpoint, headers=headers, params=params)
        r.raise_for_status()
        data = r.json()
    out: List[Candidate] = []
    for t in (data.get("data") or [])[:limit]:
        tid = t.get("id")
        if not tid:
            continue
        url = f"https://x.com/i/web/status/{tid}"
        out.append(Candidate(
            id=_stable_id(url),
            title=(t.get("text") or "")[:120].replace("\n", " ").strip(),
            url=url,
            source="X",
            published_at=t.get("created_at"),
            author=t.get("author_id"),
            snippet=t.get("text"),
            topic_tags=[query],
            raw={"x": {"tweet_id": tid}},
        ))
    return out
