"""
SecCompOps Platform — FastAPI Application Entry Point
Security & Compliance Operations Platform API
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from presentation.api.routes import health, enforcement, audit, compliance


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    # Startup
    yield
    # Shutdown


app = FastAPI(
    title="SecCompOps Platform",
    description="Security & Compliance Operations Platform — zero-tolerance enforcement, hallucination detection, evidence chain governance, and immutable audit.",
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
app.include_router(enforcement.router, prefix="/api/v1/enforcement", tags=["enforcement"])
app.include_router(audit.router, prefix="/api/v1/audit", tags=["audit"])
app.include_router(compliance.router, prefix="/api/v1/compliance", tags=["compliance"])


def run():
    """CLI entry point."""
    import uvicorn

    uvicorn.run(
        "presentation.api.main:app",
        host="0.0.0.0",
        port=8095,
        reload=True,
    )
