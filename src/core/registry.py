"""Model Registry — central model lifecycle management.

URI: indestructibleeco://src/core/registry

Contracts defined by: tests/unit/test_registry.py
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..schemas.models import (
    ModelCapability,
    ModelFormat,
    ModelInfo,
    ModelRegisterRequest,
    ModelStatus,
)


# ── Default model catalog ───────────────────────────────────────────

_DEFAULT_MODELS: List[Dict[str, Any]] = [
    {
        "model_id": "llama-3.1-8b-instruct",
        "source": "meta-llama/Llama-3.1-8B-Instruct",
        "format": ModelFormat.SAFETENSORS,
        "capabilities": [ModelCapability.CHAT, ModelCapability.COMPLETION, ModelCapability.CODE_GENERATION],
        "compatible_engines": ["vllm", "sglang", "tgi", "ollama"],
        "context_length": 131072,
        "parameters_billion": 8.0,
    },
    {
        "model_id": "llama-3.1-70b-instruct",
        "source": "meta-llama/Llama-3.1-70B-Instruct",
        "format": ModelFormat.SAFETENSORS,
        "capabilities": [ModelCapability.CHAT, ModelCapability.COMPLETION, ModelCapability.CODE_GENERATION, ModelCapability.REASONING],
        "compatible_engines": ["vllm", "sglang", "tgi"],
        "context_length": 131072,
        "parameters_billion": 70.0,
    },
    {
        "model_id": "qwen2.5-72b-instruct",
        "source": "Qwen/Qwen2.5-72B-Instruct",
        "format": ModelFormat.SAFETENSORS,
        "capabilities": [ModelCapability.CHAT, ModelCapability.COMPLETION, ModelCapability.CODE_GENERATION, ModelCapability.FUNCTION_CALLING],
        "compatible_engines": ["vllm", "sglang", "tgi"],
        "context_length": 131072,
        "parameters_billion": 72.0,
    },
    {
        "model_id": "qwen2.5-coder-32b-instruct",
        "source": "Qwen/Qwen2.5-Coder-32B-Instruct",
        "format": ModelFormat.SAFETENSORS,
        "capabilities": [ModelCapability.CHAT, ModelCapability.CODE_GENERATION],
        "compatible_engines": ["vllm", "sglang"],
        "context_length": 131072,
        "parameters_billion": 32.0,
    },
    {
        "model_id": "deepseek-r1-distill-qwen-32b",
        "source": "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
        "format": ModelFormat.SAFETENSORS,
        "capabilities": [ModelCapability.CHAT, ModelCapability.REASONING, ModelCapability.CODE_GENERATION],
        "compatible_engines": ["vllm", "sglang"],
        "context_length": 131072,
        "parameters_billion": 32.0,
    },
    {
        "model_id": "mistral-7b-instruct-v0.3",
        "source": "mistralai/Mistral-7B-Instruct-v0.3",
        "format": ModelFormat.SAFETENSORS,
        "capabilities": [ModelCapability.CHAT, ModelCapability.COMPLETION],
        "compatible_engines": ["vllm", "sglang", "tgi", "ollama"],
        "context_length": 32768,
        "parameters_billion": 7.0,
    },
]


class ModelRegistry:
    """Thread-safe model registry with default model catalog.

    Responsibilities:
    - Register/deregister model-to-engine mappings
    - Resolve model IDs (exact, source, partial match)
    - Filter by capability and engine
    - Track model status and loaded engines
    """

    def __init__(self) -> None:
        self._models: Dict[str, ModelInfo] = {}
        self._load_defaults()

    @property
    def count(self) -> int:
        return len(self._models)

    # ── Registration ────────────────────────────────────────────────

    async def register(self, req: ModelRegisterRequest) -> ModelInfo:
        if req.model_id in self._models:
            raise ValueError(f"Model '{req.model_id}' already registered")

        info = ModelInfo(
            model_id=req.model_id,
            source=req.source,
            format=req.format,
            capabilities=req.capabilities,
            compatible_engines=req.compatible_engines,
            context_length=req.context_length,
            parameters_billion=req.parameters_billion,
            quantization=req.quantization,
            hardware=req.hardware,
            status=ModelStatus.REGISTERED,
            loaded_on_engines=[],
            registered_at=datetime.now(timezone.utc).isoformat(),
            metadata=req.metadata,
        )
        self._models[req.model_id] = info
        return info

    # ── Queries ─────────────────────────────────────────────────────

    async def get(self, model_id: str) -> Optional[ModelInfo]:
        return self._models.get(model_id)

    async def list_models(
        self,
        capability: Optional[ModelCapability] = None,
        engine: Optional[str] = None,
    ) -> List[ModelInfo]:
        result = list(self._models.values())
        if capability is not None:
            result = [m for m in result if capability in m.capabilities]
        if engine is not None:
            result = [m for m in result if engine in m.compatible_engines]
        return result

    async def resolve_model(self, query: str) -> Optional[ModelInfo]:
        """Resolve a model by exact ID, source path, or partial match."""
        if query == "default":
            models = list(self._models.values())
            return models[0] if models else None

        # Exact match
        if query in self._models:
            return self._models[query]

        # Source match
        for m in self._models.values():
            if m.source == query:
                return m

        # Partial match (prefix)
        for mid, m in self._models.items():
            if mid.startswith(query):
                return m

        return None

    # ── Lifecycle ───────────────────────────────────────────────────

    async def update_status(
        self,
        model_id: str,
        status: ModelStatus,
        engine: Optional[str] = None,
    ) -> None:
        model = self._models.get(model_id)
        if model is None:
            raise KeyError(f"Model '{model_id}' not found")

        model.status = status

        if engine is not None and status == ModelStatus.READY:
            if engine not in model.loaded_on_engines:
                model.loaded_on_engines.append(engine)
        elif status in (ModelStatus.UNLOADING, ModelStatus.ERROR, ModelStatus.RETIRED):
            if engine and engine in model.loaded_on_engines:
                model.loaded_on_engines.remove(engine)

    async def delete(self, model_id: str) -> bool:
        model = self._models.get(model_id)
        if model is None:
            return False

        if model.loaded_on_engines:
            raise ValueError(
                f"Model '{model_id}' still loaded on engines: "
                f"{model.loaded_on_engines}. Unload first."
            )

        del self._models[model_id]
        return True

    # ── Internal ────────────────────────────────────────────────────

    def _load_defaults(self) -> None:
        for spec in _DEFAULT_MODELS:
            info = ModelInfo(
                model_id=spec["model_id"],
                source=spec["source"],
                format=spec["format"],
                capabilities=spec["capabilities"],
                compatible_engines=spec["compatible_engines"],
                context_length=spec["context_length"],
                parameters_billion=spec.get("parameters_billion"),
                status=ModelStatus.REGISTERED,
                loaded_on_engines=[],
                registered_at=datetime.now(timezone.utc).isoformat(),
            )
            self._models[spec["model_id"]] = info