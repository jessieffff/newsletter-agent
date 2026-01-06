"""
Unit tests for policy modules.
"""

import pytest
from newsletter_agent.mcp_like.policy import (
    normalize_url,
    validate_url,
    is_safe_url,
    sanitize_html,
    truncate_text,
    clean_snippet,
)
from newsletter_agent.mcp_like.errors import InvalidInputError


class TestURLPolicy:
    """Tests for URL validation and normalization."""
    
    def test_normalize_url_adds_scheme(self):
        """Test that normalize_url adds https:// if missing."""
        url = normalize_url("example.com")
        assert url == "https://example.com"
    
    def test_normalize_url_lowercases_domain(self):
        """Test that normalize_url lowercases domain."""
        url = normalize_url("https://EXAMPLE.COM/Path")
        assert url == "https://example.com/Path"
    
    def test_normalize_url_removes_default_ports(self):
        """Test that normalize_url removes default ports."""
        url1 = normalize_url("https://example.com:443/path")
        assert url1 == "https://example.com/path"
        
        url2 = normalize_url("http://example.com:80/path")
        assert url2 == "http://example.com/path"
    
    def test_normalize_url_removes_trailing_slash(self):
        """Test that normalize_url removes trailing slashes."""
        url = normalize_url("https://example.com/path/")
        assert url == "https://example.com/path"
    
    def test_normalize_url_keeps_root_slash(self):
        """Test that normalize_url keeps root slash."""
        url = normalize_url("https://example.com/")
        assert url == "https://example.com/"
    
    def test_normalize_url_removes_fragment(self):
        """Test that normalize_url removes fragments."""
        url = normalize_url("https://example.com/path#section")
        assert url == "https://example.com/path"
    
    def test_validate_url_accepts_https(self):
        """Test that validate_url accepts https URLs."""
        assert validate_url("https://example.com") is True
    
    def test_validate_url_accepts_http(self):
        """Test that validate_url accepts http URLs."""
        assert validate_url("http://example.com") is True
    
    def test_validate_url_rejects_invalid_scheme(self):
        """Test that validate_url rejects invalid schemes."""
        with pytest.raises(InvalidInputError, match="not allowed"):
            validate_url("ftp://example.com")
    
    def test_validate_url_requires_domain(self):
        """Test that validate_url requires a domain."""
        with pytest.raises(InvalidInputError, match="must have a domain"):
            validate_url("https://")
    
    def test_is_safe_url_accepts_public_domain(self):
        """Test that is_safe_url accepts public domains."""
        assert is_safe_url("https://example.com") is True
    
    def test_is_safe_url_rejects_localhost(self):
        """Test that is_safe_url rejects localhost."""
        with pytest.raises(InvalidInputError, match="localhost"):
            is_safe_url("https://localhost/path")
    
    def test_is_safe_url_rejects_private_ip(self):
        """Test that is_safe_url rejects private IPs."""
        with pytest.raises(InvalidInputError, match="private IP"):
            is_safe_url("https://192.168.1.1/path")
        
        with pytest.raises(InvalidInputError, match="private IP"):
            is_safe_url("https://10.0.0.1/path")
        
        with pytest.raises(InvalidInputError, match="private IP"):
            is_safe_url("https://172.16.0.1/path")
    
    def test_is_safe_url_rejects_127(self):
        """Test that is_safe_url rejects 127.x.x.x."""
        with pytest.raises(InvalidInputError, match="localhost"):
            is_safe_url("https://127.0.0.1/path")


class TestContentPolicy:
    """Tests for content sanitization."""
    
    def test_sanitize_html_removes_tags(self):
        """Test that sanitize_html removes HTML tags."""
        text = sanitize_html("<p>Hello <b>world</b></p>")
        assert text == "Hello world"
    
    def test_sanitize_html_decodes_entities(self):
        """Test that sanitize_html decodes HTML entities."""
        text = sanitize_html("&lt;div&gt; &amp; &quot;test&quot;")
        assert text == "<div> & \"test\""
    
    def test_sanitize_html_normalizes_whitespace(self):
        """Test that sanitize_html normalizes whitespace."""
        text = sanitize_html("Hello    \n\n   world")
        assert text == "Hello world"
    
    def test_sanitize_html_empty_string(self):
        """Test that sanitize_html handles empty strings."""
        assert sanitize_html("") == ""
        assert sanitize_html(None) == ""
    
    def test_truncate_text_no_truncation(self):
        """Test that truncate_text doesn't truncate short text."""
        text = truncate_text("Short text", max_length=100)
        assert text == "Short text"
    
    def test_truncate_text_truncates_long_text(self):
        """Test that truncate_text truncates long text."""
        long_text = "a" * 1000
        text = truncate_text(long_text, max_length=50)
        assert len(text) == 50
        assert text.endswith("...")
    
    def test_truncate_text_at_word_boundary(self):
        """Test that truncate_text tries to break at word boundaries."""
        text = truncate_text("The quick brown fox jumps over", max_length=20)
        assert text.endswith("...")
        assert not text.startswith("The quick brown f")  # Should break at word
    
    def test_clean_snippet_combines_operations(self):
        """Test that clean_snippet combines sanitization and truncation."""
        html = "<p>" + ("word " * 200) + "</p>"
        snippet = clean_snippet(html, max_length=100)
        
        assert snippet is not None
        assert len(snippet) <= 100
        assert "<p>" not in snippet
    
    def test_clean_snippet_returns_none_for_empty(self):
        """Test that clean_snippet returns None for empty input."""
        assert clean_snippet("") is None
        assert clean_snippet(None) is None
        assert clean_snippet("   ") is None
