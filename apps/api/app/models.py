from __future__ import annotations
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator, EmailStr
import re

class UserIn(BaseModel):
    email: EmailStr

class User(BaseModel):
    id: str
    email: str

class SourceSpec(BaseModel):
    kind: Literal["rss", "nyt", "x", "domain"]
    value: str
    
    @field_validator('value')
    @classmethod
    def validate_value(cls, v: str, info) -> str:
        # Strip whitespace first
        v = v.strip() if v else v
        
        if not v:
            raise ValueError(f"{info.field_name} cannot be empty")
        
        # Validate RSS URL format
        if info.data.get('kind') == 'rss':
            url_pattern = re.compile(
                r'^https?://'  # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
                r'localhost|'  # localhost...
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                r'(?::\d+)?'  # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            if not url_pattern.match(v):
                raise ValueError(f"Invalid RSS URL format: {v}")
        
        return v

class SubscriptionIn(BaseModel):
    topics: List[str] = Field(default_factory=list)
    sources: List[SourceSpec] = Field(default_factory=list)
    frequency: Literal["daily", "weekly", "custom_cron"] = "daily"
    cron: Optional[str] = None
    item_count: int = 8
    tone: str = "concise, professional"
    enabled: bool = True
    
    @field_validator('topics')
    @classmethod
    def validate_topics(cls, v: List[str]) -> List[str]:
        if not v or len(v) == 0:
            raise ValueError("At least one topic is required")
        # Strip whitespace and filter empty strings
        topics = [t.strip() for t in v if t.strip()]
        if not topics:
            raise ValueError("At least one non-empty topic is required")
        return topics
    
    @field_validator('item_count')
    @classmethod
    def validate_item_count(cls, v: int) -> int:
        if v < 1 or v > 50:
            raise ValueError("item_count must be between 1 and 50")
        return v

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
