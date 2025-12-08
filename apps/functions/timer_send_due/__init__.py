import os
import logging
import azure.functions as func
import httpx
from dotenv import load_dotenv

load_dotenv()

def main(mytimer: func.TimerRequest) -> None:
    api_base = os.environ.get("API_BASE_URL", "http://localhost:8000").rstrip("/")
    user_email = os.environ.get("DEFAULT_NEWSLETTER_EMAIL", "demo@example.com")

    logging.info("Timer triggered. Calling send-due...")
    try:
        with httpx.Client(timeout=60) as client:
            r = client.post(f"{api_base}/v1/runs/send-due", params={"user_email": user_email})
            r.raise_for_status()
            logging.info("send-due result: %s", r.text[:500])
    except Exception as e:
        logging.exception("send-due failed: %s", e)
