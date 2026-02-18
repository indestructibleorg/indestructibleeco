"""vLLM Inference Adapter.

PagedAttention, continuous batching, prefix caching.
Connects to vLLM's OpenAI-compatible API server.
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any, AsyncIterator

import httpx

from ..base import (
    BaseInferenceAdapter, EngineHealth, EngineStatus, EngineType,
    InferenceRequest, InferenceResponse, StreamChunk,
)

logger = logging.getLogger(__name__)


class VLLMAdapter(BaseInferenceAdapter):
    """Adapter for vLLM inference engine.

    vLLM features: PagedAttention for efficient KV-cache management,
    continuous batching for high throughput, prefix caching for
    repeated prompt prefixes, tensor parallelism for multi-GPU.
    """

    def __init__(self, endpoint: str = "http://localhost:8001", **kwargs: Any) -> None:
        super().__init__(EngineType.VLLM, endpoint, **kwargs)
        self._timeout = kwargs.get("timeout", 120.0)

    async def generate(self, request: InferenceRequest) -> InferenceResponse:
        start = time.perf_counter()
        request_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"

        payload = self._build_payload(request)

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(f"{self.endpoint}/v1/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()

        latency = (time.perf_counter() - start) * 1000
        usage = data.get("usage", {})

        return InferenceResponse(
            id=data.get("id", request_id),
            model=data.get("model", request.model),
            choices=data.get("choices", []),
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
            engine=self.engine_type.value,
            latency_ms=round(latency, 2),
        )

    async def stream(self, request: InferenceRequest) -> AsyncIterator[StreamChunk]:
        request_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        payload = self._build_payload(request)
        payload["stream"] = True

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            async with client.stream("POST", f"{self.endpoint}/v1/chat/completions", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        choices = data.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            yield StreamChunk(
                                id=data.get("id", request_id),
                                model=data.get("model", request.model),
                                delta=delta,
                                finish_reason=choices[0].get("finish_reason"),
                            )
                    except json.JSONDecodeError:
                        continue

    async def health_check(self) -> EngineHealth:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.endpoint}/health")
                models_resp = await client.get(f"{self.endpoint}/v1/models")
                models_data = models_resp.json() if models_resp.status_code == 200 else {}
                model_ids = [m["id"] for m in models_data.get("data", [])]

            return EngineHealth(
                engine_type=self.engine_type,
                status=EngineStatus.HEALTHY if resp.status_code == 200 else EngineStatus.DEGRADED,
                endpoint=self.endpoint,
                models_loaded=model_ids,
                uptime_seconds=self._uptime(),
            )
        except Exception as e:
            return EngineHealth(
                engine_type=self.engine_type,
                status=EngineStatus.UNHEALTHY,
                endpoint=self.endpoint,
                error=str(e),
                uptime_seconds=self._uptime(),
            )

    async def list_models(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{self.endpoint}/v1/models")
            resp.raise_for_status()
            return resp.json().get("data", [])

    async def embeddings(self, texts: list[str], model: str) -> dict[str, Any]:
        payload = {"input": texts, "model": model}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(f"{self.endpoint}/v1/embeddings", json=payload)
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    def _build_payload(request: InferenceRequest) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": request.model,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p,
            "frequency_penalty": request.frequency_penalty,
            "presence_penalty": request.presence_penalty,
            "n": request.n,
            "stream": False,
        }
        if request.messages:
            payload["messages"] = request.messages
        elif request.prompt:
            payload["messages"] = [{"role": "user", "content": request.prompt}]
        if request.stop:
            payload["stop"] = request.stop
        if request.top_k > 0:
            payload["top_k"] = request.top_k
        payload.update(request.extra)
        return payload