from __future__ import annotations
from typing import Optional
from ..config import settings

async def send_email(to_email: str, subject: str, html: str, text: str) -> None:
    if not (settings.acs_email_conn and settings.acs_email_from):
        raise RuntimeError("Email not configured. Set ACS_EMAIL_CONNECTION_STRING and ACS_EMAIL_FROM.")
    from azure.communication.email import EmailClient

    client = EmailClient.from_connection_string(settings.acs_email_conn)
    message = {
        "senderAddress": settings.acs_email_from,
        "recipients": {"to": [{"address": to_email}]},
        "content": {
            "subject": subject,
            "plainText": text,
            "html": html,
        },
    }
    poller = client.begin_send(message)
    result = poller.result()
    # result contains operation metadata; you can log it if needed.
