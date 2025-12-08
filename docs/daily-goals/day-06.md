# Day 06 — Real-time web grounding (optional but recommended)

## Goal
Support “latest news” beyond RSS via grounded search.

## Deliverables
- Grounded search tool returning fresh links with citations/URLs
- Merged + deduped candidates

## TODO
- [ ] Configure grounding connection (if using Azure AI Foundry)
- [ ] Implement grounded_search(query)
- [ ] Add caps (max links, max tool calls, timeouts)

## Acceptance checks
- Topic with no RSS still yields usable links
- Failures fall back to RSS-only without crashing
