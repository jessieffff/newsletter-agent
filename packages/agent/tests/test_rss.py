"""
Unit tests for RSS feed fetcher.
Tests URL canonicalization, deduplication, and error handling.
"""

import pytest
from newsletter_agent.tools.rss import (
    _canonicalize_url,
    _deduplicate_candidates,
    fetch_rss,
)
from newsletter_agent.types import Candidate


class TestCanonicalizeUrl:
    """Test URL canonicalization (tracking param removal)."""
    
    def test_removes_utm_parameters(self):
        url = "https://example.com/article?utm_source=twitter&utm_campaign=fall2024"
        canonical = _canonicalize_url(url)
        assert canonical == "https://example.com/article"
    
    def test_removes_fbclid(self):
        url = "https://example.com/page?fbclid=IwAR123456"
        canonical = _canonicalize_url(url)
        assert canonical == "https://example.com/page"
    
    def test_keeps_legitimate_params(self):
        url = "https://example.com/search?q=python&page=2"
        canonical = _canonicalize_url(url)
        assert "q=python" in canonical
        assert "page=2" in canonical
    
    def test_removes_fragment(self):
        url = "https://example.com/article#section-3"
        canonical = _canonicalize_url(url)
        assert "#" not in canonical
    
    def test_normalizes_trailing_slash(self):
        url1 = "https://example.com/article/"
        url2 = "https://example.com/article"
        assert _canonicalize_url(url1) == _canonicalize_url(url2)
    
    def test_handles_malformed_url_gracefully(self):
        url = "not-a-valid-url"
        # Should return original URL if parsing fails
        canonical = _canonicalize_url(url)
        assert canonical == url


class TestDeduplication:
    """Test candidate deduplication logic."""
    
    def test_removes_exact_duplicates(self):
        candidates = [
            Candidate(
                id="1",
                title="Article 1",
                url="https://example.com/article",
                source="test",
            ),
            Candidate(
                id="2",
                title="Article 1 (duplicate)",
                url="https://example.com/article",
                source="test",
            ),
        ]
        result = _deduplicate_candidates(candidates)
        assert len(result) == 1
    
    def test_removes_duplicates_with_tracking_params(self):
        candidates = [
            Candidate(
                id="1",
                title="Article 1",
                url="https://example.com/article",
                source="test",
            ),
            Candidate(
                id="2",
                title="Article 1 (with tracking)",
                url="https://example.com/article?utm_source=twitter",
                source="test",
            ),
        ]
        result = _deduplicate_candidates(candidates)
        assert len(result) == 1
    
    def test_keeps_most_recent_duplicate(self):
        candidates = [
            Candidate(
                id="1",
                title="Older",
                url="https://example.com/article",
                source="test",
                published_at="2024-01-01T10:00:00Z",
            ),
            Candidate(
                id="2",
                title="Newer",
                url="https://example.com/article",
                source="test",
                published_at="2024-01-02T10:00:00Z",
            ),
        ]
        result = _deduplicate_candidates(candidates)
        assert len(result) == 1
        assert result[0].title == "Newer"
    
    def test_prefers_entries_with_dates(self):
        candidates = [
            Candidate(
                id="1",
                title="No date",
                url="https://example.com/article",
                source="test",
            ),
            Candidate(
                id="2",
                title="Has date",
                url="https://example.com/article",
                source="test",
                published_at="2024-01-01T10:00:00Z",
            ),
        ]
        result = _deduplicate_candidates(candidates)
        assert len(result) == 1
        assert result[0].title == "Has date"


class TestFetchRss:
    """Test the main fetch_rss function."""
    
    def test_returns_empty_list_for_invalid_url(self):
        """Should gracefully handle invalid URLs."""
        result = fetch_rss("not-a-valid-url")
        assert result == []
    
    def test_returns_empty_list_for_404(self):
        """Should gracefully handle non-existent feeds."""
        result = fetch_rss("https://example.com/nonexistent-feed.xml")
        assert result == []
    
    def test_applies_limit(self):
        """Should respect the limit parameter."""
        # Using a real feed for integration testing
        result = fetch_rss(
            "https://feeds.arstechnica.com/arstechnica/index",
            limit=5
        )
        # Might get fewer than 5 if feed has fewer items or network issues
        assert len(result) <= 5
    
    def test_adds_topic_hint(self):
        """Should add topic_hint to all candidates."""
        result = fetch_rss(
            "https://feeds.arstechnica.com/arstechnica/index",
            topic_hint="technology",
            limit=3
        )
        if result:  # Only check if we got results
            for candidate in result:
                assert "technology" in candidate.topic_tags
    
    def test_validates_required_fields(self):
        """All candidates should have required fields."""
        result = fetch_rss(
            "https://feeds.arstechnica.com/arstechnica/index",
            limit=5
        )
        if result:  # Only check if we got results
            for candidate in result:
                assert candidate.id
                assert candidate.title
                assert candidate.url
                assert candidate.source
    
    def test_no_duplicate_urls_in_result(self):
        """Result should have no duplicate URLs."""
        result = fetch_rss(
            "https://feeds.arstechnica.com/arstechnica/index",
            limit=20
        )
        if result:  # Only check if we got results
            urls = [str(c.url) for c in result]
            assert len(urls) == len(set(urls)), "Found duplicate URLs in result"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
