from __future__ import annotations
import uuid, datetime
from typing import Dict, List, Optional
from .base import Storage
from ..models import User, Subscription, SubscriptionIn, NewsletterRun

def _now() -> str:
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

class MemoryStorage(Storage):
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.subs: Dict[str, Subscription] = {}
        self.runs: Dict[str, List[NewsletterRun]] = {}

    async def upsert_user(self, email: str) -> User:
        for u in self.users.values():
            if u.email.lower() == email.lower():
                return u
        uid = uuid.uuid4().hex[:24]
        u = User(id=uid, email=email)
        self.users[uid] = u
        return u

    async def list_subscriptions(self, user_id: str) -> List[Subscription]:
        return [s for s in self.subs.values() if s.user_id == user_id]

    async def get_subscription(self, subscription_id: str) -> Subscription:
        return self.subs[subscription_id]

    async def upsert_subscription(self, user_id: str, subscription_id: Optional[str], data: SubscriptionIn) -> Subscription:
        sid = subscription_id or uuid.uuid4().hex[:24]
        sub = Subscription(id=sid, user_id=user_id, **data.model_dump())
        self.subs[sid] = sub
        return sub

    async def record_run(self, run: NewsletterRun) -> None:
        self.runs.setdefault(run.subscription_id, []).insert(0, run)

    async def list_runs(self, subscription_id: str, limit: int = 50) -> List[NewsletterRun]:
        return (self.runs.get(subscription_id) or [])[:limit]

    async def due_subscriptions(self) -> List[Subscription]:
        # MVP: treat all enabled subscriptions as "due"
        return [s for s in self.subs.values() if s.enabled]
