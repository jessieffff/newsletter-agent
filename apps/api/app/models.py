from __future__ import annotations
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class UserIn(BaseModel):
    email: str

class User(BaseModel):
    id: str
    email: str

class SourceSpec(BaseModel):
    kind: Literal["rss", "nyt", "x", "domain"]
    value: str

class SubscriptionIn(BaseModel):
    topics: List[str] = Field(default_factory=list)
    sources: List[SourceSpec] = Field(default_factory=list)
    frequency: Literal["daily", "weekly", "custom_cron"] = "daily"
    cron: Optional[str] = None
    item_count: int = 8
    tone: str = "concise, professional"
    enabled: bool = True

class Subscription(SubscriptionIn):
    id: str
    user_id: str

class NewsletterRun(BaseModel):
    id: str
    subscription_id: str
    run_at: str
    status: Literal["queued", "sent", "failed", "drafted"]
    subject: Optional[str] = None
    html: Optional[str] = None
    text: Optional[str] = None
    error: Optional[str] = None
    items: list = Field(default_factory=list)
