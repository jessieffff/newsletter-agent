# Day 03 — Settings API + Minimal UI

## Goal
Ability to save a test subscription; bare-minimum UI.

## Deliverables
- Subscription CRUD endpoints (save/fetch)
- Ultra-simple settings form (topics, RSS URL, frequency)

## TODO
- [ ] POST /subscriptions (create with topics[], sources[], frequency, item_count)
- [ ] GET /subscriptions (list for current user)
- [ ] Form validation (topics non-empty, RSS URL format check)
- [ ] React form component: topics input, RSS URL, frequency dropdown
- [ ] "Save subscription" wires to API
- [ ] In-memory storage: subscriptions keyed by user_id

## Acceptance checks
- POST returns subscription ID
- GET returns saved subscription
- Form values persist in local state
- No styling needed; function first
