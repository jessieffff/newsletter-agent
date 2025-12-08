# Day 04 — RSS Connector + Candidate Normalization

## Goal
Fetch and normalize RSS items to a standard format.

## Deliverables
- RSS feed fetcher (handles real-world quirks)
- Candidate item list with normalized schema
- Deduplication by URL

## TODO
- [ ] RSS parser library (feedparser)
- [ ] Tool: fetch_rss_feed(url) → returns raw items
- [ ] Normalize to: {title, url, source, published_at}
- [ ] Canonical URL extraction (strip tracking params)
- [ ] Dedupe logic: group by canonical_url, keep most recent
- [ ] Test with 3–5 real RSS feeds

## Acceptance checks
- For known RSS feed: get 10–20 valid items
- No duplicate URLs in output
- Handles malformed feeds gracefully (skip bad items, continue)
