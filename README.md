# Newsletter Agent

Build a web-accessible agent that:
- lets users configure **topics/industries**, optional **sources** (RSS / NYT / X / domains),
- pulls the **latest news**, drafts a newsletter with links,
- and sends it on a schedule via email.

## Why this repo uses Foundry “Grounding with Bing Search”
Microsoft retired **Bing Search APIs on Aug 11, 2025** and recommends migrating to **Grounding with Bing Search** in Azure AI Agents. This repo includes an optional tool connector via the Azure AI Foundry SDK for real-time web grounding.

## Repo layout
```
apps/
  api/         FastAPI backend (runs agent + sends email)
  web/         Next.js UI (settings + history)
  functions/   Azure Functions timer (calls /runs/send-due)
packages/
  agent/       LangGraph workflow + tools + rendering
infra/         Bicep placeholder (fill in Day 2)
docs/          architecture + plan
```

## Quickstart (local)

### Prerequisites
- Python 3.10 or higher (required by the agent package)
- Node.js 18+ (for the Next.js web app)

### 1) Copy environment file:
```bash
cp .env.example .env
```

### 2) Start the API backend:

**Option A: Using the Makefile (requires `python3` command):**
```bash
make dev-api
```

**Option B: Manual setup (recommended on macOS):**
```bash
cd apps/api
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e ../../packages/agent
./.venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at http://localhost:8000
- Health check: http://localhost:8000/health
- API docs: http://localhost:8000/docs

### 3) Start the web frontend:
```bash
export NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
make dev-web
```

Or manually:
```bash
cd apps/web
npm install
npm run dev
```

### 4) Open the UI:
- http://localhost:3000/settings → "Send test email" (requires email config)

### Local dev notes
- Default storage is `STORAGE_BACKEND=memory` (in-memory).
- To enable Cosmos, set `STORAGE_BACKEND=cosmos` + Cosmos env vars.
- If you encounter "python: command not found", use `python3` or `python3.12` instead.


## Azure deployment (high level)
- Web → Azure Static Web Apps (GitHub Action included)
- API → Azure Container Apps (GitHub Action included)
- Scheduler → Azure Functions timer trigger (GitHub Action included)
- Secrets → Key Vault (recommended)
- Optional: Azure AI Foundry Project + Grounding tool connection

## Environment variables you’ll likely set in Azure
- `AZURE_OPENAI_*` for generation
- `ACS_EMAIL_*` for sending
- `COSMOS_*` for persistence
- `FOUNDRY_*` for web grounding (optional)

## Next steps
- Add auth (Entra ID / B2C)
- Replace heuristic parsing with structured outputs (JSON schema)
- Add proper “due” calculation per subscription frequency
- Add LangSmith tracing + evaluation harness
