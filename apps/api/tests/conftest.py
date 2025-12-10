"""Pytest configuration and fixtures for API tests."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.storage.memory import MemoryStorage
from app.dependencies import get_storage

@pytest.fixture
def storage():
    """Create a fresh in-memory storage for each test."""
    return MemoryStorage()

@pytest.fixture
def client(storage):
    """Create a test client with isolated storage."""
    app.dependency_overrides[get_storage] = lambda: storage
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def sample_user(client):
    """Create a sample user for testing."""
    response = client.post("/v1/users", json={"email": "test@example.com"})
    assert response.status_code == 200
    return response.json()

@pytest.fixture
def sample_subscription_payload():
    """Sample subscription payload for testing."""
    return {
        "topics": ["AI", "Cloud Computing"],
        "sources": [
            {"kind": "rss", "value": "https://www.theverge.com/rss/index.xml"}
        ],
        "frequency": "daily",
        "item_count": 8,
        "tone": "concise, professional",
        "enabled": True
    }
