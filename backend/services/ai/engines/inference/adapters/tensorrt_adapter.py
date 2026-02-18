"""TensorRT-LLM Inference Adapter.

NVIDIA deep optimization, FP8/FP4 quantization, kernel fusion.
Connects to Triton Inference Server with TensorRT-LLM backend.
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


class TensorRTLLMAdapter(BaseInferenceAdapter):
    """Adapter for TensorRT-LLM via Triton Inference Server.

    Features: FP8/FP4/INT4 quantization, in-flight batching,
    KV-cache paging, kernel auto-tuning, multi-GPU tensor parallelism,
    speculative decoding, CUDA graph optimization.
    """

    def __init__(self, endpoint: str = "http://localhost:8004", **kwargs: Any) -> None:
        super().__init__(EngineType.TENSORRT_LLM, endpoint, **kwargs)
        self._timeout = kwargs.get("timeout", 120.0)
        self._model_name = kwargs.get("model_name", "ensemble")

    async def generate(self, request: InferenceRequest) -> InferenceResponse:
        start = time.perf_counter()
        request_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        prompt = self._format_prompt(request)

        payload = {
            "text_input": prompt,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "stream": False,
            "bad_words": "",
            "stop_words": "|".join(request.stop) if request.stop else "",
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(
                f"{self.endpoint}/v2/models/{self._model_name}/generate", json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        generated = data.get("text_output", "")
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
            "text_input": prompt,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            async with client.stream(
                "POST", f"{self.endpoint}/v2/models/{self._model_name}/generate_stream", json=payload,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data_str = line[5:].strip()
                    if not data_str or data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        text = data.get("text_output", "")
                        if text:
                            yield StreamChunk(
                                id=request_id, model=request.model,
                                delta={"content": text},
                                finish_reason="stop" if data.get("is_final", False) else None,
                            )
                    except json.JSONDecodeError:
                        continue

    async def health_check(self) -> EngineHealth:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.endpoint}/v2/health/ready")
                models_resp = await client.get(f"{self.endpoint}/v2/models")
                models = []
                if models_resp.status_code == 200:
                    for m in models_resp.json().get("models", []):
                        models.append(m.get("name", "unknown"))
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
            resp = await client.get(f"{self.endpoint}/v2/models")
            resp.raise_for_status()
        return [
            {"id": m.get("name", ""), "object": "model", "owned_by": "nvidia-tensorrt"}
            for m in resp.json().get("models", [])
        ]

    @staticmethod
    def _format_prompt(request: InferenceRequest) -> str:
        if request.prompt:
            return request.prompt
        if not request.messages:
            return ""
        parts = []
        for msg in request.messages:
            role, content = msg.get("role", "user"), msg.get("content", "")
            if role == "system":
                parts.append(f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n{content}<|eot_id|>")
            elif role == "user":
                parts.append(f"<|start_header_id|>user<|end_header_id|>\n{content}<|eot_id|>")
            elif role == "assistant":
                parts.append(f"<|start_header_id|>assistant<|end_header_id|>\n{content}<|eot_id|>")
        parts.append("<|start_header_id|>assistant<|end_header_id|>\n")
        return "".join(parts)