.PHONY: dev-api dev-web dev-functions lint

dev-api:
	cd apps/api && python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt && pip install -e ../../packages/agent && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-web:
	cd apps/web && npm install && npm run dev

dev-functions:
	cd apps/functions && python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt && func start

lint:
	python -m compileall packages/agent/src apps/api/app
