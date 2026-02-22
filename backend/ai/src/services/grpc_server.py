"""gRPC Inference Server — Internal high-performance inference endpoint.

Exposes GenerateCompletion, GenerateEmbedding, StreamCompletion, and
HealthCheck RPCs on ECO_AI_GRPC_PORT (default 8000).

Uses asyncio-based gRPC with EngineManager for dispatch.

URI: indestructibleeco://backend/ai/services/grpc_server
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict, List, Optional

logger = logging.getLogger(__name__)


class GrpcServiceConfig:
    """gRPC server configuration."""

    def __init__(
        self,
        port: int = 8000,
        max_workers: int = 10,
        max_message_size: int = 64 * 1024 * 1024,
        keepalive_time_ms: int = 30000,
        keepalive_timeout_ms: int = 10000,
        max_concurrent_rpcs: int = 100,
        reflection_enabled: bool = True,
    ) -> None:
        self.port = port
        self.max_workers = max_workers
        self.max_message_size = max_message_size
        self.keepalive_time_ms = keepalive_time_ms
        self.keepalive_timeout_ms = keepalive_timeout_ms
        self.max_concurrent_rpcs = max_concurrent_rpcs
        self.reflection_enabled = reflection_enabled


class GenerateRequest:
    """Mirrors the protobuf GenerateRequest message."""

    __slots__ = ("request_id", "model_id", "prompt", "max_tokens", "temperature", "top_p", "stream", "metadata")

    def __init__(
        self,
        model_id: str = "default",
        prompt: str = "",
        max_tokens: int = 2048,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stream: bool = False,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        self.request_id = str(uuid.uuid1())
        self.model_id = model_id
        self.prompt = prompt
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.stream = stream
        self.metadata = metadata or {}


class GenerateResponse:
    """Mirrors the protobuf GenerateResponse message."""

    __slots__ = (
        "request_id", "content", "model_id", "engine", "finish_reason",
        "prompt_tokens", "completion_tokens", "total_tokens", "latency_ms",
        "created_at",
    )

    def __init__(
        self,
        request_id: str = "",
        content: str = "",
        model_id: str = "",
        engine: str = "",
        finish_reason: str = "stop",
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        latency_ms: float = 0.0,
    ) -> None:
        self.request_id = request_id
        self.content = content
        self.model_id = model_id
        self.engine = engine
        self.finish_reason = finish_reason
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens
        self.latency_ms = latency_ms
        self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "content": self.content,
            "model_id": self.model_id,
            "engine": self.engine,
            "finish_reason": self.finish_reason,
            "usage": {
                "prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens,
                "total_tokens": self.total_tokens,
            },
            "latency_ms": self.latency_ms,
            "created_at": self.created_at,
        }


class EmbeddingRequest:
    """Mirrors the protobuf EmbeddingRequest message."""

    __slots__ = ("request_id", "texts", "model_id", "dimensions")

    def __init__(
        self,
        texts: Optional[List[str]] = None,
        model_id: str = "default",
        dimensions: int = 1024,
    ) -> None:
        self.request_id = str(uuid.uuid1())
        self.texts = texts or []
        self.model_id = model_id
        self.dimensions = dimensions


class EmbeddingResponse:
    """Mirrors the protobuf EmbeddingResponse message."""

    __slots__ = ("request_id", "embeddings", "model_id", "dimensions", "total_tokens", "latency_ms")

    def __init__(
        self,
        request_id: str = "",
        embeddings: Optional[List[List[float]]] = None,
        model_id: str = "",
        dimensions: int = 1024,
        total_tokens: int = 0,
        latency_ms: float = 0.0,
    ) -> None:
        self.request_id = request_id
        self.embeddings = embeddings or []
        self.model_id = model_id
        self.dimensions = dimensions
        self.total_tokens = total_tokens
        self.latency_ms = latency_ms

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "embeddings": self.embeddings,
            "model_id": self.model_id,
            "dimensions": self.dimensions,
            "total_tokens": self.total_tokens,
            "latency_ms": self.latency_ms,
        }


class HealthResponse:
    """gRPC health check response."""

    __slots__ = ("status", "engines_available", "uptime_seconds")

    def __init__(self, status: str = "SERVING", engines_available: int = 0, uptime_seconds: float = 0.0) -> None:
        self.status = status
        self.engines_available = engines_available
        self.uptime_seconds = uptime_seconds


class InferenceServicer:
    """gRPC service implementation for inference RPCs.

    Methods:
        GenerateCompletion — unary completion
        StreamCompletion — server-streaming completion
        GenerateEmbedding — batch embedding
        HealthCheck — liveness/readiness
    """

    def __init__(self, engine_manager: Any = None, embedding_service: Any = None) -> None:
        self._engine_manager = engine_manager
        self._embedding_service = embedding_service
        self._start_time = time.time()

        # Metrics
        self.total_requests: int = 0
        self.total_errors: int = 0
        self.total_stream_requests: int = 0
        self.total_embedding_requests: int = 0

    async def GenerateCompletion(self, request: GenerateRequest) -> GenerateResponse:
        """Unary RPC: generate a single completion."""
        self.total_requests += 1
        start = time.monotonic()

        try:
            if self._engine_manager is not None:
                result = await self._engine_manager.generate(
                    model_id=request.model_id,
                    prompt=request.prompt,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    top_p=request.top_p,
                )
                elapsed = (time.monotonic() - start) * 1000
                usage = result.get("usage", {})
                return GenerateResponse(
                    request_id=request.request_id,
                    content=result.get("content", ""),
                    model_id=result.get("model_id", request.model_id),
                    engine=result.get("engine", "unknown"),
                    finish_reason=result.get("finish_reason", "stop"),
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0),
                    total_tokens=usage.get("total_tokens", 0),
                    latency_ms=elapsed,
                )

            elapsed = (time.monotonic() - start) * 1000
            prompt_tokens = len(request.prompt.split())
            completion_tokens = min(request.max_tokens, prompt_tokens * 2)
            return GenerateResponse(
                request_id=request.request_id,
                content=f"[grpc-fallback] Response for: {request.prompt[:100]}...",
                model_id=request.model_id,
                engine="grpc-fallback",
                finish_reason="stop",
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                latency_ms=elapsed,
            )

        except Exception as exc:
            self.total_errors += 1
            logger.error("gRPC GenerateCompletion error: %s", exc)
            return GenerateResponse(
                request_id=request.request_id,
                content=f"[error] {exc}",
                model_id=request.model_id,
                engine="error",
                finish_reason="error",
                latency_ms=(time.monotonic() - start) * 1000,
            )

    async def StreamCompletion(self, request: GenerateRequest) -> AsyncIterator[GenerateResponse]:
        """Server-streaming RPC: stream completion tokens."""
        self.total_stream_requests += 1
        start = time.monotonic()

        try:
            if self._engine_manager is not None:
                result = await self._engine_manager.generate(
                    model_id=request.model_id,
                    prompt=request.prompt,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    top_p=request.top_p,
                )
                content = result.get("content", "")
            else:
                content = f"[grpc-stream-fallback] Response for: {request.prompt[:100]}..."

            words = content.split()
            chunk_size = max(1, len(words) // 5) if words else 1
            chunks = [
                " ".join(words[i : i + chunk_size])
                for i in range(0, len(words), chunk_size)
            ]

            for idx, chunk in enumerate(chunks):
                is_last = idx == len(chunks) - 1
                elapsed = (time.monotonic() - start) * 1000
                yield GenerateResponse(
                    request_id=request.request_id,
                    content=chunk,
                    model_id=request.model_id,
                    engine=result.get("engine", "grpc-stream") if self._engine_manager else "grpc-stream-fallback",
                    finish_reason="stop" if is_last else "length",
                    prompt_tokens=len(request.prompt.split()) if is_last else 0,
                    completion_tokens=len(chunk.split()),
                    total_tokens=len(request.prompt.split()) + len(chunk.split()) if is_last else len(chunk.split()),
                    latency_ms=elapsed,
                )
                await asyncio.sleep(0.01)

        except Exception as exc:
            self.total_errors += 1
            logger.error("gRPC StreamCompletion error: %s", exc)
            yield GenerateResponse(
                request_id=request.request_id,
                content=f"[error] {exc}",
                model_id=request.model_id,
                engine="error",
                finish_reason="error",
                latency_ms=(time.monotonic() - start) * 1000,
            )

    async def GenerateEmbedding(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Unary RPC: generate embeddings for a batch of texts."""
        self.total_embedding_requests += 1
        start = time.monotonic()

        try:
            if self._embedding_service is not None:
                result = await self._embedding_service.embed_batch(
                    texts=request.texts,
                    model_id=request.model_id,
                    dimensions=request.dimensions,
                )
                elapsed = (time.monotonic() - start) * 1000
                return EmbeddingResponse(
                    request_id=request.request_id,
                    embeddings=result.get("embeddings", []),
                    model_id=result.get("model_id", request.model_id),
                    dimensions=result.get("dimensions", request.dimensions),
                    total_tokens=result.get("total_tokens", 0),
                    latency_ms=elapsed,
                )

            import math
            import hashlib

            embeddings: List[List[float]] = []
            total_tokens = 0
            for text in request.texts:
                total_tokens += len(text.split())
                seed = int(hashlib.sha256(text.encode()).hexdigest()[:8], 16)
                import random
                rng = random.Random(seed)
                vec = [rng.gauss(0, 1) / math.sqrt(request.dimensions) for _ in range(request.dimensions)]
                norm = math.sqrt(sum(v * v for v in vec))
                if norm > 0:
                    vec = [v / norm for v in vec]
                embeddings.append([round(v, 6) for v in vec])

            elapsed = (time.monotonic() - start) * 1000
            return EmbeddingResponse(
                request_id=request.request_id,
                embeddings=embeddings,
                model_id=request.model_id,
                dimensions=request.dimensions,
                total_tokens=total_tokens,
                latency_ms=elapsed,
            )

        except Exception as exc:
            self.total_errors += 1
            logger.error("gRPC GenerateEmbedding error: %s", exc)
            return EmbeddingResponse(
                request_id=request.request_id,
                model_id=request.model_id,
                dimensions=request.dimensions,
                latency_ms=(time.monotonic() - start) * 1000,
            )

    async def HealthCheck(self) -> HealthResponse:
        """Health check RPC."""
        uptime = time.time() - self._start_time
        engines_available = 0
        if self._engine_manager is not None:
            engines_available = len(self._engine_manager.list_available_engines())

        status = "SERVING" if engines_available > 0 or self._engine_manager is None else "NOT_SERVING"
        return HealthResponse(
            status=status,
            engines_available=engines_available,
            uptime_seconds=round(uptime, 2),
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Return servicer metrics."""
        return {
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
            "total_stream_requests": self.total_stream_requests,
            "total_embedding_requests": self.total_embedding_requests,
            "uptime_seconds": round(time.time() - self._start_time, 2),
        }


class GrpcServer:
    """Manages the gRPC server lifecycle.

    Wraps InferenceServicer with server start/stop, port binding,
    and optional TLS configuration.

    Usage:
        server = GrpcServer(config, engine_manager, embedding_service)
        await server.start()
        ...
        await server.stop()
    """

    def __init__(
        self,
        config: Optional[GrpcServiceConfig] = None,
        engine_manager: Any = None,
        embedding_service: Any = None,
    ) -> None:
        self._config = config or GrpcServiceConfig()
        self._servicer = InferenceServicer(
            engine_manager=engine_manager,
            embedding_service=embedding_service,
        )
        self._server: Any = None
        self._running = False

    @property
    def servicer(self) -> InferenceServicer:
        return self._servicer

    @property
    def is_running(self) -> bool:
        return self._running

    async def start(self) -> None:
        """Start the gRPC server.

        Requires grpcio to be installed. If grpcio is unavailable or startup
        fails, the server remains inactive (``is_running`` returns ``False``).
        Callers should check ``is_running`` after ``start()`` to determine
        whether the gRPC server is accepting requests.
        """
        if self._running:
            return

        try:
            import grpc
            from grpc import aio as grpc_aio

            self._server = grpc_aio.server(
                options=[
                    ("grpc.max_send_message_length", self._config.max_message_size),
                    ("grpc.max_receive_message_length", self._config.max_message_size),
                    ("grpc.keepalive_time_ms", self._config.keepalive_time_ms),
                    ("grpc.keepalive_timeout_ms", self._config.keepalive_timeout_ms),
                    ("grpc.max_concurrent_streams", self._config.max_concurrent_rpcs),
                ],
            )
            self._server.add_insecure_port(f"[::]:{self._config.port}")
            await self._server.start()
            self._running = True
            logger.info(
                "gRPC server started on port %d (grpcio, max_workers=%d)",
                self._config.port,
                self._config.max_workers,
            )

        except ImportError:
            logger.warning(
                "grpcio not available — gRPC server NOT started on port %d; "
                "install grpcio to enable gRPC support",
                self._config.port,
            )

        except Exception as exc:
            logger.warning(
                "gRPC server failed to start on port %d: %s",
                self._config.port,
                exc,
            )

    async def stop(self, grace_period: float = 5.0) -> None:
        """Stop the gRPC server with graceful shutdown."""
        if not self._running:
            return

        if self._server is not None:
            try:
                await self._server.stop(grace_period)
            except Exception as exc:
                logger.warning("gRPC server stop error: %s", exc)

        self._running = False
        logger.info("gRPC server stopped")

    def get_metrics(self) -> Dict[str, Any]:
        """Return server + servicer metrics."""
        return {
            "server": {
                "running": self._running,
                "port": self._config.port,
                "max_concurrent_rpcs": self._config.max_concurrent_rpcs,
            },
            "servicer": self._servicer.get_metrics(),
        }