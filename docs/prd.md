# PRD — Industry News Newsletter Agent

**LangChain/LangGraph + Azure**

| | |
|---|---|
| **Last updated** | 2025-12-07 |
| **Target users** | Anyone who wants a personalized "industry digest" without manually tracking dozens of sites/accounts |

---

## 1. Problem

People want to stay current on specific industries/topics, but:

- **Sources are fragmented** — RSS sites, newspapers, social feeds, specific domains
- **"Latest" changes constantly** — hard to keep up
- **Summaries are time-consuming** — manual curation required
- **Existing newsletters fall short** — either too broad or not configurable

---

## 2. Product Summary

A web app where users can:

1. **Configure** topics/industries + optional sources (RSS, specific domains, NYT, X accounts/queries)
2. **Generate** — agent gathers fresh links, selects top N, drafts a newsletter
3. **Send** — on a configured schedule via email
4. **Review** — searchable history of runs and links

**Freshness approach:** To support real-time web freshness without relying on deprecated Bing Search APIs, we use Azure AI Foundry "Grounding with Bing Search" (and optionally Grounding with Bing Custom Search for domain-restricted monitoring).

---

## 3. Goals (MVP)

- **Configurable** — topics + sources + frequency + number of items
- **Fresh** — pulls recent links at send time (not cached for days)
- **Reliable** — graceful partial results if one source fails
- **Trustworthy** — never invent URLs; clearly separate "summary" vs "source link"
- **Usable history** — user can view what was generated/sent and click through

---

## 4. Non-Goals (MVP)

- Full multi-tenant org features (teams, shared workspaces)
- Advanced personalization (long-term embeddings, deep user profiling)
- Full article summarization for every page (not recommended for grounded search flows anyway)
- Payment/subscriptions
- Complex "Twitter-like feed" UI

---

## 5. Key User Stories (MVP)

### Primary End-to-End Story: Configure → Generate → Email → History

#### 1. Configure

**As a user**, I enter:

- **Topics/industries** — e.g., "AI agents", "cloud security"
- **Optional sources** I want monitored:
  - RSS feeds (e.g., The Verge RSS)
  - Specific domains (e.g., nytimes.com, theinformation.com)
  - Optional: NYT query, X account/query
- **Frequency** — daily/weekly
- **Number of items** — N (e.g., 8)
- **Tone** — concise/professional (default)

I save settings and can return later to see them.

#### 2. Generate

**As a user**, I click "Send test" (or "Generate preview") and the system:

- Fetches candidate links from my sources
- Optionally runs web grounding search for freshness
- Dedupes + ranks
- Drafts a newsletter with "why it matters" + summary per item

#### 3. Email

**As a user**, I receive an email with:

- Subject relevant to my topics
- Each item includes title, source, link, summary
- If sending fails, the system records an error and doesn't silently drop it

#### 4. History

**As a user**, I open "History" and see:

- Past runs with status (sent/failed)
- The exact set of links/items
- The generated text (and HTML preview)

---

## 6. Functional Requirements

### 6.1 Settings (Web UI)

**Create/Update subscription:**

- `topics[]` (string)
- `sources[]` where each source is:
  - RSS URL
  - Domain allowlist entry
  - NYT query (optional)
  - X query/account (optional)
- `frequency`: daily | weekly (MVP)
- `item_count`: 1–20
- `tone`: free text (default provided)
- `enabled`: true/false

**Validate:**

- Topics not empty
- RSS URL must be valid URL format
- Item count bounds

### 6.2 Content Gathering

**Minimum connector:** RSS

**Optional connectors:**

- NYT API (metadata/snippets)
- X API (recent search limitations apply)
- Foundry Grounding with Bing Search for fresh web results

**Domain monitoring:**

- For "only these sites," use Grounding with Bing Custom Search (domain-restricted)

### 6.3 Selection & Summarization

- **Dedupe by canonical URL**
- **Rank by:**
  - Recency (if available)
  - Source preference
  - Diversity (avoid all items from one domain)
  - Topic match
- **Generate newsletter entries:**
  - `why_it_matters` (1 sentence)
  - `summary` (2–3 sentences)
  - Keep the URL exactly as fetched
  - Strongly prefer structured outputs for the final "items list" to avoid brittle parsing

### 6.4 Delivery & Scheduling

- **Email sending** via Azure Communication Services Email (begin_send)
- **Scheduling** via Azure Functions Timer Trigger for periodic "send due" runs
- **Idempotency:** don't send twice for the same subscription in the same window (daily/weekly)

### 6.5 History

**Store run record:**

- `status`: queued/drafted/sent/failed
- Rendered HTML + plain text
- Selected items list
- Error details if failed
- UI page to list runs

---

## 7. Data Model (MVP)

### User
- `id`, `email`, `created_at`

### Subscription
- `id`, `user_id`
- `topics[]`
- `sources[]` (typed: rss/domain/nyt/x)
- `frequency`, `item_count`, `tone`, `enabled`

### Run
- `id`, `subscription_id`, `run_at`
- `status`, `items[]`
- `subject`, `html`, `text`
- `error?`

**Storage:** Azure Cosmos DB for scalable managed persistence.

---

## 8. System Architecture (MVP)

- **Web:** Next.js hosted on Azure Static Web Apps
- **API:** Containerized backend on Azure Container Apps
- **Scheduler:** Azure Functions Timer Trigger calls "send due"
- **Agent:** LangChain + LangGraph workflow (better for multi-step reliability/persistence patterns than a single prompt)
- **Secrets:** Azure Key Vault for API keys/email credentials

---

## 9. MVP Success Metrics

**Activation:** % users who save a subscription and generate at least 1 run

**Delivery:** send success rate (sent / attempted)

**Quality:**
- Duplicate-link rate (target: near 0)
- Click-through rate (CTR) on links
- User feedback score (like/dislike)

**Reliability:**
- Median run time
- Tool failure fallback rate

---

## 10. Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| **Freshness / web access limitations** | Bing Search APIs retired → use Foundry grounding |
| **Hallucinated facts** | Enforce "URL must come from tool output" + structured outputs + conservative prompts |
| **Source restrictions** | For "monitor only NYT / specific domains," use Custom Search grounding + allowlists |
| **Secrets leakage** | Key Vault + avoid logging tokens/keys |

---

## 11. MVP Rollout Plan

- **Phase A (Local):** settings → run-now → render → history (no email)
- **Phase B (Email):** add ACS Email + send test
- **Phase C (Schedule):** add timer trigger + "send due"
- **Phase D (Freshness):** add Foundry grounding + optional custom search
