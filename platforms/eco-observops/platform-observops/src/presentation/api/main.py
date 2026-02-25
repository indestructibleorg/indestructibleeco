"""
ObservOps Platform — FastAPI Application Entry Point
ECO Namespace: eco-observops | Port: 8093
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from presentation.api.routes import health, metrics, alerts, traces


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    yield


app = FastAPI(
    title="ObservOps Platform",
    description="Observability Operations Platform — metrics collection, alert management, distributed tracing, and health monitoring.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["metrics"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["alerts"])
app.include_router(traces.router, prefix="/api/v1/traces", tags=["traces"])


def run():
    """CLI entry point."""
    import uvicorn
    uvicorn.run(
        "presentation.api.main:app",
        host="0.0.0.0",
        port=8093,
        reload=True,
    )
