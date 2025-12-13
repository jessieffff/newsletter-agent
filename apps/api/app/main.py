from __future__ import annotations
import os
import uuid
from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .config import settings
from .routes.api import router as api_router
from .observability import setup_tracing

try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
except Exception:  # pragma: no cover
    FastAPIInstrumentor = None  # type: ignore

load_dotenv()

setup_tracing(service_name="newsletter-agent-api")

app = FastAPI(title="Newsletter Agent API")

if FastAPIInstrumentor is not None:
    FastAPIInstrumentor.instrument_app(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    return response

@app.get("/health")
async def health():
    return {"ok": True, "storage": settings.storage_backend}

app.include_router(api_router, prefix="/v1")
