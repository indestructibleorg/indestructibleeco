"""Ollama Inference Adapter.

One-command local deployment, GGUF quantization support.
Connects to Ollama's REST API with OpenAI-compatible translation.
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


class OllamaAdapter(BaseInferenceAdapter):
    """Adapter for Ollama inference engine.

    Ollama features: one-command model pull and serve, GGUF/GGML
    quantization, CPU and GPU inference, Modelfile customization,
    concurrent model loading, OpenAI-compatible API.
    """

    def __init__(self, endpoint: str = "http://localhost:11434", **kwargs: Any) -> None:
        super().__init__(EngineType.OLLAMA, endpoint, **kwargs)
        self._timeout = kwargs.get("timeout", 300.0)

    async def generate(self, request: InferenceRequest) -> InferenceResponse:
        start = time.perf_counter()
        request_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"

        payload: dict[str, Any] = {
            "model": request.model,
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "top_p": request.top_p,
                "num_predict": request.max_tokens,
                "repeat_penalty": 1.0 + request.frequency_penalty,
            },
        }
        if request.top_k > 0:
            payload["options"]["top_k"] = request.top_k
        if request.stop:
            payload["options"]["stop"] = request.stop

        if request.messages:
            payload["messages"] = request.messages
            api_path = "/api/chat"
        else:
            payload["prompt"] = request.prompt or ""
            api_path = "/api/generate"

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(f"{self.endpoint}{api_path}", json=payload)
            resp.raise_for_status()
            data = resp.json()

        content = data.get("message", {}).get("content", "") if "message" in data else data.get("response", "")
        latency = (time.perf_counter() - start) * 1000
        prompt_tokens = data.get("prompt_eval_count", 0)
        completion_tokens = data.get("eval_count", 0)

        return self._build_openai_response(
            request_id, request.model, content, prompt_tokens, completion_tokens, latency_ms=round(latency, 2),
        )

    async def stream(self, request: InferenceRequest) -> AsyncIterator[StreamChunk]:
        request_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        payload: dict[str, Any] = {
            "model": request.model, "stream": True,
            "options": {"temperature": request.temperature, "top_p": request.top_p, "num_predict": request.max_tokens},
        }
        if request.messages:
            payload["messages"] = request.messages
            api_path = "/api/chat"
        else:
            payload["prompt"] = request.prompt or ""
            api_path = "/api/generate"

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            async with client.stream("POST", f"{self.endpoint}{api_path}", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        done = data.get("done", False)
                        if "message" in data:
                            text = data["message"].get("content", "")
                        else:
                            text = data.get("response", "")
                        if text:
                            yield StreamChunk(
                                id=request_id, model=request.model,
                                delta={"content": text},
                                finish_reason="stop" if done else None,
                            )
                        if done:
                            break
                    except json.JSONDecodeError:
                        continue

    async def health_check(self) -> EngineHealth:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.endpoint}/api/tags")
                data = resp.json() if resp.status_code == 200 else {}
                models = [m["name"] for m in data.get("models", [])]
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
            resp = await client.get(f"{self.endpoint}/api/tags")
            resp.raise_for_status()
            data = resp.json()
        return [
            {"id": m["name"], "object": "model", "owned_by": "ollama",
             "size": m.get("size", 0), "quantization": m.get("details", {}).get("quantization_level", "")}
            for m in data.get("models", [])
        ]

    async def embeddings(self, texts: list[str], model: str) -> dict[str, Any]:
        results = []
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            for i, text in enumerate(texts):
                resp = await client.post(f"{self.endpoint}/api/embeddings", json={"model": model, "prompt": text})
                resp.raise_for_status()
                data = resp.json()
                results.append({"object": "embedding", "index": i, "embedding": data.get("embedding", [])})
        return {"object": "list", "data": results, "model": model,
                "usage": {"prompt_tokens": sum(len(t.split()) for t in texts), "total_tokens": 0}}