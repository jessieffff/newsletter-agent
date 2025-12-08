# Day 02 — Azure baseline + Local Dev Setup

## Goal
Get local API + web running; defer cloud infra to later.

## Deliverables
- Local FastAPI server with `/health` endpoint
- Local Next.js web running on localhost:3000
- Cosmos DB or in-memory storage for local dev

## TODO
- [ ] FastAPI skeleton (main.py, requirements.txt)
- [ ] `/health` endpoint
- [ ] In-memory storage for local subscriptions (skip Cosmos for now)
- [ ] CORS configured
- [ ] Next.js dev server confirmed running
- [ ] API client stub in web (fetch from localhost:8000)

## Acceptance checks
- `python -m uvicorn app.main:app --reload` starts API on :8000
- `npm run dev` starts web on :3000
- Web can reach `/health` endpoint
- No external cloud infra needed to start coding agent
