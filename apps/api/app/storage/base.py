from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Optional
from ..models import User, Subscription, SubscriptionIn, NewsletterRun

class Storage(ABC):
    @abstractmethod
    async def upsert_user(self, email: str) -> User: ...

    @abstractmethod
    async def list_subscriptions(self, user_id: str) -> List[Subscription]: ...

    @abstractmethod
    async def get_subscription(self, subscription_id: str) -> Subscription: ...

    @abstractmethod
    async def upsert_subscription(self, user_id: str, subscription_id: Optional[str], data: SubscriptionIn) -> Subscription: ...

    @abstractmethod
    async def record_run(self, run: NewsletterRun) -> None: ...

    @abstractmethod
    async def list_runs(self, subscription_id: str, limit: int = 50) -> List[NewsletterRun]: ...

    @abstractmethod
    async def due_subscriptions(self) -> List[Subscription]: ...
