from __future__ import annotations
import os
from typing import Optional
from pydantic import BaseModel

class Settings(BaseModel):
    storage_backend: str = os.getenv("STORAGE_BACKEND", "memory")

    cosmos_endpoint: Optional[str] = os.getenv("COSMOS_ENDPOINT") or None
    cosmos_key: Optional[str] = os.getenv("COSMOS_KEY") or None
    cosmos_database: str = os.getenv("COSMOS_DATABASE", "newsletter")
    c_users: str = os.getenv("COSMOS_CONTAINER_USERS", "users")
    c_subs: str = os.getenv("COSMOS_CONTAINER_SUBSCRIPTIONS", "subscriptions")
    c_runs: str = os.getenv("COSMOS_CONTAINER_RUNS", "runs")

    api_base_url: str = os.getenv("API_BASE_URL", "http://localhost:8000")

    acs_email_conn: Optional[str] = os.getenv("ACS_EMAIL_CONNECTION_STRING") or None
    acs_email_from: Optional[str] = os.getenv("ACS_EMAIL_FROM") or None

settings = Settings()
