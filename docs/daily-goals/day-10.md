# Day 10 — Scheduling & “send due”

## Goal
Automated sending at user-selected frequency.

## Deliverables
- Scheduler job calls send-due endpoint
- Due calculation for daily/weekly (cron later)

## TODO
- [ ] Implement due calculation
- [ ] Add timer trigger
- [ ] Add idempotency (no duplicate sends)
- [ ] Support pause/resume

## Acceptance checks
- Scheduled run sends without manual action
- No duplicate sends within a window
