"""FastAPI application entry point for AI Engine Service."""
from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response

from .config import settings

REQUEST_COUNT = Counter("eco_ai_requests_total", "Total requests", ["method", "endpoint", "status"])
REQUEST_LATENCY = Histogram("eco_ai_request_duration_seconds", "Request latency", ["method", "endpoint"])


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize and teardown engine connections."""
    from .engines.folding.vector_folding import VectorFoldingEngine
    from .engines.folding.graph_folding import GraphFoldingEngine
    from .engines.folding.hybrid_folding import HybridFoldingOrchestrator
    from .engines.compute.similarity import SimilarityEngine
    from .engines.compute.clustering import ClusteringEngine
    from .engines.compute.reasoning import ReasoningEngine
    from .engines.compute.ranking import RankingEngine
    from .engines.index.faiss_index import FAISSIndexAdapter
    from .engines.index.neo4j_index import Neo4jIndexAdapter
    from .engines.index.elasticsearch_index import ElasticsearchIndexAdapter
    from .engines.index.hybrid_router import HybridIndexRouter

    app.state.vector_folding = VectorFoldingEngine()
    app.state.graph_folding = GraphFoldingEngine()
    app.state.hybrid_folding = HybridFoldingOrchestrator(
        vector_engine=app.state.vector_folding,
        graph_engine=app.state.graph_folding,
    )
    app.state.similarity = SimilarityEngine()
    app.state.clustering = ClusteringEngine()
    app.state.reasoning = ReasoningEngine()
    app.state.ranking = RankingEngine()
    app.state.faiss_index = FAISSIndexAdapter()
    app.state.neo4j_index = Neo4jIndexAdapter()
    app.state.es_index = ElasticsearchIndexAdapter()
    app.state.hybrid_index = HybridIndexRouter(
        faiss=app.state.faiss_index,
        neo4j=app.state.neo4j_index,
        elasticsearch=app.state.es_index,
    )

    await app.state.faiss_index.initialize()
    await app.state.neo4j_index.initialize()
    await app.state.es_index.initialize()

    yield

    await app.state.neo4j_index.close()
    await app.state.es_index.close()


def create_app() -> FastAPI:
    """Factory function to create the FastAPI application."""
    app = FastAPI(
        title="IndestructibleEco AI Engine",
        description="Code Folding, Compute, Index, and Service Engines",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        endpoint = request.url.path
        REQUEST_COUNT.labels(request.method, endpoint, response.status_code).inc()
        REQUEST_LATENCY.labels(request.method, endpoint).observe(duration)
        return response

    from .routes import folding_router, compute_router, index_router, health_router
    app.include_router(health_router, prefix="/health", tags=["health"])
    app.include_router(folding_router, prefix="/v1/folding", tags=["folding"])
    app.include_router(compute_router, prefix="/v1/compute", tags=["compute"])
    app.include_router(index_router, prefix="/v1/index", tags=["index"])

    @app.get("/metrics")
    async def prometheus_metrics():
        return Response(content=generate_latest(), media_type="text/plain; charset=utf-8")

    return app


app = create_app()