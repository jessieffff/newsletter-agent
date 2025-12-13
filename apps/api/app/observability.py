from __future__ import annotations

import os
from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

try:
    from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
except Exception:  # pragma: no cover
    AzureMonitorTraceExporter = None  # type: ignore


def setup_tracing(*, service_name: str) -> None:
    """Configure OpenTelemetry tracing with Azure Monitor exporter.

    This is intentionally minimal and safe-by-default:
    - Only enables export if `APPLICATIONINSIGHTS_CONNECTION_STRING` is present.
    - Otherwise, no-op (local dev can still run without extra env).
    """

    connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if not connection_string:
        return

    if AzureMonitorTraceExporter is None:
        return

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    exporter = AzureMonitorTraceExporter(connection_string=connection_string)
    provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(provider)


def get_tracer(name: str):
    return trace.get_tracer(name)


def current_trace_id_hex() -> Optional[str]:
    span = trace.get_current_span()
    ctx = span.get_span_context()
    if not ctx or not ctx.is_valid:
        return None
    return f"{ctx.trace_id:032x}"
