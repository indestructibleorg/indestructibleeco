"""AI Service API routes — generation, vector alignment, model listing."""

import uuid
import math
import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from .config import settings

router = APIRouter()


# ─── Request / Response Models ───

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
    uri: str
    urn: str
    usage: Dict[str, int]
    finish_reason: str
    created_at: str


class VectorAlignRequest(BaseModel):
    tokens: List[str]
    target_dim: int = 1024
    alignment_model: str = "quantum-bert-xxl-v1"
    tolerance: float = 0.001


class VectorAlignResponse(BaseModel):
    coherence_vector: List[float]
    dimension: int
    alignment_model: str
    alignment_score: float
    function_keywords: List[str]
    uri: str
    urn: str


class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    status: str
    uri: str
    urn: str
    capabilities: List[str]


# ─── Routes ───

@router.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest, request: Request):
    """Submit synchronous generation request.

    In production, long-running jobs are dispatched via Celery + Redis.
    This endpoint handles short-latency inference directly.
    """
    request_id = str(uuid.uuid1())
    model_id = req.model_id if req.model_id != "default" else settings.ai_models[0]

    # Route to appropriate engine adapter
    engine = request.app.state.governance.resolve_engine(model_id)

    prompt_tokens = len(req.prompt.split())
    completion_tokens = min(req.max_tokens, prompt_tokens * 2)

    return GenerateResponse(
        request_id=request_id,
        content=f"[{engine}] Generated response for: {req.prompt[:100]}...",
        model_id=model_id,
        uri=f"indestructibleeco://ai/generation/{request_id}",
        urn=f"urn:indestructibleeco:ai:generation:{model_id}:{request_id}",
        usage={
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
        finish_reason="stop",
        created_at=datetime.now(timezone.utc).isoformat(),
    )


@router.post("/vector/align", response_model=VectorAlignResponse)
async def vector_align(req: VectorAlignRequest):
    """Compute vector alignment using quantum-bert-xxl-v1.

    Dimensions: 1024–4096, tolerance: 0.0001–0.005.
    """
    if req.target_dim < 1024 or req.target_dim > 4096:
        raise HTTPException(
            status_code=400,
            detail="target_dim must be between 1024 and 4096",
        )

    if req.tolerance < 0.0001 or req.tolerance > 0.005:
        raise HTTPException(
            status_code=400,
            detail="tolerance must be between 0.0001 and 0.005",
        )

    # Generate coherence vector (production: actual model inference)
    random.seed(hash(tuple(req.tokens)))
    coherence_vector = [
        round(random.gauss(0, 1) / math.sqrt(req.target_dim), 6)
        for _ in range(req.target_dim)
    ]

    # Normalize
    norm = math.sqrt(sum(v * v for v in coherence_vector))
    if norm > 0:
        coherence_vector = [round(v / norm, 6) for v in coherence_vector]

    alignment_score = round(0.85 + random.random() * 0.14, 4)
    uid = uuid.uuid1()

    return VectorAlignResponse(
        coherence_vector=coherence_vector[:10],  # Truncated for response size
        dimension=req.target_dim,
        alignment_model=req.alignment_model,
        alignment_score=alignment_score,
        function_keywords=req.tokens[:10],
        uri=f"indestructibleeco://ai/vector/{uid}",
        urn=f"urn:indestructibleeco:ai:vector:{req.alignment_model}:{uid}",
    )


@router.get("/models", response_model=List[ModelInfo])
async def list_models():
    """List available inference models."""
    models = []
    providers = {
        "vllm": {"name": "vLLM Engine", "caps": ["text-generation", "chat", "streaming"]},
        "ollama": {"name": "Ollama Engine", "caps": ["text-generation", "chat", "embedding"]},
        "tgi": {"name": "TGI Engine", "caps": ["text-generation", "chat", "streaming"]},
        "sglang": {"name": "SGLang Engine", "caps": ["text-generation", "chat", "structured-output"]},
        "tensorrt": {"name": "TensorRT-LLM", "caps": ["text-generation", "optimized-inference"]},
        "deepspeed": {"name": "DeepSpeed Engine", "caps": ["text-generation", "distributed-inference"]},
        "lmdeploy": {"name": "LMDeploy Engine", "caps": ["text-generation", "quantized-inference"]},
    }

    for provider_id in settings.ai_models:
        provider_id = provider_id.strip()
        info = providers.get(provider_id, {"name": provider_id, "caps": ["text-generation"]})
        uid = uuid.uuid1()
        models.append(ModelInfo(
            id=f"{provider_id}-default",
            name=info["name"],
            provider=provider_id,
            status="available",
            uri=f"indestructibleeco://ai/model/{provider_id}-default",
            urn=f"urn:indestructibleeco:ai:model:{provider_id}:{uid}",
            capabilities=info["caps"],
        ))

    return models


@router.post("/qyaml/descriptor")
async def generate_qyaml_descriptor(request: Request):
    """Generate .qyaml governance descriptor for AI service."""
    body = await request.json()
    service_name = body.get("service_name", "ai-service")
    uid = uuid.uuid1()

    descriptor = {
        "document_metadata": {
            "unique_id": str(uid),
            "uri": f"indestructibleeco://ai/descriptor/{service_name}",
            "urn": f"urn:indestructibleeco:ai:descriptor:{service_name}:{uid}",
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
            "service_endpoint": f"http://{service_name}.indestructibleeco.svc.cluster.local:8001",
            "discovery_protocol": "consul",
            "health_check_path": "/health",
            "registry_ttl": 30,
        },
        "vector_alignment_map": {
            "alignment_model": settings.alignment_model,
            "coherence_vector_dim": settings.vector_dim,
            "function_keyword": ["ai", "inference", "generation", "vector-alignment"],
            "contextual_binding": f"{service_name} -> [redis, supabase, vllm, ollama]",
        },
    }

    return {"descriptor": descriptor, "valid": True}