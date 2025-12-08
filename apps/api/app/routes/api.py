from __future__ import annotations
from fastapi import APIRouter, HTTPException
from ..models import UserIn, User, SubscriptionIn, Subscription, NewsletterRun
from ..main import get_storage
from ..services.agent_runner import run_and_email

router = APIRouter()

@router.post("/users", response_model=User)
async def upsert_user(payload: UserIn):
    storage = get_storage()
    return await storage.upsert_user(payload.email)

@router.get("/users/{user_id}/subscriptions", response_model=list[Subscription])
async def list_subscriptions(user_id: str):
    storage = get_storage()
    return await storage.list_subscriptions(user_id)

@router.post("/users/{user_id}/subscriptions", response_model=Subscription)
async def create_subscription(user_id: str, payload: SubscriptionIn):
    storage = get_storage()
    return await storage.upsert_subscription(user_id, None, payload)

@router.put("/users/{user_id}/subscriptions/{subscription_id}", response_model=Subscription)
async def update_subscription(user_id: str, subscription_id: str, payload: SubscriptionIn):
    storage = get_storage()
    return await storage.upsert_subscription(user_id, subscription_id, payload)

@router.get("/subscriptions/{subscription_id}/runs", response_model=list[NewsletterRun])
async def list_runs(subscription_id: str, limit: int = 50):
    storage = get_storage()
    return await storage.list_runs(subscription_id, limit=limit)

@router.post("/subscriptions/{subscription_id}/run", response_model=NewsletterRun)
async def run_now(subscription_id: str, user_email: str):
    storage = get_storage()
    sub = await storage.get_subscription(subscription_id)
    return await run_and_email(storage, sub, user_email)

@router.post("/runs/send-due")
async def send_due(user_email: str):
    storage = get_storage()
    subs = await storage.due_subscriptions()
    results = []
    for s in subs:
        results.append(await run_and_email(storage, s, user_email))
    return {"count": len(results), "runs": [r.model_dump() for r in results]}
