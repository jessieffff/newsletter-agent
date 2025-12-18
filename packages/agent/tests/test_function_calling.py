"""Unit tests for function calling implementation."""

import pytest
from unittest.mock import Mock, AsyncMock
from newsletter_agent.types import (
    CandidateForRanking,
    SelectedItemForDraft,
    RankAndSelectOutput,
    DraftNewsletterOutput
)
from newsletter_agent.tools import (
    validate_rank_and_select_output,
    validate_draft_newsletter_output, 
    enforce_max_per_domain,
    extract_domain
)


class TestValidationFunctions:
    """Test validation functions."""
    
    def test_validate_rank_and_select_output_valid(self):
        """Test valid rank_and_select output."""
        candidates = [
            CandidateForRanking(id="1", title="Title 1", url="https://example.com/1", source="example.com"),
            CandidateForRanking(id="2", title="Title 2", url="https://example.com/2", source="example.com")
        ]
        
        output = {
            "selected_ids": ["1", "2"],
            "reasons": {"1": "Relevant", "2": "Recent"}
        }
        
        is_valid, error = validate_rank_and_select_output(output, candidates, 2)
        assert is_valid
        assert error == ""
    
    def test_validate_rank_and_select_output_invalid_ids(self):
        """Test rank_and_select output with invalid IDs."""
        candidates = [
            CandidateForRanking(id="1", title="Title 1", url="https://example.com/1", source="example.com")
        ]
        
        output = {
            "selected_ids": ["1", "invalid_id"],
            "reasons": {}
        }
        
        is_valid, error = validate_rank_and_select_output(output, candidates, 2)
        assert not is_valid
        assert "invalid ids" in error
    
    def test_validate_rank_and_select_output_duplicates(self):
        """Test rank_and_select output with duplicate IDs."""
        candidates = [
            CandidateForRanking(id="1", title="Title 1", url="https://example.com/1", source="example.com")
        ]
        
        output = {
            "selected_ids": ["1", "1"],
            "reasons": {}
        }
        
        is_valid, error = validate_rank_and_select_output(output, candidates, 2)
        assert not is_valid
        assert "duplicates" in error

    def test_validate_draft_newsletter_output_valid(self):
        """Test valid draft_newsletter_items output."""
        items = [
            SelectedItemForDraft(
                id="item:0",
                title="Test Title",
                url="https://example.com/test",
                source="example.com"
            )
        ]
        
        output = {
            "subject": "Test Newsletter",
            "items": [{
                "id": "item:0",
                "title": "Test Title",
                "source": "example.com",
                "url": "https://example.com/test",
                "why_it_matters": "This is important.",
                "summary": "This is a summary."
            }]
        }
        
        is_valid, error = validate_draft_newsletter_output(output, items)
        assert is_valid
        assert error == ""
    
    def test_validate_draft_newsletter_output_url_mismatch(self):
        """Test draft_newsletter_items output with URL mismatch."""
        items = [
            SelectedItemForDraft(
                id="item:0", 
                title="Test Title",
                url="https://example.com/test",
                source="example.com"
            )
        ]
        
        output = {
            "subject": "Test Newsletter",
            "items": [{
                "id": "item:0",
                "title": "Test Title", 
                "source": "example.com",
                "url": "https://different.com/url",  # Wrong URL
                "why_it_matters": "This is important.",
                "summary": "This is a summary."
            }]
        }
        
        is_valid, error = validate_draft_newsletter_output(output, items)
        assert not is_valid
        assert "URL mismatch" in error


class TestDomainEnforcement:
    """Test domain enforcement logic."""
    
    def test_extract_domain(self):
        """Test domain extraction from URLs."""
        assert extract_domain("https://techcrunch.com/article") == "techcrunch.com"
        assert extract_domain("https://www.example.com/path") == "www.example.com"
        assert extract_domain("http://subdomain.site.org/page") == "subdomain.site.org"
    
    def test_enforce_max_per_domain(self):
        """Test max_per_domain enforcement."""
        candidates = [
            CandidateForRanking(id="1", title="Title 1", url="https://techcrunch.com/1", source="techcrunch.com"),
            CandidateForRanking(id="2", title="Title 2", url="https://techcrunch.com/2", source="techcrunch.com"),
            CandidateForRanking(id="3", title="Title 3", url="https://techcrunch.com/3", source="techcrunch.com"),
            CandidateForRanking(id="4", title="Title 4", url="https://venturebeat.com/1", source="venturebeat.com"),
        ]
        
        selected_ids = ["1", "2", "3", "4"]  # 3 from techcrunch, 1 from venturebeat
        
        result = enforce_max_per_domain(selected_ids, candidates, max_per_domain=2, target_count=4)
        
        # Count domains in result
        domain_counts = {}
        id_to_candidate = {c.id: c for c in candidates}
        
        for item_id in result:
            domain = extract_domain(id_to_candidate[item_id].url)
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        
        # Should have max 2 from techcrunch
        assert domain_counts.get("techcrunch.com", 0) <= 2
        assert domain_counts.get("venturebeat.com", 0) <= 2
        
        # Should still have 4 total items (or less if not enough candidates)
        assert len(result) <= 4


class TestPydanticModels:
    """Test Pydantic model validation."""
    
    def test_candidate_for_ranking_model(self):
        """Test CandidateForRanking model validation."""
        candidate = CandidateForRanking(
            id="test:1",
            title="Test Title",
            url="https://example.com/test",
            source="example.com",
            published_at="2024-12-16T10:00:00Z",
            snippet="Test snippet"
        )
        
        assert candidate.id == "test:1"
        assert candidate.title == "Test Title"
        assert candidate.url == "https://example.com/test"
    
    def test_rank_and_select_output_model(self):
        """Test RankAndSelectOutput model validation."""
        output = RankAndSelectOutput(
            selected_ids=["1", "2", "3"],
            reasons={"1": "Relevant", "2": "Recent", "3": "Popular"},
            rejected=[{"id": "4", "reason": "Off-topic"}]
        )
        
        assert len(output.selected_ids) == 3
        assert output.reasons["1"] == "Relevant"
        assert len(output.rejected) == 1
    
    def test_draft_newsletter_output_model(self):
        """Test DraftNewsletterOutput model validation."""
        output = DraftNewsletterOutput(
            subject="Test Newsletter Subject",
            items=[
                {
                    "id": "item:0",
                    "title": "Article Title",
                    "source": "example.com", 
                    "url": "https://example.com/article",
                    "why_it_matters": "This provides important insights.",
                    "summary": "This is a detailed summary of the article."
                }
            ]
        )
        
        assert output.subject == "Test Newsletter Subject"
        assert len(output.items) == 1
        assert output.items[0].id == "item:0"


if __name__ == "__main__":
    pytest.main([__file__])