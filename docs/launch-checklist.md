# Launch Checklist — Newsletter Agent MVP

**Last updated:** 2025-12-07  
**Status:** Planning phase  
**Target launch:** Week of Dec 24, 2025

---

## Overview

This checklist outlines the minimum viable product (MVP) launch criteria and the four-phase rollout plan. Each phase gates the next based on acceptance tests.

---

## Phase A: Local Development (Scope: Settings → Run Now → Render → History)

**Goal:** Full workflow in dev environment without email sending.  
**Duration:** ~3 days  
**Acceptance:** User can configure, generate preview, view history locally.

### Backend Setup
- [ ] Azure Cosmos DB dev instance provisioned and tested
- [ ] API server boilerplate (FastAPI or similar)
- [ ] User authentication mock (no OAuth yet; hardcoded dev user)
- [ ] Subscription CRUD endpoints (POST, GET, PUT, DELETE)

### Core Agent Workflow
- [ ] LangChain/LangGraph agent scaffolding
- [ ] RSS feed connector (minimum v1 source)
- [ ] Item deduplication logic (by canonical URL)
- [ ] Basic ranking algorithm (recency + topic match)
- [ ] Newsletter rendering (Jinja template or similar)
  - [ ] HTML email template
  - [ ] Plain-text fallback

### Web UI (Settings + History)
- [ ] Settings page: Create/edit subscription
  - [ ] Topics input (comma-separated)
  - [ ] RSS URL input (at least one source)
  - [ ] Frequency dropdown (daily/weekly)
  - [ ] Item count slider (1–20)
  - [ ] Save/delete buttons
- [ ] Generate preview button (triggers run-now, no email)
- [ ] History page: List past runs
  - [ ] Run status badge (queued/drafted/sent/failed)
  - [ ] Timestamp display
  - [ ] Link to view generated newsletter (HTML + text preview)

### Data Model
- [ ] User schema + Cosmos DB schema validation
- [ ] Subscription schema + seed test data
- [ ] Run schema + status tracking

### Testing
- [ ] Unit tests for deduplication logic
- [ ] Unit tests for ranking algorithm
- [ ] Integration test: end-to-end flow (configure → generate → view)
- [ ] Manual QA: user can configure, preview, view history

### Documentation
- [ ] Architecture diagram (web, API, agent, DB)
- [ ] Local dev setup guide (env vars, Cosmos DB connection)

---

## Phase B: Email Integration (Scope: Phase A + ACS Email + Send Test)

**Goal:** Ability to send real emails from the system.  
**Duration:** ~2 days  
**Acceptance:** User can generate and send a test email to their inbox.

### Azure Communication Services (ACS) Integration
- [ ] ACS Email resource created in Azure portal
- [ ] Email domain configured (or use trial domain)
- [ ] API credentials stored in Azure Key Vault
- [ ] Key Vault SDK integrated in API

### Email Sending Service
- [ ] Email sending module (wraps ACS begin_send API)
- [ ] HTML + plain-text email composition
- [ ] Error handling and retry logic
- [ ] Logging for send attempts

### Backend Enhancements
- [ ] Run status progression: queued → drafted → sent
- [ ] `sent_at` timestamp tracking
- [ ] Error object population on failure
- [ ] Idempotency check: don't send twice for same subscription in 24h

### Web UI Enhancements
- [ ] "Send test" button on subscription page
  - [ ] Pre-fills recipient as logged-in user's email
  - [ ] Triggers run + immediate send
  - [ ] Shows success/failure toast
- [ ] History page shows `sent_at` timestamp when applicable
- [ ] "Resend" button on past draft runs (before schedule)

### Testing
- [ ] Unit test: email template renders correctly
- [ ] Integration test: trigger send-test, verify email received
- [ ] Manual QA: send test email, check spam folder, verify content
- [ ] Error scenarios: invalid email, ACS service down (graceful fail)

### Documentation
- [ ] ACS setup guide (resource creation, credentials)
- [ ] Troubleshooting: common email delivery issues

---

## Phase C: Scheduled Delivery (Scope: Phase B + Timer Trigger + "Send Due")

**Goal:** Automated daily/weekly newsletter sends on schedule.  
**Duration:** ~2 days  
**Acceptance:** Newsletter automatically sends at scheduled time without manual trigger.

### Azure Functions Timer Trigger
- [ ] Function app deployed to Azure
- [ ] Timer trigger function scaffolding
- [ ] Function identity/managed identity configured for API calls
- [ ] Function monitoring + logging enabled

### Scheduling Logic
- [ ] "Send due" query: find subscriptions where next_send_time ≤ now
  - [ ] frequency = daily: next send is today at 9 AM (user's timezone or system default)
  - [ ] frequency = weekly: next send is next Monday at 9 AM
- [ ] Batch processing: trigger runs for all due subscriptions
- [ ] Update subscription: `last_run_at`, `next_run_at` timestamps

### Idempotency & Safety
- [ ] Run record lock/lease (prevent duplicate processing)
- [ ] Handle partial failures (e.g., one subscription fails, others succeed)
- [ ] Alarm/alert on function failure (send to operations team)
- [ ] Dry-run mode: log what would send without actually sending

### Web UI Enhancements
- [ ] Display next scheduled send time on subscription card
- [ ] Allow manual reschedule (change frequency or trigger now)
- [ ] Show last run status and time in history

### Testing
- [ ] Unit test: scheduling logic (calculate next send time correctly)
- [ ] Integration test: timer function triggers, calls API, updates DB
- [ ] Manual QA: set frequency to daily, wait for scheduled send (or use accelerated clock in dev)
- [ ] Chaos test: simulate API down, verify graceful failure and retry

### Documentation
- [ ] Azure Functions deployment guide
- [ ] Scheduling timezone handling and edge cases
- [ ] Runbook for monitoring scheduled sends

---

## Phase D: Freshness & Advanced Sources (Scope: Phase C + Foundry Grounding + Optional Custom Search)

**Goal:** Real-time web freshness via Azure AI Foundry; optional domain-restricted search.  
**Duration:** ~3 days  
**Acceptance:** Newsletter includes fresh web results; domain filtering works.

### Azure AI Foundry Integration
- [ ] Foundry resource created in Azure portal
- [ ] Grounding with Bing Search connector enabled
- [ ] Optional: Custom Search connector (for domain-restricted monitoring)
- [ ] Credentials in Key Vault

### Advanced Source Connectors
- [ ] Bing Search grounding integration (fetch fresh web results)
- [ ] NYT API integration (optional; requires API key)
- [ ] X/Twitter API integration (optional; requires elevated access)
- [ ] Domain-restricted search (Custom Search for allowlisted domains only)

### Agent Enhancement
- [ ] Agent calls Foundry grounding for additional freshness
- [ ] Deduplication across all sources (RSS + Bing + NYT + X)
- [ ] Ranking refined: recency (from Bing), source diversity, topic relevance
- [ ] Fallback gracefully if Foundry unavailable

### UI Enhancements
- [ ] Settings: add toggles for optional sources (NYT, X, Bing grounding)
- [ ] Settings: add domain allowlist field (for Custom Search)
- [ ] Run details: show source breakdown (how many items from each connector)

### Testing
- [ ] Unit test: canonical URL normalization (handle tracking params)
- [ ] Integration test: grounding call + deduplication
- [ ] Integration test: custom search domain filtering
- [ ] Manual QA: generate newsletter, verify fresh results, check source diversity

### Documentation
- [ ] Foundry setup & credential management
- [ ] Custom Search configuration guide
- [ ] Handling API rate limits and timeouts

---

## Launch Gate Criteria

### Phase A Gate: "Local MVP Works"
- [ ] All acceptance tests pass
- [ ] No hardcoded secrets in code
- [ ] API returns 200 for CRUD operations
- [ ] Web UI allows end-to-end flow (settings → generate → history)
- [ ] At least 1 sample subscription generates at least 1 newsletter preview

### Phase B Gate: "Email Sends Reliably"
- [ ] Send test emails to staging inbox; all received
- [ ] Error handling tested (invalid email, service down)
- [ ] No leakage of emails outside expected recipients
- [ ] Email templates render correctly in major clients (Gmail, Outlook, Apple Mail)
- [ ] Logging records send attempts and outcomes

### Phase C Gate: "Scheduling Works Reliably"
- [ ] Timer trigger test runs; calls API successfully
- [ ] Subscriptions marked due are processed
- [ ] Idempotency verified (no duplicate sends)
- [ ] Failure notifications configured
- [ ] Runbook created and tested

### Phase D Gate: "Fresh Sources Integrate"
- [ ] Foundry grounding returns results
- [ ] Bing search + RSS + (NYT/X if enabled) items all deduplicated
- [ ] Custom Search domain filtering validated
- [ ] No hallucinated URLs in final newsletter
- [ ] Performance acceptable (target: run completes in < 30s)

---

## Non-Functional Requirements (All Phases)

### Security
- [ ] No API keys, tokens, or credentials in code
- [ ] Azure Key Vault used for all secrets
- [ ] User authentication enforced (no public APIs)
- [ ] CORS/CSRF protection on web UI
- [ ] SQL injection prevention (parameterized queries)

### Performance
- [ ] Run completes in ≤ 30 seconds (including all API calls)
- [ ] History list loads in ≤ 2 seconds
- [ ] Settings page UI responds in ≤ 1 second

### Reliability
- [ ] Graceful degradation if one source fails (don't drop entire run)
- [ ] Retry logic for transient errors (with exponential backoff)
- [ ] All errors logged with context (subscription_id, run_id, error code)

### Usability
- [ ] No jargon in UI (e.g., "topic" instead of "entity", "item" instead of "vector")
- [ ] Error messages are actionable (e.g., "Invalid RSS URL: must be http/https")
- [ ] Settings saved automatically or with single "Save" button
- [ ] Confirmation before destructive actions (delete subscription)

### Observability
- [ ] API logs include request ID, user_id, run_id for tracing
- [ ] Azure Application Insights configured for web and API
- [ ] Dashboard: active subscriptions, daily sends, failure rate
- [ ] Alerts on critical errors (e.g., ACS email service down)

---

## Deployment Strategy

### Infrastructure (IaC)
- [ ] Bicep file covers all Azure resources (App Service, Cosmos DB, ACS, Functions, Key Vault)
- [ ] Staging and production environments defined
- [ ] CI/CD pipeline (GitHub Actions or Azure DevOps)

### Staging Rollout
- [ ] Deploy Phase A to staging; internal team tests
- [ ] Deploy Phase B; send test emails to staging mailbox
- [ ] Deploy Phase C; verify timer trigger in staging
- [ ] Deploy Phase D; test Foundry in staging environment

### Production Rollout
- [ ] Incremental rollout: Phase A → B → C → D
- [ ] Each phase gates the next based on metrics
- [ ] Canary: first few users; monitor error rates and support tickets
- [ ] Full launch: announce feature availability

---

## Success Metrics (Post-Launch)

### Activation
- % users who create a subscription
- % users who generate at least 1 newsletter
- % users who receive a sent email

### Engagement
- Click-through rate (CTR) on links in newsletter
- User feedback score (like/dislike on items)
- Subscription retention (% still enabled after 1 month)

### Reliability
- Send success rate (sent / attempted)
- Average run time
- Error rate by phase
- Tool failure fallback rate (% items retrieved despite one source failing)

### Quality
- Duplicate-link rate per newsletter (target: near 0)
- User-reported hallucination rate (fabricated URLs)
- Average items per newsletter (vs. target item_count)

---

## Post-MVP Roadmap (Out of Scope)

- OAuth/multi-user authentication
- Team collaboration + shared subscriptions
- User preferences (timezone, custom templates)
- Analytics dashboard (click tracking, engagement)
- Feedback loop (user votes → ranking refinement)
- Multi-language support
- Mobile app / push notifications
- Webhook triggers
- API for external integrations

---

## Rollback Plan

Each phase has a rollback:

1. **Phase A:** If major bugs, roll back to manual testing only
2. **Phase B:** Disable email sending; revert to preview-only mode
3. **Phase C:** Disable scheduled sends; require manual trigger
4. **Phase D:** Disable Foundry grounding; fall back to RSS + seed sources

Key metric for rollback: Error rate > 5% sustained for > 1 hour → alert + manual intervention.

---

## Communication Plan

- **Internal:** Share phase gates with team before launch
- **Users:** Announce Phase A availability; gather feedback before Phase B
- **Changelog:** Document feature rollout; link to docs
- **Support:** Prepare FAQ and troubleshooting guide

