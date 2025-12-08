from __future__ import annotations
import uuid, datetime
from typing import List, Optional
from .base import Storage
from ..models import User, Subscription, SubscriptionIn, NewsletterRun
from ..config import settings

# Minimal Cosmos implementation. In production, add partition keys + indexing policy + proper upserts.
from azure.cosmos.aio import CosmosClient

def _now() -> str:
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

class CosmosStorage(Storage):
    def __init__(self):
        if not (settings.cosmos_endpoint and settings.cosmos_key):
            raise RuntimeError("COSMOS_ENDPOINT and COSMOS_KEY must be set for cosmos backend.")
        self.client = CosmosClient(settings.cosmos_endpoint, credential=settings.cosmos_key)
        self.db_name = settings.cosmos_database
        self.c_users = settings.c_users
        self.c_subs = settings.c_subs
        self.c_runs = settings.c_runs

    async def _containers(self):
        db = self.client.get_database_client(self.db_name)
        return (
            db.get_container_client(self.c_users),
            db.get_container_client(self.c_subs),
            db.get_container_client(self.c_runs),
        )

    async def upsert_user(self, email: str) -> User:
        users, _, _ = await self._containers()
        q = "SELECT * FROM c WHERE LOWER(c.email) = @email"
        items = [i async for i in users.query_items(q, parameters=[{"name":"@email","value":email.lower()}], enable_cross_partition_query=True)]
        if items:
            return User(**items[0])
        uid = uuid.uuid4().hex[:24]
        doc = {"id": uid, "email": email}
        await users.upsert_item(doc)
        return User(**doc)

    async def list_subscriptions(self, user_id: str) -> List[Subscription]:
        _, subs, _ = await self._containers()
        q = "SELECT * FROM c WHERE c.user_id = @uid"
        items = [i async for i in subs.query_items(q, parameters=[{"name":"@uid","value":user_id}], enable_cross_partition_query=True)]
        return [Subscription(**i) for i in items]

    async def get_subscription(self, subscription_id: str) -> Subscription:
        _, subs, _ = await self._containers()
        item = await subs.read_item(item=subscription_id, partition_key=subscription_id)
        return Subscription(**item)

    async def upsert_subscription(self, user_id: str, subscription_id: Optional[str], data: SubscriptionIn) -> Subscription:
        _, subs, _ = await self._containers()
        sid = subscription_id or uuid.uuid4().hex[:24]
        doc = {"id": sid, "user_id": user_id, **data.model_dump()}
        await subs.upsert_item(doc)
        return Subscription(**doc)

    async def record_run(self, run: NewsletterRun) -> None:
        _, _, runs = await self._containers()
        await runs.upsert_item(run.model_dump())

    async def list_runs(self, subscription_id: str, limit: int = 50) -> List[NewsletterRun]:
        _, _, runs = await self._containers()
        q = "SELECT * FROM c WHERE c.subscription_id = @sid ORDER BY c.run_at DESC OFFSET 0 LIMIT @lim"
        params = [{"name":"@sid","value":subscription_id},{"name":"@lim","value":limit}]
        items = [i async for i in runs.query_items(q, parameters=params, enable_cross_partition_query=True)]
        return [NewsletterRun(**i) for i in items]

    async def due_subscriptions(self) -> List[Subscription]:
        # MVP: treat all enabled subscriptions as due. Replace with proper schedule calculation later.
        _, subs, _ = await self._containers()
        q = "SELECT * FROM c WHERE c.enabled = true"
        items = [i async for i in subs.query_items(q, enable_cross_partition_query=True)]
        return [Subscription(**i) for i in items]
