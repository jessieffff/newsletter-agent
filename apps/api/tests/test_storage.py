"""Tests for storage layer (MemoryStorage)."""
import pytest
from app.storage.memory import MemoryStorage
from app.models import SubscriptionIn

@pytest.mark.asyncio
class TestMemoryStorage:
    async def test_upsert_user_creates_new_user(self):
        storage = MemoryStorage()
        user = await storage.upsert_user("test@example.com")
        
        assert user.email == "test@example.com"
        assert user.id is not None
        assert len(user.id) == 24
    
    async def test_upsert_user_returns_existing_user(self):
        storage = MemoryStorage()
        user1 = await storage.upsert_user("test@example.com")
        user2 = await storage.upsert_user("test@example.com")
        
        assert user1.id == user2.id
        assert user1.email == user2.email
    
    async def test_upsert_user_case_insensitive(self):
        storage = MemoryStorage()
        user1 = await storage.upsert_user("test@example.com")
        user2 = await storage.upsert_user("TEST@EXAMPLE.COM")
        
        assert user1.id == user2.id
    
    async def test_create_subscription(self):
        storage = MemoryStorage()
        user = await storage.upsert_user("test@example.com")
        
        sub_data = SubscriptionIn(
            topics=["AI", "Cloud"],
            sources=[{"kind": "rss", "value": "https://example.com/feed.xml"}],
            frequency="daily",
            item_count=10
        )
        
        subscription = await storage.upsert_subscription(user.id, None, sub_data)
        
        assert subscription.id is not None
        assert subscription.user_id == user.id
        assert subscription.topics == ["AI", "Cloud"]
        assert subscription.frequency == "daily"
        assert subscription.item_count == 10
    
    async def test_update_subscription(self):
        storage = MemoryStorage()
        user = await storage.upsert_user("test@example.com")
        
        # Create subscription
        sub_data = SubscriptionIn(
            topics=["AI"],
            frequency="daily",
            item_count=5
        )
        subscription = await storage.upsert_subscription(user.id, None, sub_data)
        
        # Update subscription
        updated_data = SubscriptionIn(
            topics=["AI", "Cloud", "DevOps"],
            frequency="weekly",
            item_count=15
        )
        updated_sub = await storage.upsert_subscription(user.id, subscription.id, updated_data)
        
        assert updated_sub.id == subscription.id
        assert updated_sub.topics == ["AI", "Cloud", "DevOps"]
        assert updated_sub.frequency == "weekly"
        assert updated_sub.item_count == 15
    
    async def test_list_subscriptions(self):
        storage = MemoryStorage()
        user1 = await storage.upsert_user("user1@example.com")
        user2 = await storage.upsert_user("user2@example.com")
        
        # Create subscriptions for user1
        sub_data1 = SubscriptionIn(topics=["AI"], frequency="daily")
        sub_data2 = SubscriptionIn(topics=["Cloud"], frequency="weekly")
        await storage.upsert_subscription(user1.id, None, sub_data1)
        await storage.upsert_subscription(user1.id, None, sub_data2)
        
        # Create subscription for user2
        sub_data3 = SubscriptionIn(topics=["DevOps"], frequency="daily")
        await storage.upsert_subscription(user2.id, None, sub_data3)
        
        # List subscriptions for user1
        user1_subs = await storage.list_subscriptions(user1.id)
        assert len(user1_subs) == 2
        
        # List subscriptions for user2
        user2_subs = await storage.list_subscriptions(user2.id)
        assert len(user2_subs) == 1
    
    async def test_get_subscription(self):
        storage = MemoryStorage()
        user = await storage.upsert_user("test@example.com")
        
        sub_data = SubscriptionIn(topics=["AI"], frequency="daily")
        created_sub = await storage.upsert_subscription(user.id, None, sub_data)
        
        retrieved_sub = await storage.get_subscription(created_sub.id)
        
        assert retrieved_sub.id == created_sub.id
        assert retrieved_sub.user_id == created_sub.user_id
        assert retrieved_sub.topics == created_sub.topics
    
    async def test_due_subscriptions(self):
        storage = MemoryStorage()
        user = await storage.upsert_user("test@example.com")
        
        # Create enabled subscription
        enabled_data = SubscriptionIn(topics=["AI"], enabled=True)
        await storage.upsert_subscription(user.id, None, enabled_data)
        
        # Create disabled subscription
        disabled_data = SubscriptionIn(topics=["Cloud"], enabled=False)
        await storage.upsert_subscription(user.id, None, disabled_data)
        
        due_subs = await storage.due_subscriptions()
        
        # Only enabled subscriptions should be due
        assert len(due_subs) == 1
        assert due_subs[0].enabled is True
        assert due_subs[0].topics == ["AI"]
    
    async def test_list_subscriptions_empty(self):
        storage = MemoryStorage()
        user = await storage.upsert_user("test@example.com")
        
        subs = await storage.list_subscriptions(user.id)
        assert subs == []
