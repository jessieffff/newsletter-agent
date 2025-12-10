"""Tests for Pydantic models and validation."""
import pytest
from pydantic import ValidationError
from app.models import UserIn, SourceSpec, SubscriptionIn

class TestUserIn:
    def test_valid_email(self):
        user = UserIn(email="test@example.com")
        assert user.email == "test@example.com"
    
    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            UserIn(email="not-an-email")
    
    def test_empty_email(self):
        with pytest.raises(ValidationError):
            UserIn(email="")

class TestSourceSpec:
    def test_valid_rss_url(self):
        source = SourceSpec(kind="rss", value="https://example.com/feed.xml")
        assert source.kind == "rss"
        assert source.value == "https://example.com/feed.xml"
    
    def test_invalid_rss_url(self):
        with pytest.raises(ValidationError, match="Invalid RSS URL format"):
            SourceSpec(kind="rss", value="not-a-url")
    
    def test_rss_url_without_protocol(self):
        with pytest.raises(ValidationError, match="Invalid RSS URL format"):
            SourceSpec(kind="rss", value="example.com/feed.xml")
    
    def test_empty_value(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            SourceSpec(kind="rss", value="")
    
    def test_whitespace_trimming(self):
        source = SourceSpec(kind="rss", value="  https://example.com/feed.xml  ")
        assert source.value == "https://example.com/feed.xml"
    
    def test_nyt_source(self):
        source = SourceSpec(kind="nyt", value="technology")
        assert source.kind == "nyt"
        assert source.value == "technology"
    
    def test_x_source(self):
        source = SourceSpec(kind="x", value="@elonmusk")
        assert source.kind == "x"
        assert source.value == "@elonmusk"
    
    def test_domain_source(self):
        source = SourceSpec(kind="domain", value="techcrunch.com")
        assert source.kind == "domain"
        assert source.value == "techcrunch.com"

class TestSubscriptionIn:
    def test_valid_subscription(self):
        sub = SubscriptionIn(
            topics=["AI", "Cloud"],
            sources=[{"kind": "rss", "value": "https://example.com/feed.xml"}],
            frequency="daily",
            item_count=10,
            tone="professional"
        )
        assert len(sub.topics) == 2
        assert sub.frequency == "daily"
        assert sub.item_count == 10
    
    def test_empty_topics(self):
        with pytest.raises(ValidationError, match="At least one topic is required"):
            SubscriptionIn(
                topics=[],
                sources=[{"kind": "rss", "value": "https://example.com/feed.xml"}],
                frequency="daily"
            )
    
    def test_topics_with_only_whitespace(self):
        with pytest.raises(ValidationError, match="At least one non-empty topic is required"):
            SubscriptionIn(
                topics=["  ", "   "],
                sources=[{"kind": "rss", "value": "https://example.com/feed.xml"}],
                frequency="daily"
            )
    
    def test_topics_whitespace_trimming(self):
        sub = SubscriptionIn(
            topics=["  AI  ", " Cloud Computing  "],
            sources=[{"kind": "rss", "value": "https://example.com/feed.xml"}],
            frequency="daily"
        )
        assert sub.topics == ["AI", "Cloud Computing"]
    
    def test_item_count_too_low(self):
        with pytest.raises(ValidationError, match="item_count must be between 1 and 50"):
            SubscriptionIn(
                topics=["AI"],
                sources=[{"kind": "rss", "value": "https://example.com/feed.xml"}],
                item_count=0
            )
    
    def test_item_count_too_high(self):
        with pytest.raises(ValidationError, match="item_count must be between 1 and 50"):
            SubscriptionIn(
                topics=["AI"],
                sources=[{"kind": "rss", "value": "https://example.com/feed.xml"}],
                item_count=51
            )
    
    def test_item_count_boundary_values(self):
        # Test minimum
        sub1 = SubscriptionIn(
            topics=["AI"],
            sources=[{"kind": "rss", "value": "https://example.com/feed.xml"}],
            item_count=1
        )
        assert sub1.item_count == 1
        
        # Test maximum
        sub2 = SubscriptionIn(
            topics=["AI"],
            sources=[{"kind": "rss", "value": "https://example.com/feed.xml"}],
            item_count=50
        )
        assert sub2.item_count == 50
    
    def test_default_values(self):
        sub = SubscriptionIn(topics=["AI"])
        assert sub.sources == []
        assert sub.frequency == "daily"
        assert sub.cron is None
        assert sub.item_count == 8
        assert sub.tone == "concise, professional"
        assert sub.enabled is True
    
    def test_frequency_options(self):
        # Test daily
        sub1 = SubscriptionIn(topics=["AI"], frequency="daily")
        assert sub1.frequency == "daily"
        
        # Test weekly
        sub2 = SubscriptionIn(topics=["AI"], frequency="weekly")
        assert sub2.frequency == "weekly"
        
        # Test custom_cron
        sub3 = SubscriptionIn(topics=["AI"], frequency="custom_cron", cron="0 9 * * *")
        assert sub3.frequency == "custom_cron"
        assert sub3.cron == "0 9 * * *"
    
    def test_invalid_frequency(self):
        with pytest.raises(ValidationError):
            SubscriptionIn(topics=["AI"], frequency="hourly")
