from __future__ import annotations
import hashlib
import feedparser
from typing import List, Optional
from ..types import Candidate

def _stable_id(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]

def fetch_rss(feed_url: str, topic_hint: Optional[str] = None, limit: int = 25) -> List[Candidate]:
    feed = feedparser.parse(feed_url)
    out: List[Candidate] = []
    for entry in (feed.entries or [])[:limit]:
        url = entry.get("link")
        if not url:
            continue
        out.append(Candidate(
            id=_stable_id(url),
            title=(entry.get("title") or "").strip(),
            url=url,
            source=(feed.feed.get("title") or "rss").strip(),
            published_at=(entry.get("published") or entry.get("updated")),
            author=entry.get("author"),
            snippet=(entry.get("summary") or entry.get("description")),
            topic_tags=[topic_hint] if topic_hint else [],
            raw={"feed_url": feed_url},
        ))
    return out
