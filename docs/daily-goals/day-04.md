# Day 04 — RSS Connector + Candidate Normalization

## Goal
Fetch and normalize RSS items to a standard format.

## Deliverables
- RSS feed fetcher (handles real-world quirks)
- Candidate item list with normalized schema
- Deduplication by URL

## TODO
- [x] RSS parser library (feedparser)
- [x] Tool: fetch_rss_feed(url) → returns raw items
- [x] Normalize to: {title, url, source, published_at}
- [x] Canonical URL extraction (strip tracking params)
- [x] Dedupe logic: group by canonical_url, keep most recent
- [x] Test with 3–5 real RSS feeds

## Acceptance checks
- [x] For known RSS feed: get 10–20 valid items
- [x] No duplicate URLs in output
- [x] Handles malformed feeds gracefully (skip bad items, continue)
