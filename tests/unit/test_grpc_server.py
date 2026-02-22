"""Unit tests for gRPC Inference Server."""
import importlib.util
import pytest
import asyncio

from backend.ai.src.services.grpc_server import (
    EmbeddingRequest,
    EmbeddingResponse,
    GenerateRequest,
    GenerateResponse,
    GrpcServer,
    GrpcServiceConfig,
    HealthResponse,
    InferenceServicer,
)

_grpcio_available = importlib.util.find_spec("grpc") is not None


@pytest.fixture
def servicer():
    return InferenceServicer(engine_manager=None, embedding_service=None)


@pytest.fixture
def config():
    return GrpcServiceConfig(port=50099, max_workers=2, max_concurrent_rpcs=10)


class TestGenerateRequest:
    def test_defaults(self):
        req = GenerateRequest()
        assert req.model_id == "default"
        assert req.max_tokens == 2048
        assert req.temperature == 0.7
        assert req.stream is False
        assert req.request_id is not None

    def test_custom(self):
        req = GenerateRequest(
            model_id="llama-3.1-8b",
            prompt="Hello",
            max_tokens=512,
            temperature=0.5,
            stream=True,
        )
        assert req.model_id == "llama-3.1-8b"
        assert req.prompt == "Hello"
        assert req.stream is True


class TestGenerateResponse:
    def test_to_dict(self):
        resp = GenerateResponse(
            request_id="req-1",
            content="Hello world",
            model_id="test",
            engine="vllm",
            prompt_tokens=5,
            completion_tokens=10,
            total_tokens=15,
            latency_ms=42.5,
        )
        d = resp.to_dict()
        assert d["request_id"] == "req-1"
        assert d["content"] == "Hello world"
        assert d["usage"]["total_tokens"] == 15
        assert d["latency_ms"] == 42.5
        assert "created_at" in d


class TestEmbeddingRequest:
    def test_defaults(self):
        req = EmbeddingRequest()
        assert req.texts == []
        assert req.model_id == "default"
        assert req.dimensions == 1024

    def test_custom(self):
        req = EmbeddingRequest(texts=["hello", "world"], dimensions=512)
        assert len(req.texts) == 2
        assert req.dimensions == 512


class TestInferenceServicer:
    @pytest.mark.asyncio
    async def test_generate_completion_fallback(self, servicer):
        req = GenerateRequest(model_id="test-model", prompt="Hello world")
        resp = await servicer.GenerateCompletion(req)
        assert isinstance(resp, GenerateResponse)
        assert resp.request_id == req.request_id
        assert resp.engine == "grpc-fallback"
        assert resp.finish_reason == "stop"
        assert resp.prompt_tokens > 0
        assert resp.latency_ms >= 0
        assert servicer.total_requests == 1

    @pytest.mark.asyncio
    async def test_stream_completion_fallback(self, servicer):
        req = GenerateRequest(model_id="test-model", prompt="Hello world test stream")
        chunks = []
        async for chunk in servicer.StreamCompletion(req):
            chunks.append(chunk)
        assert len(chunks) >= 1
        assert chunks[-1].finish_reason == "stop"
        assert servicer.total_stream_requests == 1

    @pytest.mark.asyncio
    async def test_generate_embedding_fallback(self, servicer):
        req = EmbeddingRequest(texts=["hello", "world"], dimensions=64)
        resp = await servicer.GenerateEmbedding(req)
        assert isinstance(resp, EmbeddingResponse)
        assert len(resp.embeddings) == 2
        assert len(resp.embeddings[0]) == 64
        assert resp.total_tokens > 0
        assert servicer.total_embedding_requests == 1

    @pytest.mark.asyncio
    async def test_health_check_no_engine(self, servicer):
        resp = await servicer.HealthCheck()
        assert isinstance(resp, HealthResponse)
        assert resp.status == "SERVING"
        assert resp.engines_available == 0
        assert resp.uptime_seconds >= 0

    @pytest.mark.asyncio
    async def test_metrics(self, servicer):
        await servicer.GenerateCompletion(GenerateRequest(prompt="test"))
        await servicer.GenerateCompletion(GenerateRequest(prompt="test2"))
        metrics = servicer.get_metrics()
        assert metrics["total_requests"] == 2
        assert metrics["total_errors"] == 0
        assert metrics["uptime_seconds"] >= 0


@pytest.mark.skipif(not _grpcio_available, reason="grpcio not installed")
class TestGrpcServer:
    @pytest.mark.asyncio
    async def test_server_lifecycle(self, config):
        server = GrpcServer(config=config)
        assert server.is_running is False

        await server.start()
        assert server.is_running is True

        await server.stop()
        assert server.is_running is False

    @pytest.mark.asyncio
    async def test_server_metrics(self, config):
        server = GrpcServer(config=config)
        await server.start()
        metrics = server.get_metrics()
        assert metrics["server"]["running"] is True
        assert metrics["server"]["port"] == 50099
        assert "servicer" in metrics
        await server.stop()

    @pytest.mark.asyncio
    async def test_server_double_start(self, config):
        server = GrpcServer(config=config)
        await server.start()
        await server.start()  # should be idempotent
        assert server.is_running is True
        await server.stop()

    @pytest.mark.asyncio
    async def test_server_double_stop(self, config):
        server = GrpcServer(config=config)
        await server.start()
        await server.stop()
        await server.stop()  # should be idempotent
        assert server.is_running is False

    def test_config_defaults(self):
        cfg = GrpcServiceConfig()
        assert cfg.port == 8000
        assert cfg.max_workers == 10
        assert cfg.max_message_size == 64 * 1024 * 1024
        assert cfg.max_concurrent_rpcs == 100
        assert cfg.reflection_enabled is True

    @pytest.mark.asyncio
    async def test_servicer_accessible(self, config):
        server = GrpcServer(config=config)
        assert server.servicer is not None
        assert isinstance(server.servicer, InferenceServicer)