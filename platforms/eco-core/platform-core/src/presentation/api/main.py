"""
Platform Core — Shared Kernel FastAPI Application Entry Point
ECO Namespace: eco-core | Port: 8080
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from presentation.api.routes import health


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    # Startup
    yield
    # Shutdown


app = FastAPI(
    title="Platform Core — Shared Kernel",
    description="Auth Service, Memory Hub, Event Bus, Policy & Audit, Infra Manager",
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


def run():
    """CLI entry point."""
    import uvicorn

    uvicorn.run(
        "presentation.api.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
    )
