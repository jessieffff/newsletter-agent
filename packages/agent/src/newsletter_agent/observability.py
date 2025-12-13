from __future__ import annotations

from contextlib import contextmanager
from typing import Dict, Iterator, Optional

try:
    from opentelemetry import trace
except Exception:  # pragma: no cover
    trace = None  # type: ignore


def _tracer():
    if trace is None:
        return None
    return trace.get_tracer("newsletter_agent")


@contextmanager
def span(name: str, *, attributes: Optional[Dict[str, object]] = None) -> Iterator[None]:
    """Create an OTel span if OpenTelemetry is installed/configured.

    Safe no-op when OTel isn't available (e.g., local unit tests).
    """

    tracer = _tracer()
    if tracer is None:
        yield
        return

    with tracer.start_as_current_span(name) as s:
        if attributes:
            for k, v in attributes.items():
                if v is None:
                    continue
                s.set_attribute(k, v)
        yield


def set_attributes(attributes: Dict[str, object]) -> None:
    if trace is None:
        return
    s = trace.get_current_span()
    for k, v in attributes.items():
        if v is None:
            continue
        s.set_attribute(k, v)
