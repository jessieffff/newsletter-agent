LLM Function Calling — Implementation Requirements
Project: newsletter-agent
Scope: Replace simple_rank(...) with LLM tool call rank_and_select, and convert generate_newsletter_content(...) into an LLM tool call draft_newsletter_items.

======================================================================
A. OVERVIEW (WHAT MUST CHANGE)
======================================================================

1) In packages/agent/src/newsletter_agent/workflow.py:
   - Update node_select_and_write:
     - Keep filter_and_dedupe_candidates(...) as-is.
     - Replace:
         ranked = simple_rank(candidates)
         picked = ranked[:subscription.item_count]
       with:
         picked = picked_candidates_from_llm_rank_and_select(...)
     - Replace:
         selected, newsletter = await generate_newsletter_content(subscription, picked, state)
       with:
         draft = draft_from_llm_draft_newsletter_items(...)
         selected/newsletter derived deterministically from draft + picked.

2) In packages/agent/src/newsletter_agent/llm_ops.py (or a new module tools.py):
   - Add two LLM tools with strict schemas:
     - rank_and_select
     - draft_newsletter_items
   - Both must be implemented using LangChain “tool/function calling” (structured tool outputs).
   - Add output validation and safe fallbacks.

3) Types and validation:
   - Ensure the LLM can NEVER introduce new URLs.
   - Ensure max_per_domain is enforced.
   - Ensure outputs always conform to schema; otherwise fall back.

======================================================================
B. TOOL 1: rank_and_select (LLM TOOL CALL)
======================================================================

Goal:
Select the best N candidates from a list using recency + topic relevance + diversity.
The model returns IDs only (NOT full items) so it cannot invent URLs.

B1. Input contract (Pydantic model)
- Tool name: rank_and_select
- Input fields:
  - topics: list[str]
  - target_count: int  (must equal subscription.item_count)
  - max_per_domain: int (default 2)
  - candidates: list[CandidateForRanking]
- CandidateForRanking fields:
  - id: str                 (stable ID assigned in node_select_and_write)
  - title: str
  - url: str
  - source: str             (e.g., rss/nyt/x/foundry or domain name)
  - published_at: str | None (ISO 8601 if present)
  - snippet: str | None

B2. Output contract (Pydantic model)
- selected_ids: list[str]            (length <= target_count)
- reasons: dict[str, str]            (key = id, value = short reason)
- rejected: list[{id: str, reason: str}] (optional)

B3. Hard requirements
1) IDs only:
   - The tool output must reference existing candidate IDs only.
   - If an ID is not found in the input candidate set, treat output as invalid.

2) Diversity constraint:
   - Enforce max_per_domain in TWO layers:
     a) ask LLM to respect it (soft constraint)
     b) enforce it deterministically after tool output (hard constraint)
   - If after enforcement selected_count < target_count, fill remaining using deterministic fallback rank.

3) Validation:
   - Validate schema strictly.
   - Validate selected_ids uniqueness.
   - Validate all IDs exist.
   - Validate output size <= target_count.

4) Fallback:
   - If tool call fails (invoke error / invalid schema / invalid IDs),
     fall back to:
       ranked = simple_rank(candidates)
       picked = ranked[:subscription.item_count]
   - Record an error in state.errors with source="llm", code="rank_and_select_failed"
     including short detail (e.g., "invalid ids", "tool invoke failure").

B4. Prompting requirements (system / tool description)
- Include explicit rules:
  - Use only provided candidate IDs.
  - Do not modify URLs.
  - Prefer recent and on-topic items.
  - Enforce diversity: no more than max_per_domain per domain.

======================================================================
C. TOOL 2: draft_newsletter_items (LLM TOOL CALL)
======================================================================

Goal:
Generate newsletter subject and per-item copy with strict structured output.
The model must copy URLs verbatim from inputs and must not add unsupported claims.

C1. Input contract (Pydantic model)
- Tool name: draft_newsletter_items
- Input fields:
  - tone: str (e.g., "concise_professional")
  - max_summary_sentences: int (default 3)
  - items: list[SelectedItemForDraft]
- SelectedItemForDraft fields:
  - id: str                  (same ID used earlier)
  - title: str
  - url: str                 (must be preserved)
  - source: str
  - published_at: str | None
  - snippet: str | None

C2. Output contract (Pydantic model)
- subject: str
- items: list[DraftedItem]
- DraftedItem fields:
  - id: str                  (must reference an input item id)
  - title: str               (should equal input title OR be lightly edited; optional)
  - source: str              (from input)
  - url: str                 (MUST match input url for that id exactly)
  - why_it_matters: str      (exactly 1 sentence)
  - summary: str             (2–3 sentences, <= max_summary_sentences)

C3. Hard requirements
1) URL integrity:
   - For every output item, verify:
       output.url == input.url for same id
   - If any mismatch exists, treat output invalid and fall back.

2) ID integrity:
   - Output items must reference input IDs only.
   - No duplicates.

3) Length constraints:
   - why_it_matters must be exactly 1 sentence (approx check: one terminal punctuation; keep simple rule).
   - summary must be 2–3 sentences and should not exceed max_summary_sentences.

4) No hallucinated claims:
   - Prompt must instruct: only use information supported by title/snippet/citation.
   - If snippet is empty, summary must be conservative and clearly framed.

5) Fallback:
   - If tool call fails or validation fails:
     - Call the existing generate_newsletter_content(subscription, picked, state) as fallback (temporary).
     - Record an error in state.errors with source="llm", code="draft_newsletter_items_failed".

C4. Deterministic rendering
- After draft output is validated, construct Newsletter object deterministically (no freeform LLM HTML):
  - Newsletter.subject = draft.subject
  - Newsletter.items = mapped DraftedItems (ordered as output order)
- If you have an HTML renderer, run it deterministically after this step (not inside LLM).

======================================================================
D. node_select_and_write: REQUIRED CHANGES (workflow.py)
======================================================================

D1. Keep existing behavior
- Keep:
  - check_node_execution_limit
  - filter_and_dedupe_candidates
  - status logic (draft vs approved)
  - logging and otel_span

D2. Replace ranking and drafting
Inside node_select_and_write:

1) Assign stable IDs for candidates before sending to LLM:
   - Example:
       for idx, c in enumerate(candidates):
           c_id = f"cand:{idx}"
   - Do not use URL as ID directly (tracking params may differ pre-canonicalization).

2) Call LLM tool rank_and_select:
   - Provide topics, target_count=subscription.item_count, max_per_domain=2, candidates payload.

3) Post-process and enforce max_per_domain deterministically:
   - Derive domain from URL (urllib.parse).
   - If violations, drop extras and fill with fallback ranking list.

4) Call LLM tool draft_newsletter_items on the final picked set:
   - Provide tone, max_summary_sentences, items payload.

5) Validate draft output and build:
   - state["selected"] = picked (or mapped selected)
   - state["newsletter"] = Newsletter(subject, items)
   - If invalid, run fallback generate_newsletter_content as described above.

D3. Telemetry requirements
- Add structured logging fields:
  - used_llm_ranker: bool
  - used_llm_drafter: bool
  - llm_ranker_fallback_reason: str | None
  - llm_drafter_fallback_reason: str | None
  - max_per_domain_enforced: bool
- Keep existing latency + selected_count logging.

======================================================================
E. TESTS (MINIMUM REQUIRED)
======================================================================

Add tests in packages/agent/tests (or existing test folder):

1) rank_and_select validation:
   - Rejects unknown IDs
   - Rejects duplicate IDs
   - Falls back to simple_rank on invalid tool output

2) max_per_domain enforcement:
   - Given tool output that violates max_per_domain, code enforces it.
   - Ensures final selected_count == target_count when enough candidates exist.

3) draft_newsletter_items URL integrity:
   - If drafter changes URL, validation fails and fallback is used.

4) end-to-end node_select_and_write:
   - With mocked LLM tool outputs (valid):
     - state.newsletter produced and status set correctly
   - With mocked LLM tool outputs (invalid):
     - fallback path used and errors recorded

======================================================================
F. ACCEPTANCE CRITERIA
======================================================================

The implementation is complete when:

- node_select_and_write no longer calls simple_rank in the default path.
- LLM rank_and_select selects by IDs only; URLs are never generated by the model.
- max_per_domain is enforced deterministically regardless of LLM output.
- draft_newsletter_items output is schema-validated and URL-validated.
- When LLM outputs are invalid or tool call fails, system falls back safely and records errors.
- Logs/telemetry clearly show when LLM ranking/drafting is used vs fallback.

