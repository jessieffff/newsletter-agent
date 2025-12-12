"""Core types and data models for the newsletter agent."""

from __future__ import annotations
from typing import Literal, Optional, List, Dict, Any, TypedDict
from pydantic import BaseModel, Field, HttpUrl, field_validator, ValidationError
import re

Frequency = Literal["daily", "weekly", "custom_cron"]

# Validation constants
MAX_TOPIC_LENGTH = 200
MAX_TONE_LENGTH = 100
ALLOWED_TONES = [
    "concise, professional",
    "friendly, casual",
    "technical, detailed",
    "brief, conversational"
]

# Common prompt injection patterns to detect
PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions?",
    r"you\s+are\s+(now\s+)?(chatgpt|gpt|claude|an?\s+ai|a\s+large\s+language\s+model)",
    r"system\s*:",
    r"assistant\s*:",
    r"forget\s+(all\s+)?previous",
    r"new\s+instructions?",
    r"disregard\s+(all\s+)?above",
]

def contains_prompt_injection(text: str) -> bool:
    """Check if text contains obvious LLM control phrases."""
    if not text:
        return False
    text_lower = text.lower()
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    return False

def sanitize_article_text(text: str, max_length: int = 5000) -> str:
    """
    Sanitize article text before sending to LLM.
    - Removes or neutralizes prompt injection phrases
    - Truncates overly long text
    - Returns safe version of the text
    """
    if not text:
        return ""
    
    # Truncate to max length
    sanitized = text[:max_length]
    
    # Replace prompt injection patterns with safe alternatives
    for pattern in PROMPT_INJECTION_PATTERNS:
        sanitized = re.sub(pattern, "[REMOVED]", sanitized, flags=re.IGNORECASE)
    
    # Neutralize common control tokens
    sanitized = sanitized.replace("system:", "[SYSTEM]")
    sanitized = sanitized.replace("assistant:", "[ASSISTANT]")
    sanitized = sanitized.replace("user:", "[USER]")
    
    return sanitized

class SourceSpec(BaseModel):
    kind: Literal["rss", "nyt", "x", "domain"]
    value: str  # e.g. RSS URL, "nytimes", "@some_account", "theverge.com"

class Error(BaseModel):
    """Structured error type for tracking failures across the workflow."""
    source: Literal["rss", "nyt", "x", "foundry", "llm", "email", "validation", "system"]
    code: str  # e.g. "network_error", "invalid_response", "parse_failure"
    message: str
    details: Optional[Dict[str, Any]] = Field(default_factory=dict)

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
    require_approval: bool = False  # If True, newsletter is generated but not sent automatically

    @field_validator('topics')
    @classmethod
    def validate_topics(cls, v: List[str]) -> List[str]:
        """Validate topics list."""
        for topic in v:
            if len(topic) > MAX_TOPIC_LENGTH:
                raise ValueError(f"Topic exceeds maximum length of {MAX_TOPIC_LENGTH} characters")
            if contains_prompt_injection(topic):
                raise ValueError("Topic contains prohibited control phrases")
        return v

    @field_validator('tone')
    @classmethod
    def validate_tone(cls, v: str) -> str:
        """Validate tone field."""
        if len(v) > MAX_TONE_LENGTH:
            raise ValueError(f"Tone exceeds maximum length of {MAX_TONE_LENGTH} characters")
        if v not in ALLOWED_TONES:
            raise ValueError(f"Tone must be one of: {', '.join(ALLOWED_TONES)}")
        if contains_prompt_injection(v):
            raise ValueError("Tone contains prohibited control phrases")
        return v

    @field_validator('item_count')
    @classmethod
    def validate_item_count(cls, v: int) -> int:
        """Validate item count is within reasonable bounds."""
        if v < 1 or v > 50:
            raise ValueError("Item count must be between 1 and 50")
        return v

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


class AgentState(TypedDict, total=False):
    """State passed between workflow nodes."""
    subscription: Subscription
    candidates: List[Candidate]
    selected: List[SelectedItem]
    newsletter: Newsletter
    errors: List[Error]
    node_execution_count: int
    external_search_count: int
    status: Literal["draft", "approved", "sent", "failed"]  # Workflow status
