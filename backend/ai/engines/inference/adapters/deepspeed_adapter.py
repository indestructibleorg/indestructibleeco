"""DeepSpeed Inference Adapter.

ZeRO optimization, large-scale distributed inference,
DeepSpeed-MII for low-latency serving.
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


class DeepSpeedAdapter(BaseInferenceAdapter):
    """Adapter for DeepSpeed-MII inference engine.

    Features: ZeRO-Inference for memory-efficient large model serving,
    tensor parallelism, pipeline parallelism, dynamic SplitFuse,
    blocked KV-cache, continuous batching via DeepSpeed-FastGen.
    """

    def __init__(self, endpoint: str = "http://localhost:8006", **kwargs: Any) -> None:
        super().__init__(EngineType.DEEPSPEED, endpoint, **kwargs)
        self._timeout = kwargs.get("timeout", 180.0)

    async def generate(self, request: InferenceRequest) -> InferenceResponse:
        start = time.perf_counter()
        request_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        prompt = self._format_prompt(request)

        payload = {
            "prompts": [prompt],
            "max_new_tokens": request.max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "do_sample": request.temperature > 0,
        }
        if request.stop:
            payload["stop_words"] = request.stop

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(f"{self.endpoint}/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()

        responses = data.get("responses", data.get("text", [""]))
        generated = responses[0] if isinstance(responses, list) else str(responses)
        latency = (time.perf_counter() - start) * 1000
        prompt_tokens = len(prompt.split()) * 4 // 3
        completion_tokens = len(generated.split()) * 4 // 3

        return self._build_openai_response(
            request_id, request.model, generated, prompt_tokens, completion_tokens, latency_ms=round(latency, 2),
        )

    async def stream(self, request: InferenceRequest) -> AsyncIterator[StreamChunk]:
        request_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        prompt = self._format_prompt(request)

        payload = {
            "prompts": [prompt],
            "max_new_tokens": request.max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            async with client.stream("POST", f"{self.endpoint}/generate_stream", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    if line.startswith("data:"):
                        line = line[5:].strip()
                    if line == "[DONE]":
                        break
                    try:
                        data = json.loads(line)
                        text = data.get("text", data.get("token", {}).get("text", ""))
                        if text:
                            yield StreamChunk(
                                id=request_id, model=request.model,
                                delta={"content": text},
                                finish_reason="stop" if data.get("finished", False) else None,
                            )
                    except json.JSONDecodeError:
                        continue

    async def health_check(self) -> EngineHealth:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.endpoint}/health")
            return EngineHealth(
                engine_type=self.engine_type,
                status=EngineStatus.HEALTHY if resp.status_code == 200 else EngineStatus.DEGRADED,
                endpoint=self.endpoint, uptime_seconds=self._uptime(),
            )
        except Exception as e:
            return EngineHealth(
                engine_type=self.engine_type, status=EngineStatus.UNHEALTHY,
                endpoint=self.endpoint, error=str(e), uptime_seconds=self._uptime(),
            )

    async def list_models(self) -> list[dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.endpoint}/models")
                resp.raise_for_status()
                return resp.json().get("models", [])
        except Exception:
            return [{"id": "deepspeed-model", "object": "model", "owned_by": "microsoft-deepspeed"}]

    @staticmethod
    def _format_prompt(request: InferenceRequest) -> str:
        if request.prompt:
            return request.prompt
        if not request.messages:
            return ""
        parts = []
        for msg in request.messages:
            role, content = msg.get("role", "user"), msg.get("content", "")
            parts.append(f"<|{role}|>\n{content}")
        parts.append("<|assistant|>\n")
        return "\n".join(parts)