# Day 7 Notes – AI Agents in Production: Observability & Evaluation

Reference lesson: https://github.com/microsoft/ai-agents-for-beginners/tree/main/10-ai-agents-production

These notes summarize the lesson content, organized to match `days/day07.md`.

## Step 1: Define “Success” for One Agent

The lesson’s key message: you can’t evaluate or improve an agent unless you define what “good” means.

- Define success up front: what outcome should the agent reliably produce?
- Decide what you will label/score: pass/fail labels, accuracy proxy, user satisfaction, or task completion.
- Tie “success” to measurable signals:
  - **Accuracy / desirability** (correctness, relevance, policy compliance)
  - **Reliability** (works consistently, avoids loops)
  - **Operational health** (low error rate, acceptable latency/cost)

Why: once agents are in production, observability data becomes the foundation for diagnosis, trust, and improvement.

## Step 2: Observability Events & Fields (Telemetry Schema)

### Core concepts (from the lesson)

- **Trace**: a complete agent run end-to-end (e.g., handling one user query).
- **Span**: an individual step inside the trace (e.g., an LLM call, retrieval, tool call).
- Observability turns agents from **“black boxes”** into **“glass boxes”** by making steps, timing, costs, and failures visible.

### Why observability matters in production

- **Debugging & root-cause analysis**: traces pinpoint where failures happen in multi-step workflows.
- **Latency & cost management**: measure slow/expensive steps to optimize prompts, models, or workflows.
- **Trust, safety, compliance**: keep an audit trail of decisions/actions; help detect prompt injection, harmful output, or PII mishandling.
- **Continuous improvement loop**: production insights inform offline test sets and changes.

### Key metrics to track (lesson list)

- **Latency**: total run + per-step timing; identify bottlenecks.
- **Costs**: cost per run; token usage; number of calls; unexpected spikes.
- **Request errors**: API/tool failures; support retries/fallbacks (e.g., provider A → provider B).
- **User feedback (explicit)**: ratings (thumbs / stars) and comments.
- **User feedback (implicit)**: rephrases, retries, repeated questions, aborts.
- **Accuracy / success rate**: define what success means, then label traces “succeeded/failed”.
- **Automated evaluation metrics**:
  - Use LLM-as-a-judge to score helpfulness/accuracy.
  - Use task-specific tools (e.g., RAG evaluation libraries like RAGAS; safety tooling such as LLM Guard) where relevant.

### Instrumentation approaches

- **OpenTelemetry (OTel)**: emerging standard for LLM observability; generate/export telemetry.
- **Instrumentation wrappers**: libraries that automatically capture spans for agent frameworks.
- **Manual spans**: add custom spans and attributes/tags for business context.
  - Example attributes mentioned: `user_id`, `session_id`, `model_version`.

## Step 3: Map Spans to Your Agent Workflow

The lesson recommends thinking in trace trees: one trace per request, with spans for each meaningful step.

Typical span categories:
- LLM calls (planning, drafting, judging)
- Retrieval steps (search/RAG)
- Tool calls (API, DB, file, browser)
- Safety checks / policy filters
- Retries/fallbacks

Why: consistent span naming and structure makes dashboards and regression detection possible.

## Step 4: Build an Offline Eval Set

### Offline evaluation (lesson summary)

- Evaluate the agent in a **controlled setting** using test datasets.
- Benefits:
  - Repeatable, suitable for CI/CD regression tests.
  - Clearer accuracy metrics when you have ground truth.
- Challenge:
  - Test sets can become stale; the agent may face different real-world queries.
- Practical guidance:
  - Maintain a mix of **small “smoke tests”** (fast checks) and **larger eval sets** (broad coverage).
  - Keep adding new edge cases informed by production failures.

### Recommended evaluation loop

The lesson’s loop:

`evaluate offline → deploy → monitor online → collect new failure cases → add to offline dataset → refine → repeat`

## Step 5: Design an Online Feedback Loop

### Online evaluation (lesson summary)

- Evaluate the agent in the **live environment** on real user interactions.
- Benefits:
  - Captures unexpected real-world queries.
  - Detects **model drift** (performance changes over time as inputs shift).
- Common techniques:
  - Track success rate, satisfaction, and operational metrics on real traffic.
  - Collect explicit + implicit feedback.
  - Consider **shadow testing** / **A/B testing** to compare agent versions.
- Challenge:
  - Live labels can be noisy; you may rely on user feedback or downstream behaviors.

### Common production issues (and how observability helps)

- Inconsistent task performance: refine prompts/objectives; consider decomposing tasks.
- Continuous loops: define termination conditions; consider using a stronger reasoning model for planning.
- Tool calls failing: validate tools outside the agent; refine tool definitions/parameters.
- Multi-agent inconsistency: make roles distinct; use a router/controller agent.

### Cost management strategies (lesson list)

- Use **smaller models (SLMs)** for simpler steps; reserve larger models for complex reasoning.
- Use a **router model** to choose the right model by request complexity.
- **Cache responses** for common requests (and optionally classify similarity before running the full agent).

## Notes / Links

- Lesson: https://github.com/microsoft/ai-agents-for-beginners/tree/main/10-ai-agents-production
- Example notebook referenced by lesson: https://github.com/microsoft/ai-agents-for-beginners/blob/main/10-ai-agents-production/code_samples/10_autogen_evaluation.ipynb
