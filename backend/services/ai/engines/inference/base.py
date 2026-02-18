"""Base adapter interface for all inference engines.

Every engine adapter must implement this contract to participate
in the multi-engine routing system. The router dispatches requests
to adapters based on model registry mappings and health status.
"""
from __future__ import annotations

import abc
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator


class EngineType(str, Enum):
    VLLM = "vllm"
    TGI = "tgi"
    SGLANG = "sglang"
    OLLAMA = "ollama"
    TENSORRT_LLM = "tensorrt-llm"
    LMDEPLOY = "lmdeploy"
    DEEPSPEED = "deepspeed"


class EngineStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    STARTING = "starting"
    UNKNOWN = "unknown"


@dataclass
class InferenceRequest:
    model: str
    messages: list[dict[str, Any]] | None = None
    prompt: str | None = None
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 1.0
    top_k: int = -1
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: list[str] | None = None
    stream: bool = False
    n: int = 1
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class InferenceResponse:
    id: str
    model: str
    choices: list[dict[str, Any]]
    usage: dict[str, int]
    created: int = field(default_factory=lambda: int(time.time()))
    engine: str = ""
    latency_ms: float = 0.0


@dataclass
class StreamChunk:
    id: str
    model: str
    delta: dict[str, Any]
    finish_reason: str | None = None
    created: int = field(default_factory=lambda: int(time.time()))


@dataclass
class EngineHealth:
    engine_type: EngineType
    status: EngineStatus
    endpoint: str
    models_loaded: list[str] = field(default_factory=list)
    gpu_utilization: float | None = None
    memory_used_mb: float | None = None
    memory_total_mb: float | None = None
    requests_pending: int = 0
    uptime_seconds: float = 0.0
    error: str | None = None


class BaseInferenceAdapter(abc.ABC):
    """Abstract base class for inference engine adapters.

    Each adapter wraps a specific inference backend (vLLM, TGI, etc.)
    and translates between the unified request/response format and
    the engine's native API.
    """

    def __init__(self, engine_type: EngineType, endpoint: str, **kwargs: Any) -> None:
        self.engine_type = engine_type
        self.endpoint = endpoint.rstrip("/")
        self._config = kwargs
        self._start_time = time.time()

    @abc.abstractmethod
    async def generate(self, request: InferenceRequest) -> InferenceResponse:
        """Execute a non-streaming inference request.

        Args:
            request: Unified inference request.

        Returns:
            Complete inference response with all choices.
        """

    @abc.abstractmethod
    async def stream(self, request: InferenceRequest) -> AsyncIterator[StreamChunk]:
        """Execute a streaming inference request.

        Args:
            request: Unified inference request with stream=True.

        Yields:
            StreamChunk objects as tokens are generated.
        """

    @abc.abstractmethod
    async def health_check(self) -> EngineHealth:
        """Check engine health and resource utilization.

        Returns:
            EngineHealth with current status and metrics.
        """

    @abc.abstractmethod
    async def list_models(self) -> list[dict[str, Any]]:
        """List all models currently loaded in the engine.

        Returns:
            List of model info dicts with id, object, created, owned_by.
        """

    async def embeddings(self, texts: list[str], model: str) -> dict[str, Any]:
        """Generate embeddings (optional, not all engines support this).

        Args:
            texts: List of texts to embed.
            model: Embedding model identifier.

        Returns:
            Dict with embeddings list and usage info.

        Raises:
            NotImplementedError: If engine does not support embeddings.
        """
        raise NotImplementedError(f"{self.engine_type.value} does not support embeddings")

    def _build_openai_response(
        self,
        request_id: str,
        model: str,
        content: str,
        prompt_tokens: int,
        completion_tokens: int,
        finish_reason: str = "stop",
        latency_ms: float = 0.0,
    ) -> InferenceResponse:
        """Helper to construct a standardized OpenAI-format response."""
        return InferenceResponse(
            id=request_id,
            model=model,
            choices=[{
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": finish_reason,
            }],
            usage={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
            engine=self.engine_type.value,
            latency_ms=latency_ms,
        )

    def _uptime(self) -> float:
        return time.time() - self._start_time