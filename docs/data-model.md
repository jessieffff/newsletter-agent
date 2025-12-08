# Data Model — Newsletter Agent (MVP)

**Last updated:** 2025-12-07  
**Status:** MVP specification  
**Storage:** Azure Cosmos DB

---

## Overview

The data model supports the core user workflow:

1. **User** creates a **Subscription** with topics, sources, and preferences
2. Scheduler or manual trigger initiates a **Run** based on the subscription
3. During a **Run**, we fetch and process **Items** from various sources
4. The **Run** generates a newsletter email and stores the **Items** with metadata
5. **History** is queryable by the user via the web UI

---

## Core Entities

### 1. User

Represents an authenticated user with a configured email address.

```json
{
  "id": "string (UUID)",
  "email": "string (email format)",
  "created_at": "timestamp (ISO 8601)",
  "updated_at": "timestamp (ISO 8601)"
}
```

**Fields:**
- `id` — Unique identifier (UUID or similar)
- `email` — User's email; used for authentication and sending newsletters
- `created_at` — Account creation timestamp
- `updated_at` — Last profile update timestamp

**Partition key:** `id`

---

### 2. Subscription

A configuration set that defines which topics/sources to monitor and how often to send.

```json
{
  "id": "string (UUID)",
  "user_id": "string (UUID, FK to User)",
  "topics": [
    "string (e.g., 'AI agents', 'cloud security')"
  ],
  "sources": [
    {
      "type": "enum (rss | domain | nyt | x)",
      "rss_url": "string (optional, required if type=rss)",
      "domain": "string (optional, required if type=domain)",
      "nyt_query": "string (optional, required if type=nyt)",
      "x_query": "string (optional, required if type=x)",
      "x_account": "string (optional)"
    }
  ],
  "frequency": "enum (daily | weekly)",
  "item_count": "integer (1–20)",
  "tone": "string (default: 'professional')",
  "enabled": "boolean (default: true)",
  "created_at": "timestamp (ISO 8601)",
  "updated_at": "timestamp (ISO 8601)"
}
```

**Fields:**
- `id` — Unique identifier (UUID)
- `user_id` — Reference to owning User (enables multi-subscription per user)
- `topics` — Array of topic strings; user-provided keywords to focus the search
- `sources` — Array of source objects:
  - `type` — One of: `rss` (RSS feed), `domain` (domain allowlist), `nyt` (New York Times API), `x` (Twitter/X API)
  - Type-specific fields:
    - **RSS:** `rss_url` (fully qualified URL)
    - **Domain:** `domain` (e.g., `nytimes.com`, `theinformation.com`)
    - **NYT:** `nyt_query` (e.g., `AI agents`)
    - **X:** `x_query` (search query) and optionally `x_account` (specific account to monitor)
- `frequency` — How often to send: `daily` or `weekly`
- `item_count` — Target number of items per newsletter (validated 1–20)
- `tone` — Instructions for writing style (e.g., `"professional"`, `"concise"`, `"technical"`)
- `enabled` — If false, skip scheduling for this subscription
- `created_at`, `updated_at` — Timestamps

**Partition key:** `user_id` (enables efficient queries by user)  
**Secondary index:** `enabled` (for finding active subscriptions)

---

### 3. Run

A single execution of a newsletter generation for a subscription.

```json
{
  "id": "string (UUID)",
  "subscription_id": "string (UUID, FK to Subscription)",
  "user_id": "string (UUID, FK to User, for partition key)",
  "run_at": "timestamp (ISO 8601, when run was triggered)",
  "status": "enum (queued | drafted | sent | failed)",
  "items": [
    {
      "id": "string (UUID)",
      "title": "string",
      "url": "string (exact URL from source)",
      "source": "string (e.g., 'RSS: The Verge', 'Domain: nytimes.com', 'NYT API')",
      "summary": "string (2–3 sentences)",
      "why_it_matters": "string (1 sentence, why relevant to topics)",
      "fetched_at": "timestamp (ISO 8601)",
      "dedup_canonical_url": "string (normalized URL for deduplication)"
    }
  ],
  "subject": "string (e.g., 'Your AI Digest — Dec 7')",
  "html": "string (rendered HTML email)",
  "text": "string (plain-text fallback)",
  "error": {
    "code": "string (e.g., 'RSS_FETCH_FAILED')",
    "message": "string (human-readable error details)",
    "failed_sources": ["string (list of sources that failed)"]
  },
  "created_at": "timestamp (ISO 8601)",
  "sent_at": "timestamp (ISO 8601, optional, only if status=sent)"
}
```

**Fields:**
- `id` — Unique identifier (UUID)
- `subscription_id` — Reference to the Subscription that triggered this run
- `user_id` — Denormalized reference to User (for partition key and quick lookup)
- `run_at` — When the run was initiated (scheduled time or manual trigger)
- `status` — Current state:
  - `queued` — awaiting processing
  - `drafted` — newsletter content generated, not yet sent
  - `sent` — email successfully delivered
  - `failed` — processing encountered a critical error
- `items` — Array of selected and processed newsletter items:
  - `id` — Unique item identifier
  - `title` — Article/content title from source
  - `url` — Full URL (never invented; must come from source tool output)
  - `source` — Human-readable source identifier (e.g., `"RSS: The Verge"`)
  - `summary` — 2–3 sentence summary (AI-generated if fetching full content)
  - `why_it_matters` — 1-sentence explanation of relevance to user's topics
  - `fetched_at` — Timestamp when item was retrieved
  - `dedup_canonical_url` — Normalized URL used for deduplication logic
- `subject` — Email subject line (generated based on topics and items)
- `html` — Rendered HTML email body
- `text` — Plain-text email fallback (for non-HTML clients)
- `error` — Error details if status is `failed`:
  - `code` — Machine-readable error code
  - `message` — Human-readable error description
  - `failed_sources` — List of source connectors that failed (for graceful degradation)
- `created_at` — Timestamp when run record was created
- `sent_at` — Timestamp when email was successfully delivered (only if `status=sent`)

**Partition key:** `user_id` (enables efficient queries per user)  
**Secondary indexes:**
  - `subscription_id` (for listing runs under a subscription)
  - `status` (for filtering by state)
  - `run_at` (for temporal queries)

---

## Relationships

```
User
 ├─ 1:N ─> Subscription (one user has many subscriptions)
            └─ 1:N ─> Run (one subscription has many runs)
                      └─ 1:N ─> Items (one run has many items)
```

- **User → Subscription:** One user can create multiple subscriptions (e.g., "AI news", "Cloud security", "Web3")
- **Subscription → Run:** One subscription can have multiple runs over time (daily/weekly executions)
- **Run → Items:** One run contains multiple selected items (typically N=5–20 per newsletter)

---

## Data Constraints & Validation

### Subscription
- `topics` — non-empty array; at least one topic required
- `item_count` — integer in range [1, 20]
- `sources` — at least one source required; each source URL must be valid
- `frequency` — one of: `daily`, `weekly`
- `enabled` — boolean

### Run
- `items` array length should match or be close to target `item_count` (some sources may fail)
- `url` fields must never be null or fabricated; always sourced from tool output
- `status` transitions:
  - `queued` → `drafted` (after content generation)
  - `drafted` → `sent` (after successful email send)
  - Any → `failed` (if critical error occurs)
- `sent_at` should only be populated when `status=sent`

---

## Cosmos DB Specifics

### Partition Strategy

**Primary partition key:** `user_id` (enables multi-tenancy and efficient per-user queries)

- **Subscription container:** partition by `user_id`
- **Run container:** partition by `user_id` (even though `subscription_id` is referenced)

This allows efficient queries like:
- "Get all subscriptions for user X"
- "Get all runs for user X in the past 30 days"
- "Get a specific run by ID and user_id"

### TTL (Time-to-Live)

Consider setting optional TTL policies:
- **Run records:** Keep indefinitely or archive after 1 year (for history)
- **Temporary processing records:** Use TTL = 7 days for transient state during long-running workflows

### Indexing

Recommended indexes:
- `subscription_id` (for filtering runs by subscription)
- `status` (for filtering runs by state)
- `run_at` (for temporal queries, sorted history)
- `enabled` (on Subscriptions, for finding active subscriptions)

---

## Workflow State Diagram

```
┌─────────────────────────────────────┐
│ Subscription (configured by user)   │
└──────────────────┬──────────────────┘
                   │
         (trigger: scheduled or manual)
                   │
                   v
         ┌─────────────────┐
         │ Run: queued     │
         └────────┬────────┘
                  │
         (fetch sources, dedupe, rank)
                  │
                  v
         ┌─────────────────┐
         │ Run: drafted    │
         └────────┬────────┘
                  │
         (render email, call ACS send)
                  │
          ┌───────┴─────────┐
          │                 │
       success           failure
          │                 │
          v                 v
    ┌──────────┐    ┌─────────────┐
    │ Run:sent │    │ Run: failed  │
    └──────────┘    └─────────────┘
          │
    (stored in history)
```

---

## Example Documents

### Example: Subscription (AI + Cloud Security)

```json
{
  "id": "sub-001",
  "user_id": "user-abc123",
  "topics": ["AI agents", "cloud security", "LLM breakthroughs"],
  "sources": [
    {
      "type": "rss",
      "rss_url": "https://feeds.theverge.com/rss/index.xml"
    },
    {
      "type": "domain",
      "domain": "nytimes.com"
    },
    {
      "type": "nyt",
      "nyt_query": "artificial intelligence agents"
    },
    {
      "type": "x",
      "x_query": "LLM agents breaking",
      "x_account": "optional_account_handle"
    }
  ],
  "frequency": "daily",
  "item_count": 8,
  "tone": "professional, concise, technical",
  "enabled": true,
  "created_at": "2025-12-01T10:00:00Z",
  "updated_at": "2025-12-07T14:30:00Z"
}
```

### Example: Run (Daily Newsletter)

```json
{
  "id": "run-001",
  "subscription_id": "sub-001",
  "user_id": "user-abc123",
  "run_at": "2025-12-07T09:00:00Z",
  "status": "sent",
  "items": [
    {
      "id": "item-001",
      "title": "New LLM Router Cuts Inference Costs by 40%",
      "url": "https://example.com/llm-router-breakthrough",
      "source": "RSS: The Verge",
      "summary": "Researchers at OpenAI introduced a routing layer that intelligently selects smaller models for simpler queries. This achieves 40% cost reduction while maintaining quality. The technique may democratize LLM deployment.",
      "why_it_matters": "Directly relevant to 'AI agents' — lower inference costs enable more affordable agent deployments.",
      "fetched_at": "2025-12-07T08:45:00Z",
      "dedup_canonical_url": "example.com/llm-router-breakthrough"
    },
    {
      "id": "item-002",
      "title": "Cloud Misconfiguration Leads to Data Breach in AWS S3",
      "url": "https://nytimes.com/article/aws-s3-breach-2025",
      "source": "NYT (custom search)",
      "summary": "A Fortune 500 company exposed customer PII due to publicly-readable S3 bucket policies. Incident highlights the ongoing risk of cloud misconfiguration. CISA recommends regular audits.",
      "why_it_matters": "Critical for 'cloud security' — shows real-world attack surface from misconfigurations.",
      "fetched_at": "2025-12-07T08:50:00Z",
      "dedup_canonical_url": "nytimes.com/article/aws-s3-breach-2025"
    }
  ],
  "subject": "Your AI & Cloud Security Digest — Dec 7",
  "html": "<html><body>... rendered newsletter HTML ...</body></html>",
  "text": "Your AI & Cloud Security Digest — Dec 7\n\n--- Item 1: New LLM Router...",
  "error": null,
  "created_at": "2025-12-07T08:30:00Z",
  "sent_at": "2025-12-07T09:05:00Z"
}
```

---

## Future Extensions (Post-MVP)

- **User preferences:** timezone, frequency override per subscription
- **Analytics:** click-through rates per item, engagement scoring
- **Feedback:** user votes (like/dislike) on items for ranking refinement
- **Template versions:** allow users to customize email layouts
- **Webhook support:** trigger runs via external events
- **Multi-language:** store topics/summaries in multiple languages

