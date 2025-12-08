from __future__ import annotations
import uuid, datetime
from typing import Any
from ..models import Subscription, NewsletterRun
from ..storage.base import Storage
from ..services.emailer import send_email

from newsletter_agent.types import Subscription as AgentSubscription, SourceSpec
from newsletter_agent.workflow import run_once

def _now() -> str:
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def _to_agent_sub(sub: Subscription) -> AgentSubscription:
    return AgentSubscription(
        id=sub.id,
        user_id=sub.user_id,
        topics=sub.topics,
        sources=[SourceSpec(kind=s.kind, value=s.value) for s in sub.sources],
        frequency=sub.frequency,
        cron=sub.cron,
        item_count=sub.item_count,
        tone=sub.tone,
        enabled=sub.enabled,
    )

async def run_and_email(storage: Storage, sub: Subscription, user_email: str) -> NewsletterRun:
    run_id = uuid.uuid4().hex[:24]
    run = NewsletterRun(
        id=run_id,
        subscription_id=sub.id,
        run_at=_now(),
        status="drafted",
    )
    try:
        newsletter = await run_once(_to_agent_sub(sub))
        run.subject = newsletter.subject
        run.html = newsletter.html
        run.text = newsletter.text
        run.items = [it.model_dump() for it in newsletter.items]
        await send_email(user_email, newsletter.subject, newsletter.html, newsletter.text)
        run.status = "sent"
    except Exception as e:
        run.status = "failed"
        run.error = str(e)
    await storage.record_run(run)
    return run
