from __future__ import annotations
from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl

Frequency = Literal["daily", "weekly", "custom_cron"]

class SourceSpec(BaseModel):
    kind: Literal["rss", "nyt", "x", "domain"]
    value: str  # e.g. RSS URL, "nytimes", "@some_account", "theverge.com"

class Subscription(BaseModel):
    id: str
    user_id: str
    topics: List[str] = Field(default_factory=list)
    sources: List[SourceSpec] = Field(default_factory=list)
    frequency: Frequency = "daily"
    cron: Optional[str] = None
    item_count: int = 8
    tone: str = "concise, professional"
    enabled: bool = True

class Candidate(BaseModel):
    id: str
    title: str
    url: HttpUrl
    source: str
    published_at: Optional[str] = None  # ISO8601 string for simplicity
    author: Optional[str] = None
    snippet: Optional[str] = None
    topic_tags: List[str] = Field(default_factory=list)
    raw: Dict[str, Any] = Field(default_factory=dict)

class SelectedItem(BaseModel):
    title: str
    url: HttpUrl
    source: str
    published_at: Optional[str] = None
    why_it_matters: str
    summary: str

class Newsletter(BaseModel):
    subject: str
    html: str
    text: str
    items: List[SelectedItem]
