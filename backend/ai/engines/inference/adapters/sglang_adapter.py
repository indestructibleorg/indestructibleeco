"""SGLang Inference Adapter.

RadixAttention, structured generation, 6.4x throughput boost.
Connects to SGLang's OpenAI-compatible API server.
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


class SGLangAdapter(BaseInferenceAdapter):
    """Adapter for SGLang inference engine.

    SGLang features: RadixAttention for automatic KV-cache reuse,
    structured generation with regex/JSON schema constraints,
    continuous batching, FlashInfer kernels, multi-modal support.
    """

    def __init__(self, endpoint: str = "http://localhost:8003", **kwargs: Any) -> None:
        super().__init__(EngineType.SGLANG, endpoint, **kwargs)
        self._timeout = kwargs.get("timeout", 120.0)

    async def generate(self, request: InferenceRequest) -> InferenceResponse:
        start = time.perf_counter()
        request_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        payload = self._build_payload(request)

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(f"{self.endpoint}/v1/chat/completions", json=payload)
            resp.raise_for_status()
            data = resp.json()

        latency = (time.perf_counter() - start) * 1000
        usage = data.get("usage", {})

        return InferenceResponse(
            id=data.get("id", request_id), model=data.get("model", request.model),
            choices=data.get("choices", []),
            usage={"prompt_tokens": usage.get("prompt_tokens", 0),
                   "completion_tokens": usage.get("completion_tokens", 0),
                   "total_tokens": usage.get("total_tokens", 0)},
            engine=self.engine_type.value, latency_ms=round(latency, 2),
        )

    async def stream(self, request: InferenceRequest) -> AsyncIterator[StreamChunk]:
        request_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        payload = self._build_payload(request)
        payload["stream"] = True

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            async with client.stream("POST", f"{self.endpoint}/v1/chat/completions", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        choices = data.get("choices", [])
                        if choices:
                            yield StreamChunk(
                                id=data.get("id", request_id), model=data.get("model", request.model),
                                delta=choices[0].get("delta", {}),
                                finish_reason=choices[0].get("finish_reason"),
                            )
                    except json.JSONDecodeError:
                        continue

    async def health_check(self) -> EngineHealth:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.endpoint}/health")
                models_resp = await client.get(f"{self.endpoint}/v1/models")
                models = [m["id"] for m in models_resp.json().get("data", [])] if models_resp.status_code == 200 else []
            return EngineHealth(
                engine_type=self.engine_type,
                status=EngineStatus.HEALTHY if resp.status_code == 200 else EngineStatus.DEGRADED,
                endpoint=self.endpoint, models_loaded=models, uptime_seconds=self._uptime(),
            )
        except Exception as e:
            return EngineHealth(
                engine_type=self.engine_type, status=EngineStatus.UNHEALTHY,
                endpoint=self.endpoint, error=str(e), uptime_seconds=self._uptime(),
            )

    async def list_models(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{self.endpoint}/v1/models")
            resp.raise_for_status()
            return resp.json().get("data", [])

    @staticmethod
    def _build_payload(request: InferenceRequest) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": request.model, "temperature": request.temperature,
            "max_tokens": request.max_tokens, "top_p": request.top_p,
            "frequency_penalty": request.frequency_penalty,
            "presence_penalty": request.presence_penalty, "stream": False,
        }
        if request.messages:
            payload["messages"] = request.messages
        elif request.prompt:
            payload["messages"] = [{"role": "user", "content": request.prompt}]
        if request.stop:
            payload["stop"] = request.stop
        payload.update(request.extra)
        return payload