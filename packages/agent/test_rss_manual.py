#!/usr/bin/env python3
"""
Manual test script for RSS feed fetcher.
Tests with real RSS feeds to verify:
- Successful parsing
- Deduplication
- Error handling with malformed feeds
"""

from src.newsletter_agent.tools.rss import fetch_rss

def test_feeds():
    """Test with 3-5 real RSS feeds"""
    
    test_feeds = [
        ("https://feeds.arstechnica.com/arstechnica/index", "tech"),
        ("https://www.wired.com/feed/rss", "tech"),
        ("https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml", "tech"),
        ("https://techcrunch.com/feed/", "tech"),
        ("https://www.theverge.com/rss/index.xml", "tech"),
    ]
    
    print("=" * 80)
    print("RSS FEED FETCHER TEST")
    print("=" * 80)
    
    for feed_url, topic in test_feeds:
        print(f"\n📡 Fetching: {feed_url}")
        print(f"   Topic: {topic}")
        print("-" * 80)
        
        try:
            candidates = fetch_rss(feed_url, topic_hint=topic, limit=10)
            
            if not candidates:
                print("⚠️  No items fetched (feed might be unavailable or malformed)")
                continue
            
            print(f"✅ Fetched {len(candidates)} items")
            
            # Check for duplicates
            urls = [str(c.url) for c in candidates]
            if len(urls) != len(set(urls)):
                print("❌ DUPLICATE URLs FOUND!")
            else:
                print("✅ No duplicate URLs")
            
            # Show first 3 items
            print("\n📰 Sample items:")
            for i, candidate in enumerate(candidates[:3], 1):
                print(f"\n  {i}. {candidate.title}")
                print(f"     URL: {candidate.url}")
                print(f"     Source: {candidate.source}")
                print(f"     Published: {candidate.published_at or 'N/A'}")
                if candidate.snippet:
                    snippet_preview = candidate.snippet[:100] + "..." if len(candidate.snippet) > 100 else candidate.snippet
                    print(f"     Snippet: {snippet_preview}")
        
        except Exception as e:
            print(f"❌ Error: {type(e).__name__}: {e}")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_feeds()
