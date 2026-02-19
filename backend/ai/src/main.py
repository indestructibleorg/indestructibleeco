"""
indestructibleeco AI Service — FastAPI entry point
Exposes HTTP endpoints (port 8001) and gRPC server (port 8000)
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from prometheus_client import make_asgi_app
from .routes import generate, health, models

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("AI service starting up...")
    yield
    print("AI service shutting down...")

app = FastAPI(
    title="indestructibleeco AI Service",
    version="1.0.0",
    lifespan=lifespan,
)

# Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

app.include_router(health.router)
app.include_router(generate.router, prefix="/api/v1/ai")
app.include_router(models.router,   prefix="/api/v1/ai")