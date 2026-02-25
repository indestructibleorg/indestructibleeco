"""
DataOps Platform — FastAPI Application Entry Point
Data & Evidence Operations Platform API
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from presentation.api.routes import health, evidence, replay, anomaly, quality


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    # Startup
    yield
    # Shutdown


app = FastAPI(
    title="DataOps Platform",
    description="Data & Evidence Operations Platform — evidence pipeline lifecycle, replay engine, semantic processing, anomaly detection, and data quality governance.",
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

# Register routers
app.include_router(health.router, tags=["health"])
app.include_router(evidence.router, prefix="/api/v1/evidence", tags=["evidence"])
app.include_router(replay.router, prefix="/api/v1/replay", tags=["replay"])
app.include_router(anomaly.router, prefix="/api/v1/anomaly", tags=["anomaly"])
app.include_router(quality.router, prefix="/api/v1/quality", tags=["quality"])


def run():
    """CLI entry point."""
    import uvicorn

    uvicorn.run(
        "presentation.api.main:app",
        host="0.0.0.0",
        port=8092,
        reload=True,
    )
