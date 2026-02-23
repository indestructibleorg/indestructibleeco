"""AI Service API routes — generation, vector alignment, model listing,
embedding, async jobs, OpenAI-compatible chat/completions/embeddings.

Routes dispatch to EngineManager for real inference with failover,
EmbeddingService for vector embeddings, InferenceWorker for async jobs,
and ModelRegistry for model resolution.

OpenAI-compatible endpoints:
  POST /v1/chat/completions  — ChatCompletionRequest/Response
  POST /v1/completions       — CompletionRequest
  POST /v1/embeddings        — EmbeddingRequest (OpenAI format)
  GET  /v1/models            — ModelInfo list from registry

Legacy endpoints (kept for backward compat):
  POST /generate             — simple prompt-based generation
  POST /vector/align         — vector alignment
  POST /embeddings           — eco embedding format
  POST /embeddings/similarity
  POST /jobs, GET /jobs, etc — async job management
  POST /qyaml/descriptor     — governance descriptor
"""

import uuid
import math
import random
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .config import settings

router = APIRouter()


# ─── Legacy Request / Response Models ─────────────────────────────────────────

class GenerateRequest(BaseModel):
    prompt: str
    model_id: str = "default"
    params: Dict[str, Any] = Field(default_factory=dict)
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 0.9


class GenerateResponse(BaseModel):
    request_id: str
    content: str
    model_id: str
    engine: str
    uri: str
    urn: str
    usage: Dict[str, int]
    finish_reason: str
    latency_ms: float
    created_at: str


class VectorAlignRequest(BaseModel):
    tokens: List[str]
    target_dim: int = 1024
    alignment_model: str = "BAAI/bge-large-en-v1.5"
    tolerance: float = 0.001


class VectorAlignResponse(BaseModel):
    coherence_vector: List[float]
    dimension: int
    alignment_model: str
    alignment_score: float
    function_keywords: List[str]
    uri: str
    urn: str


class LegacyModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    status: str
    uri: str
    urn: str
    capabilities: List[str]


class EmbedRequest(BaseModel):
    input: Any
    model: str = "default"
    dimensions: int = 1024
    encoding_format: str = "float"


class EmbedResponse(BaseModel):
    request_id: str
    data: List[Dict[str, Any]]
    model: str
    dimensions: int
    total_tokens: int
    latency_ms: float
    uri: str
    urn: str


class SimilarityRequest(BaseModel):
    text_a: str
    text_b: str
    model: str = "default"
    dimensions: int = 1024


class SimilarityResponse(BaseModel):
    text_a: str
    text_b: str
    cosine_similarity: float
    euclidean_distance: float
    model: str
    uri: str
    urn: str


class AsyncJobRequest(BaseModel):
    prompt: str
    model_id: str = "default"
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 0.9
    priority: str = "normal"
    timeout_seconds: float = 300.0


class AsyncJobResponse(BaseModel):
    job_id: str
    status: str
    uri: str
    urn: str
    created_at: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    result: Optional[str] = None
    error: Optional[str] = None
    engine: Optional[str] = None
    usage: Dict[str, int] = Field(default_factory=dict)
    latency_ms: float = 0.0
    uri: str
    urn: str
    created_at: str
    completed_at: Optional[str] = None


# ─── OpenAI-Compatible Models (using shared schemas) ─────────────────────────

class OAIChatMessage(BaseModel):
    role: str
    content: str
    name: Optional[str] = None


class OAIChatCompletionRequest(BaseModel):
    model: str = "default"
    messages: List[OAIChatMessage]
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    max_tokens: int = Field(default=2048, ge=1, le=131072)
    stream: bool = False
    stop: Optional[List[str]] = None
    seed: Optional[int] = None
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)


class OAICompletionRequest(BaseModel):
    model: str = "default"
    prompt: Union[str, List[str]] = ""
    max_tokens: int = Field(default=2048, ge=1, le=131072)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    stream: bool = False
    stop: Optional[List[str]] = None


class OAIEmbeddingRequest(BaseModel):
    input: Union[str, List[str]]
    model: str = "default"
    encoding_format: str = "float"
    dimensions: Optional[int] = None


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _resolve_model_id(request: Request, model_id: str) -> str:
    """Resolve model_id through ModelRegistry, falling back to config."""
    if model_id == "default":
        registry = getattr(request.app.state, "model_registry", None)
        if registry:
            resolved = await registry.resolve_model("default")
            if resolved:
                return resolved.model_id
        return settings.ai_models[0]

    registry = getattr(request.app.state, "model_registry", None)
    if registry:
        resolved = await registry.resolve_model(model_id)
        if resolved:
            return resolved.model_id

    return model_id


async def _generate_via_engine(
    request: Request,
    model_id: str,
    prompt: str,
    max_tokens: int = 2048,
    temperature: float = 0.7,
    top_p: float = 0.9,
) -> Dict[str, Any]:
    """Dispatch generation to EngineManager with registry-resolved model."""
    resolved_model = await _resolve_model_id(request, model_id)

    engine_mgr = getattr(request.app.state, "engine_manager", None)
    if engine_mgr:
        result = await engine_mgr.generate(
            model_id=resolved_model,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )
        result["model_id"] = resolved_model
        return result

    # Fallback
    governance = getattr(request.app.state, "governance", None)
    engine = governance.resolve_engine(resolved_model) if governance else "fallback"
    prompt_tokens = len(prompt.split())
    completion_tokens = min(max_tokens, prompt_tokens * 2)
    return {
        "content": f"[{engine}] Generated response for: {prompt[:100]}...",
        "model_id": resolved_model,
        "engine": engine,
        "finish_reason": "stop",
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
        "latency_ms": 0,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# OpenAI-Compatible Routes
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/v1/chat/completions")
async def chat_completions(req: OAIChatCompletionRequest, request: Request):
    """OpenAI-compatible chat completion endpoint.

    Resolves model through ModelRegistry, dispatches to EngineManager.
    Supports streaming via SSE when stream=True.
    """
    resolved_model = await _resolve_model_id(request, req.model)

    # Build prompt from messages
    prompt_parts: List[str] = []
    for msg in req.messages:
        prompt_parts.append(f"{msg.role}: {msg.content}")
    prompt = "\n".join(prompt_parts)

    start = time.monotonic()
    result = await _generate_via_engine(
        request,
        model_id=resolved_model,
        prompt=prompt,
        max_tokens=req.max_tokens,
        temperature=req.temperature,
        top_p=req.top_p,
    )
    elapsed = (time.monotonic() - start) * 1000

    request_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
    content = result.get("content", "")
    usage = result.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})

    if req.stream:
        import json

        async def stream_generator():
            words = content.split()
            chunk_size = max(1, len(words) // 5) if words else 1
            chunks = [
                " ".join(words[i:i + chunk_size])
                for i in range(0, len(words), chunk_size)
            ]
            for idx, chunk_text in enumerate(chunks):
                is_last = idx == len(chunks) - 1
                chunk_data = {
                    "id": request_id,
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": resolved_model,
                    "choices": [{
                        "index": 0,
                        "delta": {"content": chunk_text} if not is_last else {},
                        "finish_reason": "stop" if is_last else None,
                    }],
                }
                yield f"data: {json.dumps(chunk_data)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    return {
        "id": request_id,
        "object": "chat.completion",
        "created": int(time.time()),
        "model": resolved_model,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": content},
            "finish_reason": result.get("finish_reason", "stop"),
        }],
        "usage": usage,
        "system_fingerprint": f"eco-{result.get('engine', 'unknown')}",
    }


@router.post("/v1/completions")
async def completions(req: OAICompletionRequest, request: Request):
    """OpenAI-compatible legacy completion endpoint."""
    resolved_model = await _resolve_model_id(request, req.model)

    prompt = req.prompt if isinstance(req.prompt, str) else " ".join(req.prompt)

    start = time.monotonic()
    result = await _generate_via_engine(
        request,
        model_id=resolved_model,
        prompt=prompt,
        max_tokens=req.max_tokens,
        temperature=req.temperature,
        top_p=req.top_p,
    )
    elapsed = (time.monotonic() - start) * 1000

    request_id = f"cmpl-{uuid.uuid4().hex[:12]}"
    content = result.get("content", "")
    usage = result.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})

    return {
        "id": request_id,
        "object": "text_completion",
        "created": int(time.time()),
        "model": resolved_model,
        "choices": [{
            "index": 0,
            "text": content,
            "finish_reason": result.get("finish_reason", "stop"),
        }],
        "usage": usage,
    }


@router.post("/v1/embeddings")
async def oai_embeddings(req: OAIEmbeddingRequest, request: Request):
    """OpenAI-compatible embedding endpoint.

    Resolves model through ModelRegistry, dispatches to EmbeddingService.
    """
    embedding_svc = getattr(request.app.state, "embedding_service", None)
    if not embedding_svc:
        raise HTTPException(status_code=503, detail="Embedding service not available")

    resolved_model = await _resolve_model_id(request, req.model)
    texts: List[str] = [req.input] if isinstance(req.input, str) else list(req.input)
    if not texts:
        raise HTTPException(status_code=400, detail="Empty input")

    dim = req.dimensions or settings.vector_dim

    try:
        result = await embedding_svc.embed_batch(
            texts=texts,
            model_id=resolved_model,
            dimensions=dim,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    data = [
        {"object": "embedding", "index": i, "embedding": emb}
        for i, emb in enumerate(result.embeddings)
    ]

    return {
        "object": "list",
        "data": data,
        "model": resolved_model,
        "usage": {
            "prompt_tokens": result.total_tokens,
            "total_tokens": result.total_tokens,
        },
    }


@router.get("/v1/models")
async def oai_list_models(request: Request):
    """OpenAI-compatible model listing from ModelRegistry."""
    registry = getattr(request.app.state, "model_registry", None)
    if not registry:
        raise HTTPException(status_code=503, detail="Model registry not available")

    models = await registry.list_models()
    engine_mgr = getattr(request.app.state, "engine_manager", None)
    available_engines = set(engine_mgr.list_available_engines()) if engine_mgr else set()

    data = []
    for m in models:
        has_available_engine = bool(set(m.compatible_engines) & available_engines)
        data.append({
            "id": m.model_id,
            "object": "model",
            "created": int(time.time()),
            "owned_by": "eco-base",
            "permission": [],
            "root": m.source,
            "parent": None,
            "capabilities": [c.value for c in m.capabilities],
            "compatible_engines": m.compatible_engines,
            "status": m.status.value,
            "engine_available": has_available_engine,
            "context_length": m.context_length,
            "parameters_billion": m.parameters_billion,
        })

    return {"object": "list", "data": data}


# ═══════════════════════════════════════════════════════════════════════════════
# Legacy Routes (backward compatible)
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest, request: Request):
    """Submit synchronous generation request (legacy endpoint)."""
    request_id = str(uuid.uuid1())

    result = await _generate_via_engine(
        request,
        model_id=req.model_id,
        prompt=req.prompt,
        max_tokens=req.max_tokens,
        temperature=req.temperature,
        top_p=req.top_p,
    )

    model_id = result.get("model_id", req.model_id)
    return GenerateResponse(
        request_id=request_id,
        content=result.get("content", ""),
        model_id=model_id,
        engine=result.get("engine", "unknown"),
        uri=f"eco-base://ai/generation/{request_id}",
        urn=f"urn:eco-base:ai:generation:{model_id}:{request_id}",
        usage=result.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}),
        finish_reason=result.get("finish_reason", "stop"),
        latency_ms=result.get("latency_ms", 0),
        created_at=datetime.now(timezone.utc).isoformat(),
    )


@router.post("/vector/align", response_model=VectorAlignResponse)
async def vector_align(req: VectorAlignRequest):
    """Compute vector alignment via real embedding similarity.

    Embeds the provided tokens as a single sentence using EmbeddingService,
    which dispatches to an engine adapter when available and falls back to
    sentence-transformers local inference or deterministic hash-based vectors.
    """
    if req.target_dim < 1024 or req.target_dim > 4096:
        raise HTTPException(status_code=400, detail="target_dim must be between 1024 and 4096")
    if req.tolerance < 0.0001 or req.tolerance > 0.005:
        raise HTTPException(status_code=400, detail="tolerance must be between 0.0001 and 0.005")

    from .services.embedding import EmbeddingService  # local import to avoid circular deps

    svc = EmbeddingService(
        default_model=req.alignment_model,
        default_dimensions=req.target_dim,
    )
    sentence = " ".join(req.tokens) if req.tokens else "<empty>"
    result = await svc.embed(sentence, model_id=req.alignment_model, dimensions=req.target_dim)

    coherence_vector = result.embeddings[0] if result.embeddings else []

    # Alignment score: L2-norm of the coherence vector normalised to [0, 1].
    # A well-formed unit vector has norm = 1.0; partial or zero vectors score lower.
    if coherence_vector:
        raw_norm = math.sqrt(sum(v * v for v in coherence_vector))
        alignment_score = round(min(1.0, raw_norm), 4)
    else:
        alignment_score = 0.0
    uid = uuid.uuid1()

    return VectorAlignResponse(
        coherence_vector=coherence_vector[:10],
        dimension=req.target_dim,
        alignment_model=req.alignment_model,
        alignment_score=alignment_score,
        function_keywords=req.tokens[:10],
        uri=f"eco-base://ai/vector/{uid}",
        urn=f"urn:eco-base:ai:vector:{req.alignment_model}:{uid}",
    )


@router.get("/models", response_model=List[LegacyModelInfo])
async def list_models(request: Request):
    """List available inference models (legacy format)."""
    providers = {
        "vllm": {"name": "vLLM Engine", "caps": ["text-generation", "chat", "streaming"]},
        "ollama": {"name": "Ollama Engine", "caps": ["text-generation", "chat", "embedding"]},
        "tgi": {"name": "TGI Engine", "caps": ["text-generation", "chat", "streaming"]},
        "sglang": {"name": "SGLang Engine", "caps": ["text-generation", "chat", "structured-output"]},
        "tensorrt": {"name": "TensorRT-LLM", "caps": ["text-generation", "optimized-inference"]},
        "deepspeed": {"name": "DeepSpeed Engine", "caps": ["text-generation", "distributed-inference"]},
        "lmdeploy": {"name": "LMDeploy Engine", "caps": ["text-generation", "quantized-inference"]},
    }

    engine_mgr = getattr(request.app.state, "engine_manager", None)
    available = set()
    if engine_mgr:
        available = set(engine_mgr.list_available_engines())

    models = []
    for provider_id in settings.ai_models:
        provider_id = provider_id.strip()
        info = providers.get(provider_id, {"name": provider_id, "caps": ["text-generation"]})
        uid = uuid.uuid1()
        status = "available" if provider_id in available else "registered"
        models.append(LegacyModelInfo(
            id=f"{provider_id}-default",
            name=info["name"],
            provider=provider_id,
            status=status,
            uri=f"eco-base://ai/model/{provider_id}-default",
            urn=f"urn:eco-base:ai:model:{provider_id}:{uid}",
            capabilities=info["caps"],
        ))

    return models


# ─── Embedding Routes (eco format) ───────────────────────────────────────────

@router.post("/embeddings", response_model=EmbedResponse)
async def create_embeddings(req: EmbedRequest, request: Request):
    """Generate embeddings for text input(s) (eco format)."""
    embedding_svc = getattr(request.app.state, "embedding_service", None)
    if not embedding_svc:
        raise HTTPException(status_code=503, detail="Embedding service not available")

    texts: List[str] = [req.input] if isinstance(req.input, str) else list(req.input)
    if not texts:
        raise HTTPException(status_code=400, detail="Empty input")

    model = req.model if req.model != "default" else settings.alignment_model

    try:
        result = await embedding_svc.embed_batch(texts=texts, model_id=model, dimensions=req.dimensions)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    uid = uuid.uuid1()
    data = [
        {"object": "embedding", "index": i, "embedding": emb}
        for i, emb in enumerate(result.embeddings)
    ]

    return EmbedResponse(
        request_id=result.request_id,
        data=data,
        model=model,
        dimensions=result.dimensions,
        total_tokens=result.total_tokens,
        latency_ms=round(result.latency_ms, 2),
        uri=f"eco-base://ai/embedding/{uid}",
        urn=f"urn:eco-base:ai:embedding:{model}:{uid}",
    )


@router.post("/embeddings/similarity", response_model=SimilarityResponse)
async def compute_similarity(req: SimilarityRequest, request: Request):
    """Compute cosine similarity and Euclidean distance between two texts."""
    embedding_svc = getattr(request.app.state, "embedding_service", None)
    if not embedding_svc:
        raise HTTPException(status_code=503, detail="Embedding service not available")

    model = req.model if req.model != "default" else settings.alignment_model

    try:
        result = await embedding_svc.similarity(
            text_a=req.text_a, text_b=req.text_b, model_id=model, dimensions=req.dimensions,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    uid = uuid.uuid1()
    return SimilarityResponse(
        text_a=result.text_a[:100],
        text_b=result.text_b[:100],
        cosine_similarity=round(result.cosine_similarity, 6),
        euclidean_distance=round(result.euclidean_distance, 6),
        model=model,
        uri=f"eco-base://ai/similarity/{uid}",
        urn=f"urn:eco-base:ai:similarity:{model}:{uid}",
    )


# ─── Async Job Routes ────────────────────────────────────────────────────────

@router.post("/jobs", response_model=AsyncJobResponse)
async def submit_job(req: AsyncJobRequest, request: Request):
    """Submit an async inference job to the worker queue."""
    worker = getattr(request.app.state, "inference_worker", None)
    if not worker:
        raise HTTPException(status_code=503, detail="Inference worker not available")

    from .services.worker import InferenceJob, JobPriority

    priority_map = {"high": JobPriority.HIGH, "normal": JobPriority.NORMAL, "low": JobPriority.LOW}
    priority = priority_map.get(req.priority, JobPriority.NORMAL)

    resolved_model = await _resolve_model_id(request, req.model_id)

    job = InferenceJob(
        model_id=resolved_model,
        prompt=req.prompt,
        max_tokens=req.max_tokens,
        temperature=req.temperature,
        top_p=req.top_p,
        priority=priority,
        timeout_seconds=req.timeout_seconds,
    )

    try:
        job_id = await worker.submit(job)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    return AsyncJobResponse(
        job_id=job_id,
        status=job.status.value,
        uri=f"eco-base://ai/job/{job_id}",
        urn=f"urn:eco-base:ai:job:{resolved_model}:{job_id}",
        created_at=datetime.fromtimestamp(job.created_at, tz=timezone.utc).isoformat(),
    )


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job(job_id: str, request: Request):
    """Get status and result of an async inference job."""
    worker = getattr(request.app.state, "inference_worker", None)
    if not worker:
        raise HTTPException(status_code=503, detail="Inference worker not available")

    job = worker.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status.value,
        result=job.result,
        error=job.error,
        engine=job.engine,
        usage=job.usage,
        latency_ms=job.latency_ms,
        uri=f"eco-base://ai/job/{job.job_id}",
        urn=f"urn:eco-base:ai:job:{job.model_id}:{job.job_id}",
        created_at=datetime.fromtimestamp(job.created_at, tz=timezone.utc).isoformat(),
        completed_at=(
            datetime.fromtimestamp(job.completed_at, tz=timezone.utc).isoformat()
            if job.completed_at else None
        ),
    )


@router.get("/jobs")
async def list_jobs(request: Request, status: Optional[str] = None, limit: int = 100):
    """List async inference jobs, optionally filtered by status."""
    worker = getattr(request.app.state, "inference_worker", None)
    if not worker:
        raise HTTPException(status_code=503, detail="Inference worker not available")

    from .services.worker import JobStatus as WJobStatus

    filter_status = None
    if status:
        try:
            filter_status = WJobStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    jobs = worker.list_jobs(status=filter_status, limit=limit)
    return [j.to_dict() for j in jobs]


@router.delete("/jobs/{job_id}")
async def cancel_job(job_id: str, request: Request):
    """Cancel a pending async inference job."""
    worker = getattr(request.app.state, "inference_worker", None)
    if not worker:
        raise HTTPException(status_code=503, detail="Inference worker not available")

    cancelled = await worker.cancel(job_id)
    if not cancelled:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found or not cancellable")

    return {"job_id": job_id, "status": "cancelled"}


# ─── Governance Descriptor ────────────────────────────────────────────────────

@router.post("/qyaml/descriptor")
async def generate_qyaml_descriptor(request: Request):
    """Generate .qyaml governance descriptor for AI service."""
    body = await request.json()
    service_name = body.get("service_name", "ai-service")
    uid = uuid.uuid1()

    descriptor = {
        "document_metadata": {
            "unique_id": str(uid),
            "uri": f"eco-base://ai/descriptor/{service_name}",
            "urn": f"urn:eco-base:ai:descriptor:{service_name}:{uid}",
            "target_system": "gke-production",
            "cross_layer_binding": ["redis", "supabase", "vllm", "ollama"],
            "schema_version": "v1",
            "generated_by": "yaml-toolkit-v1",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        "governance_info": {
            "owner": "platform-team",
            "approval_chain": ["platform-team", "ml-team"],
            "compliance_tags": ["zero-trust", "soc2", "internal", "gpu-workload"],
            "lifecycle_policy": "active",
        },
        "registry_binding": {
            "service_endpoint": f"http://{service_name}.eco-base.svc.cluster.local:8001",
            "discovery_protocol": "consul",
            "health_check_path": "/health",
            "registry_ttl": 30,
        },
        "vector_alignment_map": {
            "alignment_model": settings.alignment_model,
            "coherence_vector_dim": settings.vector_dim,
            "function_keyword": ["ai", "inference", "generation", "vector-alignment", "embedding"],
            "contextual_binding": f"{service_name} -> [redis, supabase, vllm, ollama]",
        },
    }

    return {"descriptor": descriptor, "valid": True}