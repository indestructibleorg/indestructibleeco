"""IndestructibleEco AI Generation Service — FastAPI + Uvicorn.

Runtime: Python 3.11 + FastAPI + Uvicorn
Ports: 8000 (gRPC internal) + 8001 (HTTP)
Vector alignment: quantum-bert-xxl-v1 · dim 1024–4096 · tol 0.0001–0.005
Queuing: Celery + Redis for async inference jobs
"""

import os
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .config import settings
from .routes import router as api_router
from .governance import GovernanceEngine


# ─── Startup / Shutdown ───
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.start_time = time.time()
    app.state.governance = GovernanceEngine()
    yield


app = FastAPI(
    title="IndestructibleEco AI Service",
    version="1.0.0",
    docs_url="/docs" if settings.environment != "production" else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


# ─── Health ───
@app.get("/health")
async def health(request: Request):
    uptime = time.time() - request.app.state.start_time
    return {
        "status": "healthy",
        "service": "ai",
        "version": "1.0.0",
        "uri": "indestructibleeco://backend/ai/health",
        "urn": f"urn:indestructibleeco:backend:ai:health:{uuid.uuid1()}",
        "uptime_seconds": round(uptime, 2),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/metrics")
async def metrics(request: Request):
    uptime = time.time() - request.app.state.start_time
    import resource
    mem = resource.getrusage(resource.RUSAGE_SELF)
    lines = [
        "# HELP ai_uptime_seconds AI service uptime in seconds",
        "# TYPE ai_uptime_seconds gauge",
        f"ai_uptime_seconds {uptime:.2f}",
        "# HELP ai_memory_maxrss_bytes Maximum resident set size",
        "# TYPE ai_memory_maxrss_bytes gauge",
        f"ai_memory_maxrss_bytes {mem.ru_maxrss * 1024}",
    ]
    return JSONResponse(
        content="\n".join(lines) + "\n",
        media_type="text/plain; version=0.0.4",
    )