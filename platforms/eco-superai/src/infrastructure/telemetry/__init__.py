"""OpenTelemetry instrumentation — traces, metrics, and context propagation."""
from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger(__name__)


def setup_telemetry(
    service_name: str = "superai-platform",
    otlp_endpoint: str = "http://localhost:4317",
    enabled: bool = True,
    sample_rate: float = 1.0,
) -> Any | None:
    """Initialize OpenTelemetry tracing and metrics exporters.

    Args:
        service_name: Logical service name for traces.
        otlp_endpoint: OTLP gRPC collector endpoint.
        enabled: Master switch for telemetry.
        sample_rate: Trace sampling ratio (0.0–1.0).

    Returns:
        TracerProvider instance or None if disabled / unavailable.
    """
    if not enabled:
        logger.info("telemetry_disabled")
        return None

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
    except ImportError:
        logger.warning("telemetry_import_failed", hint="pip install opentelemetry-sdk opentelemetry-exporter-otlp")
        return None

    resource = Resource.create({
        "service.name": service_name,
        "service.version": "1.0.0",
        "deployment.environment": _get_environment(),
    })

    sampler = TraceIdRatioBased(sample_rate)
    provider = TracerProvider(resource=resource, sampler=sampler)

    exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)

    logger.info(
        "telemetry_initialized",
        service=service_name,
        endpoint=otlp_endpoint,
        sample_rate=sample_rate,
    )
    return provider


def instrument_fastapi(app: Any) -> None:
    """Attach OpenTelemetry instrumentation to a FastAPI application."""
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor.instrument_app(
            app,
            excluded_urls="health,metrics,readiness,liveness",
        )
        logger.info("fastapi_instrumented")
    except ImportError:
        logger.debug("fastapi_instrumentation_skipped", reason="opentelemetry-instrumentation-fastapi not installed")
    except Exception as exc:
        logger.warning("fastapi_instrumentation_failed", error=str(exc))


def instrument_sqlalchemy(engine: Any) -> None:
    """Attach OpenTelemetry instrumentation to a SQLAlchemy engine."""
    try:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        SQLAlchemyInstrumentor().instrument(engine=engine)
        logger.info("sqlalchemy_instrumented")
    except ImportError:
        logger.debug("sqlalchemy_instrumentation_skipped")
    except Exception as exc:
        logger.warning("sqlalchemy_instrumentation_failed", error=str(exc))


def instrument_httpx() -> None:
    """Attach OpenTelemetry instrumentation to httpx HTTP client."""
    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        HTTPXClientInstrumentor().instrument()
        logger.info("httpx_instrumented")
    except ImportError:
        logger.debug("httpx_instrumentation_skipped")
    except Exception as exc:
        logger.warning("httpx_instrumentation_failed", error=str(exc))


def get_tracer(name: str = "superai") -> Any:
    """Get an OpenTelemetry tracer instance."""
    try:
        from opentelemetry import trace
        return trace.get_tracer(name)
    except ImportError:
        return _NoOpTracer()


class _NoOpTracer:
    """Fallback tracer when OpenTelemetry is not installed."""

    def start_as_current_span(self, name: str, **kwargs: Any) -> Any:
        from contextlib import contextmanager

        @contextmanager
        def _noop():
            yield None

        return _noop()


def _get_environment() -> str:
    try:
        from src.infrastructure.config import get_settings
        return get_settings().app_env.value
    except Exception:
        return "unknown"


__all__ = [
    "setup_telemetry",
    "instrument_fastapi",
    "instrument_sqlalchemy",
    "instrument_httpx",
    "get_tracer",
]