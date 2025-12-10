"""Tests for API endpoints."""
import pytest

class TestHealthEndpoint:
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "storage" in data

class TestUserEndpoints:
    def test_create_user(self, client):
        response = client.post("/v1/users", json={"email": "newuser@example.com"})
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert "id" in data
    
    def test_create_user_invalid_email(self, client):
        response = client.post("/v1/users", json={"email": "invalid-email"})
        assert response.status_code == 422
    
    def test_upsert_user_idempotent(self, client):
        # Create user twice with same email
        response1 = client.post("/v1/users", json={"email": "same@example.com"})
        response2 = client.post("/v1/users", json={"email": "same@example.com"})
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Should return same user ID
        assert response1.json()["id"] == response2.json()["id"]

class TestSubscriptionEndpoints:
    def test_create_subscription(self, client, sample_user, sample_subscription_payload):
        response = client.post(
            f"/v1/users/{sample_user['id']}/subscriptions",
            json=sample_subscription_payload
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert data["user_id"] == sample_user["id"]
        assert data["topics"] == sample_subscription_payload["topics"]
        assert data["frequency"] == sample_subscription_payload["frequency"]
        assert data["item_count"] == sample_subscription_payload["item_count"]
    
    def test_create_subscription_validates_topics(self, client, sample_user):
        payload = {
            "topics": [],  # Empty topics should fail
            "sources": [{"kind": "rss", "value": "https://example.com/feed.xml"}],
            "frequency": "daily"
        }
        response = client.post(
            f"/v1/users/{sample_user['id']}/subscriptions",
            json=payload
        )
        assert response.status_code == 422
    
    def test_create_subscription_validates_rss_url(self, client, sample_user):
        payload = {
            "topics": ["AI"],
            "sources": [{"kind": "rss", "value": "not-a-valid-url"}],
            "frequency": "daily"
        }
        response = client.post(
            f"/v1/users/{sample_user['id']}/subscriptions",
            json=payload
        )
        assert response.status_code == 422
    
    def test_create_subscription_validates_item_count(self, client, sample_user):
        payload = {
            "topics": ["AI"],
            "sources": [{"kind": "rss", "value": "https://example.com/feed.xml"}],
            "frequency": "daily",
            "item_count": 100  # Too high
        }
        response = client.post(
            f"/v1/users/{sample_user['id']}/subscriptions",
            json=payload
        )
        assert response.status_code == 422
    
    def test_list_subscriptions(self, client, sample_subscription_payload):
        # Create a fresh user for this test
        user_response = client.post("/v1/users", json={"email": "list_test@example.com"})
        sample_user = user_response.json()
        
        # Create two subscriptions
        client.post(
            f"/v1/users/{sample_user['id']}/subscriptions",
            json=sample_subscription_payload
        )
        
        payload2 = sample_subscription_payload.copy()
        payload2["topics"] = ["DevOps"]
        client.post(
            f"/v1/users/{sample_user['id']}/subscriptions",
            json=payload2
        )
        
        # List subscriptions
        response = client.get(f"/v1/users/{sample_user['id']}/subscriptions")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 2
        assert all("id" in sub for sub in data)
        assert all(sub["user_id"] == sample_user["id"] for sub in data)
    
    def test_list_subscriptions_empty(self, client):
        # Create a fresh user for this test
        user_response = client.post("/v1/users", json={"email": "empty_test@example.com"})
        sample_user = user_response.json()
        
        response = client.get(f"/v1/users/{sample_user['id']}/subscriptions")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_update_subscription(self, client, sample_user, sample_subscription_payload):
        # Create subscription
        create_response = client.post(
            f"/v1/users/{sample_user['id']}/subscriptions",
            json=sample_subscription_payload
        )
        subscription_id = create_response.json()["id"]
        
        # Update subscription
        updated_payload = sample_subscription_payload.copy()
        updated_payload["topics"] = ["AI", "Cloud", "DevOps"]
        updated_payload["frequency"] = "weekly"
        
        update_response = client.put(
            f"/v1/users/{sample_user['id']}/subscriptions/{subscription_id}",
            json=updated_payload
        )
        
        assert update_response.status_code == 200
        data = update_response.json()
        
        assert data["id"] == subscription_id
        assert data["topics"] == ["AI", "Cloud", "DevOps"]
        assert data["frequency"] == "weekly"
    
    def test_subscription_with_minimal_payload(self, client, sample_user):
        # Minimal valid payload (only topics required)
        payload = {"topics": ["AI"]}
        
        response = client.post(
            f"/v1/users/{sample_user['id']}/subscriptions",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check defaults are applied
        assert data["topics"] == ["AI"]
        assert data["frequency"] == "daily"
        assert data["item_count"] == 8
        assert data["tone"] == "concise, professional"
        assert data["enabled"] is True
        assert data["sources"] == []
    
    def test_subscription_with_multiple_sources(self, client, sample_user):
        payload = {
            "topics": ["Tech News"],
            "sources": [
                {"kind": "rss", "value": "https://techcrunch.com/feed/"},
                {"kind": "rss", "value": "https://www.theverge.com/rss/index.xml"},
                {"kind": "nyt", "value": "technology"}
            ],
            "frequency": "daily"
        }
        
        response = client.post(
            f"/v1/users/{sample_user['id']}/subscriptions",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["sources"]) == 3

class TestIntegrationFlow:
    def test_full_subscription_flow(self, client):
        """Test the complete flow: create user -> create subscription -> list -> update."""
        
        # 1. Create user
        user_response = client.post("/v1/users", json={"email": "flow@example.com"})
        assert user_response.status_code == 200
        user = user_response.json()
        
        # 2. Create subscription
        sub_payload = {
            "topics": ["AI", "Machine Learning"],
            "sources": [{"kind": "rss", "value": "https://example.com/feed.xml"}],
            "frequency": "daily",
            "item_count": 10
        }
        create_response = client.post(
            f"/v1/users/{user['id']}/subscriptions",
            json=sub_payload
        )
        assert create_response.status_code == 200
        subscription = create_response.json()
        
        # 3. List subscriptions
        list_response = client.get(f"/v1/users/{user['id']}/subscriptions")
        assert list_response.status_code == 200
        subscriptions = list_response.json()
        assert len(subscriptions) == 1
        assert subscriptions[0]["id"] == subscription["id"]
        
        # 4. Update subscription
        updated_payload = {
            "topics": ["AI", "Deep Learning", "NLP"],
            "sources": [{"kind": "rss", "value": "https://example.com/feed.xml"}],
            "frequency": "weekly",
            "item_count": 15
        }
        update_response = client.put(
            f"/v1/users/{user['id']}/subscriptions/{subscription['id']}",
            json=updated_payload
        )
        assert update_response.status_code == 200
        updated_sub = update_response.json()
        assert updated_sub["topics"] == ["AI", "Deep Learning", "NLP"]
        assert updated_sub["frequency"] == "weekly"
        assert updated_sub["item_count"] == 15
        
        # 5. Verify update persisted
        final_list = client.get(f"/v1/users/{user['id']}/subscriptions")
        assert len(final_list.json()) == 1
        assert final_list.json()[0]["frequency"] == "weekly"
