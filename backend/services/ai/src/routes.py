"""API Routes for AI Engine Service.

Exposes REST endpoints for all engine subsystems:
- /health - Service health and engine status
- /v1/folding - Code folding (vector, graph, hybrid)
- /v1/compute - Similarity, clustering, reasoning, ranking
- /v1/index - FAISS, Neo4j, Elasticsearch, hybrid search
- /v1/chat/completions - OpenAI-compatible inference
- /v1/models - Model registry
"""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

# ── Health Routes ───────────────────────────────────────────
health_router = APIRouter()


@health_router.get("/")
async def health():
    return {"status": "healthy", "service": "indestructibleeco-ai", "version": "1.0.0"}


@health_router.get("/ready")
async def readiness(request: Request):
    checks = {
        "faiss": request.app.state.faiss_index is not None,
        "folding": request.app.state.vector_folding is not None,
        "compute": request.app.state.similarity is not None,
    }
    all_ready = all(checks.values())
    return {"ready": all_ready, "checks": checks}


# ── Folding Routes ──────────────────────────────────────────
folding_router = APIRouter()


class FoldRequest(BaseModel):
    content: str
    content_type: str = "source_code"
    language: str | None = None
    strategy: str = "vector"
    target_dimensions: int | None = None


class FoldBatchRequest(BaseModel):
    items: list[FoldRequest]


@folding_router.post("/fold")
async def fold_content(req: FoldRequest, request: Request):
    if req.strategy == "vector":
        engine = request.app.state.vector_folding
        return engine.fold(req.content, req.content_type, req.language, req.target_dimensions)
    elif req.strategy == "graph":
        engine = request.app.state.graph_folding
        return engine.fold(req.content, req.content_type, req.language)
    elif req.strategy == "hybrid":
        engine = request.app.state.hybrid_folding
        return engine.fold(req.content, req.content_type, req.language, req.target_dimensions)
    else:
        raise HTTPException(400, f"Unknown strategy: {req.strategy}")


@folding_router.post("/fold/batch")
async def fold_batch(req: FoldBatchRequest, request: Request):
    results = []
    for item in req.items:
        if item.strategy == "vector":
            r = request.app.state.vector_folding.fold(item.content, item.content_type, item.language, item.target_dimensions)
        elif item.strategy == "graph":
            r = request.app.state.graph_folding.fold(item.content, item.content_type, item.language)
        else:
            r = request.app.state.hybrid_folding.fold(item.content, item.content_type, item.language, item.target_dimensions)
        results.append(r)
    return {"results": results, "count": len(results)}


# ── Compute Routes ──────────────────────────────────────────
compute_router = APIRouter()


class SimilarityRequest(BaseModel):
    query_vector: list[float]
    candidate_vectors: list[list[float]]
    candidate_ids: list[str]
    metric: str = "cosine"
    top_k: int = 10
    threshold: float | None = None


class ClusterRequest(BaseModel):
    vectors: list[list[float]]
    ids: list[str]
    algorithm: str = "kmeans"
    params: dict[str, Any] = Field(default_factory=dict)


class ReasoningRequest(BaseModel):
    graph_data: dict[str, Any]
    start_node: str
    relation_path: list[str] | None = None
    target_node: str | None = None
    max_depth: int = 10
    reasoning_type: str = "deductive"


class RankRequest(BaseModel):
    query: str
    candidates: list[dict[str, Any]]
    strategy: str = "hybrid"
    query_vector: list[float] | None = None
    top_k: int = 20


@compute_router.post("/similarity")
async def compute_similarity(req: SimilarityRequest, request: Request):
    engine = request.app.state.similarity
    return engine.compute(
        req.query_vector, req.candidate_vectors, req.candidate_ids,
        req.metric, req.top_k, req.threshold,
    )


@compute_router.post("/cluster")
async def compute_clusters(req: ClusterRequest, request: Request):
    engine = request.app.state.clustering
    return engine.cluster(req.vectors, req.ids, req.algorithm, req.params)


@compute_router.post("/cluster/auto")
async def auto_cluster(req: ClusterRequest, request: Request):
    engine = request.app.state.clustering
    return engine.auto_cluster(req.vectors, req.ids)


@compute_router.post("/reason")
async def compute_reasoning(req: ReasoningRequest, request: Request):
    engine = request.app.state.reasoning
    return engine.reason(
        req.graph_data, req.start_node, req.relation_path,
        req.target_node, req.max_depth, req.reasoning_type,
    )


@compute_router.post("/rank")
async def compute_ranking(req: RankRequest, request: Request):
    engine = request.app.state.ranking
    return engine.rank(req.query, req.candidates, req.strategy, req.query_vector, req.top_k)


# ── Index Routes ────────────────────────────────────────────
index_router = APIRouter()


class IndexIngestRequest(BaseModel):
    entry_id: str
    content: str
    content_type: str = "source_code"
    language: str | None = None
    vector: list[float] | None = None
    graph_data: dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class IndexSearchRequest(BaseModel):
    query_text: str | None = None
    query_vector: list[float] | None = None
    graph_query: str | None = None
    top_k: int = 10
    index_types: list[str] | None = None
    filters: dict[str, Any] = Field(default_factory=dict)


@index_router.post("/ingest")
async def index_ingest(req: IndexIngestRequest, request: Request):
    router = request.app.state.hybrid_index
    result = await router.ingest(
        entry_id=req.entry_id, content=req.content, vector=req.vector,
        graph_data=req.graph_data, content_type=req.content_type,
        language=req.language, metadata=req.metadata,
    )
    return {"status": "ingested", "backends": result}


@index_router.post("/search")
async def index_search(req: IndexSearchRequest, request: Request):
    router = request.app.state.hybrid_index
    return await router.search(
        query_text=req.query_text, query_vector=req.query_vector,
        graph_query=req.graph_query, top_k=req.top_k,
        index_types=req.index_types, filters=req.filters,
    )


@index_router.get("/stats")
async def index_stats(request: Request):
    router = request.app.state.hybrid_index
    return await router.get_stats()