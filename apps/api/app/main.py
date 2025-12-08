from __future__ import annotations
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .config import settings
from .storage.memory import MemoryStorage
from .storage.cosmos import CosmosStorage
from .storage.base import Storage
from .routes.api import router as api_router

load_dotenv()

app = FastAPI(title="Newsletter Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_storage: Storage | None = None

def get_storage() -> Storage:
    global _storage
    if _storage is None:
        if settings.storage_backend == "cosmos":
            _storage = CosmosStorage()
        else:
            _storage = MemoryStorage()
    return _storage

@app.get("/health")
async def health():
    return {"ok": True, "storage": settings.storage_backend}

app.include_router(api_router, prefix="/v1")
