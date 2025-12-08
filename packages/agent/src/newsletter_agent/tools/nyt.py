from __future__ import annotations
import hashlib
from typing import List, Optional
import httpx
from ..types import Candidate

def _stable_id(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]

# NYT: Article Search API (metadata + snippets). You provide your own API key.
# Docs: https://developer.nytimes.com/docs/articlesearch-product/1/overview
async def fetch_nyt(query: str, api_key: str, limit: int = 25) -> List[Candidate]:
    url = "https://api.nytimes.com/svc/search/v2/articlesearch.json"
    params = {"q": query, "sort": "newest", "api-key": api_key}
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        data = r.json()
    docs = (data.get("response") or {}).get("docs") or []
    out: List[Candidate] = []
    for d in docs[:limit]:
        web_url = d.get("web_url")
        if not web_url:
            continue
        headline = ((d.get("headline") or {}).get("main") or "").strip()
        out.append(Candidate(
            id=_stable_id(web_url),
            title=headline,
            url=web_url,
            source="NYT",
            published_at=d.get("pub_date"),
            author=(((d.get("byline") or {}).get("original"))),
            snippet=d.get("abstract") or d.get("lead_paragraph"),
            topic_tags=[query],
            raw={"nyt": {"section": d.get("section_name"), "news_desk": d.get("news_desk")}},
        ))
    return out
