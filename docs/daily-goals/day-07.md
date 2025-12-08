# Day 07 — LangGraph reliability (state, retries, fallback)

## Goal
Robust workflow with clear stages and error handling.

## Deliverables
- Graph nodes: load → fetch → optional grounding → dedupe → rank → write → render
- Run record stored with status

## TODO
- [ ] Node-level error capture in state
- [ ] Idempotency key per subscription + time window
- [ ] Persist run outputs (subject/items/html/text)

## Acceptance checks
- Partial failures still produce a valid newsletter
- Run history shows status + error when applicable
