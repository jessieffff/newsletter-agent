# Day 05 — Agent Workflow: Fetch → Rank → Summarize → Render

## Goal
Core agent logic that drafts a newsletter from a subscription.

## Deliverables
- LangGraph agent workflow
- End-to-end: candidates → rank/select → summarize → HTML/text output

## TODO
- [ ] LangGraph workflow scaffold (define nodes, edges)
- [ ] Node: fetch candidates from subscription sources
- [ ] Node: rank/select top N items (by recency, topic match)
- [ ] Node: summarize each item (1 sentence why_it_matters, 2–3 sentences summary)
- [ ] Node: render newsletter (subject + HTML + text)
- [ ] Guardrail: all URLs come from candidates (no invented links)
- [ ] Error handling: if summarization fails for an item, skip it (don't fail run)
- [ ] Test with a saved subscription

## Acceptance checks
- POST /run (subscription_id) → returns {status, subject, items[], html, text}
- Every item.url matches a candidate URL
- Newsletter is readable and well-formatted
- No hallucinated content
