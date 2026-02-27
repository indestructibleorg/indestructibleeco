"""
SuperAI Platform - FastAPI Application Factory
Production-grade entry point with full middleware stack.
"""
from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import ORJSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry, REGISTRY

from src.infrastructure.config import get_settings

logger = structlog.get_logger(__name__)

# --- Prometheus Metrics (safe re-registration) ---
def _safe_metric(metric_cls, name, doc, labels, **kwargs):
    """Return existing metric or create new one, avoiding duplicate registration."""
    collector = REGISTRY._names_to_collectors.get(name)
    if collector is not None:
        return collector
    # For Counter, prometheus adds _total suffix internally
    base_name = name.rstrip('_total') if name.endswith('_total') else name
    collector = REGISTRY._names_to_collectors.get(base_name)
    if collector is not None:
        return collector  # pragma: no cover
    return metric_cls(name, doc, labels, **kwargs)

REQUEST_COUNT = _safe_metric(Counter, "superai_http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"])
REQUEST_LATENCY = _safe_metric(Histogram, "superai_http_request_duration_seconds", "HTTP request latency", ["method", "endpoint"], buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0])


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle: startup and shutdown."""
    settings = get_settings()
    logger.info("superai_platform_starting", env=settings.app_env.value, version=settings.app_version)

    # Startup: initialize connections
    from src.infrastructure.persistence.database import engine, init_db
    await init_db()
    logger.info("database_initialized")

    yield

    # Shutdown: cleanup
    from src.infrastructure.persistence.database import engine
    await engine.dispose()
    logger.info("superai_platform_shutdown")


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="超級AI自開發雲原生平台 - Quantum-AI Hybrid Framework",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None,
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    # --- Middleware Stack (order matters: last added = first executed) ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors.allowed_origins,
        allow_credentials=settings.cors.allow_credentials,
        allow_methods=settings.cors.allowed_methods,
        allow_headers=settings.cors.allowed_headers,
        max_age=settings.cors.max_age,
    )

    if settings.is_production:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next: Any) -> Response:
        import uuid
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        structlog.contextvars.bind_contextvars(request_id=request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    @app.middleware("http")
    async def timing_middleware(request: Request, call_next: Any) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        response.headers["X-Process-Time"] = f"{duration:.4f}"
        endpoint = request.url.path
        REQUEST_COUNT.labels(method=request.method, endpoint=endpoint, status=response.status_code).inc()
        REQUEST_LATENCY.labels(method=request.method, endpoint=endpoint).observe(duration)
        return response

    # --- Exception Handlers ---
    from src.presentation.exceptions.handlers import register_exception_handlers
    register_exception_handlers(app)

    # --- Routes ---
    from src.presentation.api.routes import health, users, quantum, ai, scientific, admin
    app.include_router(health.router, prefix="/api/v1", tags=["Health"])
    app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
    app.include_router(quantum.router, prefix="/api/v1/quantum", tags=["Quantum Computing"])
    app.include_router(ai.router, prefix="/api/v1/ai", tags=["AI & ML"])
    app.include_router(scientific.router, prefix="/api/v1/scientific", tags=["Scientific Computing"])
    app.include_router(admin.router, prefix="/api/v1/admin", tags=["Administration"])

    # --- Prometheus Metrics Endpoint ---
    @app.get("/metrics", include_in_schema=False)
    async def metrics() -> Response:
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


app = create_app()


def cli() -> None:
    """CLI entry point."""
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "src.presentation.api.main:app",
        host=settings.app_host,
        port=settings.app_port,
        workers=settings.app_workers,
        reload=settings.is_development,
        log_level=settings.log_level,
    )