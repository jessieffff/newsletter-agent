from __future__ import annotations
import os
from .config import settings
from .storage.memory import MemoryStorage
from .storage.cosmos import CosmosStorage
from .storage.base import Storage

_storage: Storage | None = None

def get_storage() -> Storage:
    global _storage
    if _storage is None:
        if settings.storage_backend == "cosmos":
            _storage = CosmosStorage()
        else:
            _storage = MemoryStorage()
    return _storage
