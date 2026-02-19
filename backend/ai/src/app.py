"""IndestructibleEco AI Generation Service -- FastAPI + Uvicorn.

Runtime: Python 3.11 + FastAPI + Uvicorn
Ports: 8000 (gRPC internal) + 8001 (HTTP)
Vector alignment: quantum-bert-xxl-v1, dim 1024-4096, tol 0.0001-0.005
Queuing: Async worker for inference jobs
Engine management: 7 adapters with connection pools + circuit breakers
Embedding: Batch embedding via engine adapters with fallback
gRPC: Internal high-performance inference endpoint
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


def _resolve_engine_endpoints() -> Dict[str, str]:
    """Resolve engine endpoints from ECO_* env vars."""
    return {
        "vllm": os.environ.get("ECO_VLLM_URL", "http://localhost:8100"),
        "tgi": os.environ.get("ECO_TGI_URL", "http://localhost:8101"),
        "ollama": os.environ.get("ECO_OLLAMA_URL", "http://localhost:11434"),
        "sglang": os.environ.get("ECO_SGLANG_URL", "http://localhost:8102"),
        "tensorrt": os.environ.get("ECO_TENSORRT_URL", "http://localhost:8103"),
        "deepspeed": os.environ.get("ECO_DEEPSPEED_URL", "http://localhost:8104"),
        "lmdeploy": os.environ.get("ECO_LMDEPLOY_URL", "http://localhost:8105"),
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.start_time = time.time()
    app.state.governance = GovernanceEngine()

    # --- Engine Manager ---
    from .services.engine_manager import EngineManager

    endpoints = _resolve_engine_endpoints()
    engine_mgr = EngineManager(
        endpoints=endpoints,
        failure_threshold=3,
        recovery_timeout=30.0,
    )
    await engine_mgr.initialize()
    app.state.engine_manager = engine_mgr

    # --- Embedding Service ---
    from .services.embedding import EmbeddingService

    embedding_svc = EmbeddingService(
        engine_manager=engine_mgr,
        default_model=settings.alignment_model,
        default_dimensions=settings.vector_dim,
    )
    app.state.embedding_service = embedding_svc

    # --- Inference Worker ---
    from .services.worker import InferenceWorker

    worker = InferenceWorker(
        engine_manager=engine_mgr,
        max_queue_size=int(os.environ.get("ECO_WORKER_QUEUE_SIZE", "10000")),
        stale_timeout=float(os.environ.get("ECO_WORKER_STALE_TIMEOUT", "600")),
    )
    worker_concurrency = int(os.environ.get("ECO_WORKER_CONCURRENCY", "4"))
    await worker.start(concurrency=worker_concurrency)
    app.state.inference_worker = worker

    # --- gRPC Server ---
    from .services.grpc_server import GrpcServer, GrpcServiceConfig

    grpc_config = GrpcServiceConfig(
        port=settings.grpc_port,
        max_workers=int(os.environ.get("ECO_GRPC_MAX_WORKERS", "10")),
        max_concurrent_rpcs=int(os.environ.get("ECO_GRPC_MAX_CONCURRENT", "100")),
    )
    grpc_server = GrpcServer(
        config=grpc_config,
        engine_manager=engine_mgr,
        embedding_service=embedding_svc,
    )
    await grpc_server.start()
    app.state.grpc_server = grpc_server

    yield

    # --- Shutdown ---
    await grpc_server.stop()
    await worker.shutdown()
    await engine_mgr.shutdown()


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


@app.get("/health")
async def health(request: Request):
    uptime = time.time() - request.app.state.start_time
    engine_mgr = getattr(request.app.state, "engine_manager", None)
    available_engines = engine_mgr.list_available_engines() if engine_mgr else []

    worker = getattr(request.app.state, "inference_worker", None)
    worker_running = worker._running if worker else False

    grpc = getattr(request.app.state, "grpc_server", None)
    grpc_running = grpc.is_running if grpc else False

    return {
        "status": "healthy",
        "service": "ai",
        "version": "1.0.0",
        "uri": "indestructibleeco://backend/ai/health",
        "urn": f"urn:indestructibleeco:backend:ai:health:{uuid.uuid1()}",
        "uptime_seconds": round(uptime, 2),
        "engines": available_engines,
        "worker": {"running": worker_running},
        "grpc": {"running": grpc_running, "port": settings.grpc_port},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health/engines")
async def engine_health(request: Request):
    """Detailed engine health with circuit breaker states."""
    engine_mgr = getattr(request.app.state, "engine_manager", None)
    if not engine_mgr:
        return {"error": "engine manager not initialized"}
    return engine_mgr.get_health()


@app.get("/health/worker")
async def worker_health(request: Request):
    """Worker queue depth and job statistics."""
    worker = getattr(request.app.state, "inference_worker", None)
    if not worker:
        return {"error": "worker not initialized"}
    return worker.get_stats()


@app.get("/health/grpc")
async def grpc_health(request: Request):
    """gRPC server metrics."""
    grpc = getattr(request.app.state, "grpc_server", None)
    if not grpc:
        return {"error": "grpc server not initialized"}
    return grpc.get_metrics()


@app.get("/health/embedding")
async def embedding_health(request: Request):
    """Embedding service statistics."""
    embedding_svc = getattr(request.app.state, "embedding_service", None)
    if not embedding_svc:
        return {"error": "embedding service not initialized"}
    return embedding_svc.get_stats()


@app.get("/metrics")
async def metrics(request: Request):
    uptime = time.time() - request.app.state.start_time
    import resource
    mem = resource.getrusage(resource.RUSAGE_SELF)

    engine_mgr = getattr(request.app.state, "engine_manager", None)
    engine_lines = []
    if engine_mgr:
        for name, h in engine_mgr._health.items():
            engine_lines.extend([
                f'eco_engine_requests_total{{engine="{name}"}} {h.total_requests}',
                f'eco_engine_errors_total{{engine="{name}"}} {h.total_errors}',
                f'eco_engine_latency_ms{{engine="{name}"}} {h.latency_ms:.2f}',
                f'eco_engine_available{{engine="{name}"}} {1 if h.is_available else 0}',
            ])

    worker = getattr(request.app.state, "inference_worker", None)
    worker_lines = []
    if worker:
        worker_lines.extend([
            f"eco_worker_submitted_total {worker.total_submitted}",
            f"eco_worker_completed_total {worker.total_completed}",
            f"eco_worker_failed_total {worker.total_failed}",
            f"eco_worker_timeout_total {worker.total_timeout}",
            f"eco_worker_queue_depth {worker._queue.qsize()}",
        ])

    embedding_svc = getattr(request.app.state, "embedding_service", None)
    embedding_lines = []
    if embedding_svc:
        embedding_lines.extend([
            f"eco_embedding_requests_total {embedding_svc.total_requests}",
            f"eco_embedding_tokens_total {embedding_svc.total_tokens}",
            f"eco_embedding_vectors_total {embedding_svc.total_vectors}",
            f"eco_embedding_errors_total {embedding_svc.total_errors}",
        ])

    grpc = getattr(request.app.state, "grpc_server", None)
    grpc_lines = []
    if grpc:
        sm = grpc.servicer.get_metrics()
        grpc_lines.extend([
            f"eco_grpc_requests_total {sm['total_requests']}",
            f"eco_grpc_errors_total {sm['total_errors']}",
            f"eco_grpc_stream_requests_total {sm['total_stream_requests']}",
            f"eco_grpc_embedding_requests_total {sm['total_embedding_requests']}",
        ])

    lines = [
        "# HELP eco_uptime_seconds AI service uptime in seconds",
        "# TYPE eco_uptime_seconds gauge",
        f"eco_uptime_seconds {uptime:.2f}",
        "# HELP eco_memory_maxrss_bytes Maximum resident set size",
        "# TYPE eco_memory_maxrss_bytes gauge",
        f"eco_memory_maxrss_bytes {mem.ru_maxrss * 1024}",
        "# HELP eco_engine_requests_total Total requests per engine",
        "# TYPE eco_engine_requests_total counter",
        "# HELP eco_engine_errors_total Total errors per engine",
        "# TYPE eco_engine_errors_total counter",
    ] + engine_lines + [
        "# HELP eco_worker_submitted_total Total jobs submitted to worker",
        "# TYPE eco_worker_submitted_total counter",
    ] + worker_lines + [
        "# HELP eco_embedding_requests_total Total embedding requests",
        "# TYPE eco_embedding_requests_total counter",
    ] + embedding_lines + [
        "# HELP eco_grpc_requests_total Total gRPC requests",
        "# TYPE eco_grpc_requests_total counter",
    ] + grpc_lines

    return JSONResponse(
        content="\n".join(lines) + "\n",
        media_type="text/plain; version=0.0.4",
    )