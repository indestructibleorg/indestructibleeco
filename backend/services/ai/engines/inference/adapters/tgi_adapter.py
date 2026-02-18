"""TGI (Text Generation Inference) Adapter.

HuggingFace ecosystem, Flash Attention 2, production-grade serving.
Connects to TGI's native API with OpenAI-compatible translation.
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


class TGIAdapter(BaseInferenceAdapter):
    """Adapter for HuggingFace Text Generation Inference.

    TGI features: Flash Attention 2, continuous batching, quantization
    (GPTQ, AWQ, EETQ, bitsandbytes), Paged Attention, token streaming,
    watermarking, grammar-constrained generation.
    """

    def __init__(self, endpoint: str = "http://localhost:8002", **kwargs: Any) -> None:
        super().__init__(EngineType.TGI, endpoint, **kwargs)
        self._timeout = kwargs.get("timeout", 120.0)

    async def generate(self, request: InferenceRequest) -> InferenceResponse:
        start = time.perf_counter()
        request_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"

        prompt = self._format_prompt(request)
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": request.max_tokens,
                "temperature": max(request.temperature, 0.01),
                "top_p": request.top_p,
                "top_k": request.top_k if request.top_k > 0 else None,
                "repetition_penalty": 1.0 + request.frequency_penalty,
                "do_sample": request.temperature > 0,
                "return_full_text": False,
            },
        }
        if request.stop:
            payload["parameters"]["stop_sequences"] = request.stop

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(f"{self.endpoint}/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()

        generated = data.get("generated_text", "") if isinstance(data, dict) else data[0].get("generated_text", "")
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
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": request.max_tokens,
                "temperature": max(request.temperature, 0.01),
                "top_p": request.top_p,
                "do_sample": request.temperature > 0,
            },
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            async with client.stream("POST", f"{self.endpoint}/generate_stream", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data_str = line[5:].strip()
                    if not data_str:
                        continue
                    try:
                        data = json.loads(data_str)
                        token = data.get("token", {})
                        text = token.get("text", "")
                        special = token.get("special", False)
                        if special:
                            continue
                        yield StreamChunk(
                            id=request_id,
                            model=request.model,
                            delta={"content": text},
                            finish_reason="stop" if data.get("generated_text") is not None else None,
                        )
                    except json.JSONDecodeError:
                        continue

    async def health_check(self) -> EngineHealth:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.endpoint}/health")
                info_resp = await client.get(f"{self.endpoint}/info")
                info = info_resp.json() if info_resp.status_code == 200 else {}

            return EngineHealth(
                engine_type=self.engine_type,
                status=EngineStatus.HEALTHY if resp.status_code == 200 else EngineStatus.DEGRADED,
                endpoint=self.endpoint,
                models_loaded=[info.get("model_id", "unknown")],
                uptime_seconds=self._uptime(),
            )
        except Exception as e:
            return EngineHealth(
                engine_type=self.engine_type, status=EngineStatus.UNHEALTHY,
                endpoint=self.endpoint, error=str(e), uptime_seconds=self._uptime(),
            )

    async def list_models(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{self.endpoint}/info")
            resp.raise_for_status()
            info = resp.json()
        return [{"id": info.get("model_id", "unknown"), "object": "model", "owned_by": "huggingface"}]

    @staticmethod
    def _format_prompt(request: InferenceRequest) -> str:
        if request.prompt:
            return request.prompt
        if not request.messages:
            return ""
        parts = []
        for msg in request.messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                parts.append(f"<|system|>\n{content}</s>")
            elif role == "user":
                parts.append(f"<|user|>\n{content}</s>")
            elif role == "assistant":
                parts.append(f"<|assistant|>\n{content}</s>")
        parts.append("<|assistant|>\n")
        return "\n".join(parts)