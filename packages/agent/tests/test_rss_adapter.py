"""
Unit tests for RSS adapter.
"""

import pytest
from unittest.mock import patch, MagicMock
from newsletter_agent.mcp_like.adapters import fetch_rss_items
from newsletter_agent.mcp_like.errors import InvalidInputError


class TestRSSAdapter:
    """Tests for RSS adapter."""
    
    def test_fetch_rss_items_validates_input(self):
        """Test that fetch_rss_items validates input."""
        # Missing feed_url
        with pytest.raises(InvalidInputError, match="feed_url"):
            fetch_rss_items({})
        
        # Invalid max_items
        with pytest.raises(InvalidInputError, match="max_items"):
            fetch_rss_items({"feed_url": "https://example.com/feed", "max_items": 0})
        
        with pytest.raises(InvalidInputError, match="max_items"):
            fetch_rss_items({"feed_url": "https://example.com/feed", "max_items": 200})
    
    @patch("newsletter_agent.mcp_like.adapters.rss_adapter.fetch_and_parse_rss")
    def test_fetch_rss_items_returns_normalized_items(self, mock_fetch):
        """Test that fetch_rss_items normalizes RSS entries."""
        # Mock RSS entries
        mock_fetch.return_value = [
            {
                "link": "https://example.com/article1",
                "title": "Article 1",
                "published": "2025-01-01T00:00:00Z",
                "summary": "Summary of article 1",
                "id": "article-1",
            },
            {
                "link": "https://example.com/article2",
                "title": "Article 2",
                "updated": "2025-01-02T00:00:00Z",
                "description": "Description of article 2",
            },
        ]
        
        result = fetch_rss_items({"feed_url": "https://example.com/feed"})
        
        assert len(result.items) == 2
        assert result.items[0].title == "Article 1"
        assert result.items[0].url == "https://example.com/article1"
        assert result.items[0].published_at is not None
        assert result.items[0].snippet is not None
        assert result.items[0].source.startswith("rss:")
        assert result.items[0].raw_id == "article-1"
        
        assert result.items[1].title == "Article 2"
        assert result.items[1].url == "https://example.com/article2"
    
    @patch("newsletter_agent.mcp_like.adapters.rss_adapter.fetch_and_parse_rss")
    def test_fetch_rss_items_skips_invalid_entries(self, mock_fetch):
        """Test that fetch_rss_items skips invalid entries."""
        # Mock RSS entries with some invalid ones
        mock_fetch.return_value = [
            {
                "link": "https://example.com/article1",
                "title": "Article 1",
            },
            {
                # Missing link
                "title": "Article 2",
            },
            {
                # Missing title
                "link": "https://example.com/article3",
            },
            {
                "link": "https://example.com/article4",
                "title": "Article 4",
            },
        ]
        
        result = fetch_rss_items({"feed_url": "https://example.com/feed"})
        
        # Should only return valid entries
        assert len(result.items) == 2
        assert result.items[0].title == "Article 1"
        assert result.items[1].title == "Article 4"
        
        # Should have warnings about skipped entries
        assert len(result.warnings) > 0
    
    @patch("newsletter_agent.mcp_like.adapters.rss_adapter.fetch_and_parse_rss")
    def test_fetch_rss_items_cleans_snippets(self, mock_fetch):
        """Test that fetch_rss_items cleans HTML from snippets."""
        mock_fetch.return_value = [
            {
                "link": "https://example.com/article1",
                "title": "Article 1",
                "summary": "<p>HTML <b>snippet</b> with tags</p>",
            },
        ]
        
        result = fetch_rss_items({"feed_url": "https://example.com/feed"})
        
        assert len(result.items) == 1
        assert "<p>" not in result.items[0].snippet
        assert "<b>" not in result.items[0].snippet
        assert "HTML snippet with tags" in result.items[0].snippet
    
    @patch("newsletter_agent.mcp_like.adapters.rss_adapter.fetch_and_parse_rss")
    def test_fetch_rss_items_respects_max_items(self, mock_fetch):
        """Test that fetch_rss_items respects max_items limit."""
        # Return 50 entries
        mock_fetch.return_value = [
            {
                "link": f"https://example.com/article{i}",
                "title": f"Article {i}",
            }
            for i in range(50)
        ]
        
        result = fetch_rss_items({"feed_url": "https://example.com/feed", "max_items": 10})
        
        # Should only return 10 items
        assert len(result.items) == 10
    
    def test_fetch_rss_items_validates_urls(self):
        """Test that fetch_rss_items validates URLs."""
        # Invalid URL scheme
        with pytest.raises(InvalidInputError):
            fetch_rss_items({"feed_url": "ftp://example.com/feed"})
    
    @patch("newsletter_agent.mcp_like.adapters.rss_adapter.fetch_and_parse_rss")
    def test_fetch_rss_items_filters_unsafe_urls(self, mock_fetch):
        """Test that fetch_rss_items filters out unsafe URLs."""
        mock_fetch.return_value = [
            {
                "link": "https://example.com/article1",
                "title": "Safe Article",
            },
            {
                "link": "https://192.168.1.1/article2",
                "title": "Unsafe Article (private IP)",
            },
            {
                "link": "https://localhost/article3",
                "title": "Unsafe Article (localhost)",
            },
        ]
        
        result = fetch_rss_items({"feed_url": "https://example.com/feed"})
        
        # Should only return the safe article
        assert len(result.items) == 1
        assert result.items[0].title == "Safe Article"
        
        # Should have warnings about filtered URLs
        assert len(result.warnings) > 0
