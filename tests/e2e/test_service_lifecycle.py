"""End-to-end tests for eco-base service lifecycle.

Covers cross-service integration flows not tested in test_full_flow.py:
  - Connection pool lifecycle (init -> get_client -> close)
  - Circuit breaker state transitions under engine failure
  - Embedding service batch + similarity + dimension reduction
  - Worker job lifecycle (submit -> poll -> complete -> cancel)
  - Health monitor probe cycle
  - Governance engine audit trail integrity
  - Config validation
  - Model registry filter + resolve + lifecycle
  - gRPC servicer request/response contracts
  - Engine manager init + degraded generate
  - Request queue enqueue/dequeue with priority

URI: eco-base://tests/e2e/test_service_lifecycle
"""

import pytest
import asyncio
import os
import sys
import time
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


# --- Connection Pool Lifecycle ------------------------------------------------


class TestConnectionPoolLifecycle:
    """Verify connection pool init, get_client, close cycle."""

    def test_pool_creates_client_for_engine(self):
        from backend.ai.src.services.connection_pool import ConnectionPool

        pool = ConnectionPool()
        client = pool.get_client("vllm", "http://localhost:8100")
        assert client is not None

    def test_pool_returns_same_client_on_repeat(self):
        from backend.ai.src.services.connection_pool import ConnectionPool

        pool = ConnectionPool()
        c1 = pool.get_client("vllm", "http://localhost:8100")
        c2 = pool.get_client("vllm", "http://localhost:8100")
        assert c1 is c2

    @pytest.mark.asyncio
    async def test_pool_recreates_after_close(self):
        from backend.ai.src.services.connection_pool import ConnectionPool

        pool = ConnectionPool()
        pool.get_client("tgi", "http://localhost:8101")
        await pool.close_client("tgi")
        c = pool.get_client("tgi", "http://localhost:8101")
        assert c is not None

    def test_pool_to_dict(self):
        from backend.ai.src.services.connection_pool import ConnectionPool

        pool = ConnectionPool()
        pool.get_client("vllm", "http://localhost:8100")
        pool.get_client("tgi", "http://localhost:8101")
        status = pool.to_dict()
        assert isinstance(status, dict)

    @pytest.mark.asyncio
    async def test_pool_close_all(self):
        from backend.ai.src.services.connection_pool import ConnectionPool

        pool = ConnectionPool()
        pool.get_client("vllm", "http://localhost:8100")
        await pool.close_all()


# --- Circuit Breaker State Machine --------------------------------------------


class TestCircuitBreakerStateMachine:
    """Full state machine: CLOSED -> OPEN -> HALF_OPEN -> CLOSED / OPEN."""

    def test_closed_to_open_on_threshold(self):
        from backend.ai.src.services.circuit_breaker import CircuitBreaker, CircuitState

        cb = CircuitBreaker(name="e2e-test", failure_threshold=3, recovery_timeout=0.1)
        assert cb.state == CircuitState.CLOSED
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

    def test_open_rejects_requests(self):
        from backend.ai.src.services.circuit_breaker import CircuitBreaker, CircuitState

        cb = CircuitBreaker(name="e2e-reject", failure_threshold=1, recovery_timeout=60)
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.allow_request() is False

    def test_half_open_recovery(self):
        from backend.ai.src.services.circuit_breaker import CircuitBreaker, CircuitState

        cb = CircuitBreaker(name="e2e-recover", failure_threshold=1, recovery_timeout=0.05)
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        time.sleep(0.1)
        assert cb.state == CircuitState.HALF_OPEN
        assert cb.allow_request() is True
        cb.record_success()
        assert cb.state == CircuitState.CLOSED

    def test_half_open_failure_reopens(self):
        from backend.ai.src.services.circuit_breaker import CircuitBreaker, CircuitState

        cb = CircuitBreaker(name="e2e-reopen", failure_threshold=1, recovery_timeout=0.05)
        cb.record_failure()
        time.sleep(0.1)
        assert cb.state == CircuitState.HALF_OPEN
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

    def test_total_rejections_tracked(self):
        from backend.ai.src.services.circuit_breaker import CircuitBreaker, CircuitState

        cb = CircuitBreaker(name="e2e-track", failure_threshold=1, recovery_timeout=60)
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        cb.allow_request()
        cb.allow_request()
        assert cb.total_rejections >= 2


# --- Embedding Service E2E ---------------------------------------------------


class TestEmbeddingServiceE2E:
    """Embedding batch, similarity, dimension reduction via fallback path."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        from backend.ai.src.services.embedding import EmbeddingService

        self.svc = EmbeddingService(
            engine_manager=None,
            default_model="BAAI/bge-large-en-v1.5",
            default_dimensions=1024,
        )

    @pytest.mark.asyncio
    async def test_single_embed(self):
        result = await self.svc.embed("hello world")
        assert result.model_id == "BAAI/bge-large-en-v1.5"
        assert len(result.embeddings[0]) == 1024
        assert result.total_tokens > 0

    @pytest.mark.asyncio
    async def test_batch_embed(self):
        result = await self.svc.embed_batch(["alpha", "beta", "gamma"])
        assert len(result.embeddings) == 3
        for emb in result.embeddings:
            assert len(emb) == 1024

    @pytest.mark.asyncio
    async def test_similarity_symmetric(self):
        sim = await self.svc.similarity("kubernetes", "deployment")
        assert -1.0 <= sim.cosine_similarity <= 1.0
        sim_rev = await self.svc.similarity("deployment", "kubernetes")
        assert abs(sim.cosine_similarity - sim_rev.cosine_similarity) < 1e-9

    @pytest.mark.asyncio
    async def test_dimension_reduction(self):
        result = await self.svc.embed("test", dimensions=256)
        assert len(result.embeddings[0]) == 256

    @pytest.mark.asyncio
    async def test_embed_deterministic(self):
        r1 = await self.svc.embed("deterministic")
        r2 = await self.svc.embed("deterministic")
        assert r1.embeddings == r2.embeddings

    @pytest.mark.asyncio
    async def test_embed_stats(self):
        await self.svc.embed("stats test")
        stats = self.svc.get_stats()
        assert stats["total_requests"] >= 1


# --- Worker Job Lifecycle -----------------------------------------------------


class TestWorkerJobLifecycle:
    """Submit -> poll -> complete -> cancel flow."""

    @pytest.mark.asyncio
    async def test_full_job_lifecycle(self):
        from backend.ai.src.services.worker import InferenceWorker, InferenceJob, JobPriority

        worker = InferenceWorker()
        await worker.start(concurrency=2)
        try:
            job = InferenceJob(
                model_id="default",
                prompt="E2E lifecycle test",
                priority=JobPriority.HIGH,
            )
            job_id = await worker.submit(job)
            assert job_id is not None

            retrieved = worker.get_job(job_id)
            assert retrieved is not None
            assert retrieved.prompt == "E2E lifecycle test"

            jobs = worker.list_jobs()
            assert any(j.job_id == job_id for j in jobs)
        finally:
            await worker.shutdown()

    @pytest.mark.asyncio
    async def test_cancel_pending_job(self):
        from backend.ai.src.services.worker import InferenceWorker, InferenceJob

        worker = InferenceWorker()
        await worker.start(concurrency=1)
        try:
            job = InferenceJob(model_id="default", prompt="cancel me")
            job_id = await worker.submit(job)
            cancelled = await worker.cancel(job_id)
            assert cancelled is True
        finally:
            await worker.shutdown()

    @pytest.mark.asyncio
    async def test_submit_requires_start(self):
        from backend.ai.src.services.worker import InferenceWorker, InferenceJob

        worker = InferenceWorker()
        job = InferenceJob(model_id="default", prompt="fail")
        with pytest.raises(RuntimeError):
            await worker.submit(job)

    def test_worker_stats(self):
        from backend.ai.src.services.worker import InferenceWorker

        worker = InferenceWorker()
        stats = worker.get_stats()
        assert "running" in stats
        assert "total_submitted" in stats

    @pytest.mark.asyncio
    async def test_cleanup_stale(self):
        from backend.ai.src.services.worker import InferenceWorker

        worker = InferenceWorker(stale_timeout=0.001)
        await worker.start(concurrency=1)
        try:
            cleaned = await worker.cleanup_stale()
            assert isinstance(cleaned, int)
        finally:
            await worker.shutdown()


# --- gRPC Servicer Contracts --------------------------------------------------


class TestGrpcServicerContracts:
    """Verify gRPC servicer request/response data contracts."""

    def test_generate_request_creation(self):
        from backend.ai.src.services.grpc_server import GenerateRequest

        req = GenerateRequest(
            prompt="test prompt",
            model_id="default",
            max_tokens=256,
            temperature=0.7,
        )
        assert req.prompt == "test prompt"
        assert req.model_id == "default"
        assert req.max_tokens == 256

    def test_generate_response_creation(self):
        from backend.ai.src.services.grpc_server import GenerateResponse

        resp = GenerateResponse(
            request_id="req-123",
            content="generated text",
            model_id="default",
            engine="vllm",
            latency_ms=42.5,
        )
        assert resp.request_id == "req-123"
        assert resp.content == "generated text"
        assert resp.latency_ms == 42.5

    def test_embedding_request_creation(self):
        from backend.ai.src.services.grpc_server import EmbeddingRequest

        req = EmbeddingRequest(
            texts=["hello", "world"],
            model_id="BAAI/bge-large-en-v1.5",
            dimensions=1024,
        )
        assert len(req.texts) == 2
        assert req.dimensions == 1024

    def test_embedding_response_creation(self):
        from backend.ai.src.services.grpc_server import EmbeddingResponse

        resp = EmbeddingResponse(
            request_id="emb-456",
            embeddings=[[0.1, 0.2], [0.3, 0.4]],
            model_id="BAAI/bge-large-en-v1.5",
            dimensions=2,
            total_tokens=4,
        )
        assert len(resp.embeddings) == 2
        assert resp.total_tokens == 4

    @pytest.mark.asyncio
    async def test_servicer_health_check(self):
        from backend.ai.src.services.grpc_server import InferenceServicer

        servicer = InferenceServicer(engine_manager=None)
        health = await servicer.HealthCheck()
        assert health.status in ("healthy", "degraded", "ok", "SERVING")

    def test_servicer_metrics(self):
        from backend.ai.src.services.grpc_server import InferenceServicer

        servicer = InferenceServicer(engine_manager=None)
        metrics = servicer.get_metrics()
        assert isinstance(metrics, dict)


# --- Health Monitor Probe Cycle -----------------------------------------------


class TestHealthMonitorProbe:
    """Verify health monitor configuration and probe logic."""

    def test_config_defaults(self):
        from backend.ai.src.services.health_monitor import HealthMonitorConfig

        cfg = HealthMonitorConfig()
        assert cfg.probe_interval > 0
        assert cfg.stale_cleanup_interval > 0

    @pytest.mark.asyncio
    async def test_monitor_start_stop(self):
        from backend.ai.src.services.health_monitor import (
            EngineHealthMonitor,
            HealthMonitorConfig,
        )

        monitor = EngineHealthMonitor(
            config=HealthMonitorConfig(probe_interval=0.05),
            engine_manager=None,
            model_registry=None,
            inference_worker=None,
        )
        await monitor.start()
        assert monitor._running is True
        await asyncio.sleep(0.1)
        await monitor.stop()
        assert monitor._running is False

    def test_monitor_stats(self):
        from backend.ai.src.services.health_monitor import (
            EngineHealthMonitor,
            HealthMonitorConfig,
        )

        monitor = EngineHealthMonitor(
            config=HealthMonitorConfig(),
            engine_manager=None,
            model_registry=None,
            inference_worker=None,
        )
        stats = monitor.get_stats()
        assert "running" in stats
        assert "total_probes" in stats


# --- Governance Audit Trail ---------------------------------------------------


class TestGovernanceAuditTrail:
    """Verify governance engine produces traceable audit records."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        from backend.ai.src.governance import GovernanceEngine

        self.gov = GovernanceEngine()

    def test_stamp_contains_all_blocks(self):
        stamp = self.gov.stamp_governance("e2e-svc", "eco-base", "Deployment")
        assert "document_metadata" in stamp
        assert "governance_info" in stamp
        assert "registry_binding" in stamp
        assert "vector_alignment_map" in stamp

    def test_stamp_uri_format(self):
        stamp = self.gov.stamp_governance("test-svc", "eco-base", "Service")
        uri = stamp["document_metadata"]["uri"]
        assert uri.startswith("eco-base://")

    def test_stamp_urn_format(self):
        stamp = self.gov.stamp_governance("test-svc", "eco-base", "Service")
        urn = stamp["document_metadata"]["urn"]
        assert urn.startswith("urn:eco-base:")

    def test_audit_log_grows(self):
        initial = len(self.gov.get_audit_log())
        self.gov.stamp_governance("audit-test", "eco-base", "ConfigMap")
        after = len(self.gov.get_audit_log())
        assert after > initial

    def test_resolve_engine_vllm(self):
        engine = self.gov.resolve_engine("vllm-default")
        assert engine == "vllm_adapter"

    def test_resolve_engine_ollama(self):
        engine = self.gov.resolve_engine("ollama-chat")
        assert engine == "ollama_adapter"

    def test_resolve_engine_unknown_fallback(self):
        engine = self.gov.resolve_engine("unknown-engine-xyz")
        assert engine is not None


# --- Config Validation --------------------------------------------------------


class TestConfigValidation:
    """Verify Settings loads correct defaults."""

    def test_default_ports(self):
        from backend.ai.src.config import Settings

        s = Settings()
        assert s.http_port == 8001
        assert s.grpc_port == 8000

    def test_default_vector_config(self):
        from backend.ai.src.config import Settings

        s = Settings()
        assert s.vector_dim == 1024
        assert s.alignment_model == "BAAI/bge-large-en-v1.5"

    def test_default_redis(self):
        from backend.ai.src.config import Settings

        s = Settings()
        assert "redis" in s.redis_url
        assert "redis" in s.celery_broker

    def test_cors_origins(self):
        from backend.ai.src.config import Settings

        s = Settings()
        assert isinstance(s.cors_origins, list)
        assert len(s.cors_origins) >= 1


# --- Model Registry E2E ------------------------------------------------------


class TestModelRegistryE2E:
    """Registry resolve, filter, lifecycle across the full model set."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        from src.core.registry import ModelRegistry

        self.registry = ModelRegistry()

    @pytest.mark.asyncio
    async def test_list_returns_default_models(self):
        models = await self.registry.list_models()
        assert len(models) >= 5
        ids = [m.model_id for m in models]
        assert "llama-3.1-8b-instruct" in ids

    @pytest.mark.asyncio
    async def test_resolve_default(self):
        model = await self.registry.resolve_model("default")
        assert model is not None

    @pytest.mark.asyncio
    async def test_resolve_specific(self):
        model = await self.registry.resolve_model("llama-3.1-8b-instruct")
        assert model is not None
        assert model.model_id == "llama-3.1-8b-instruct"

    @pytest.mark.asyncio
    async def test_resolve_nonexistent(self):
        model = await self.registry.resolve_model("nonexistent-model-xyz")
        assert model is None

    @pytest.mark.asyncio
    async def test_filter_by_capability(self):
        from src.schemas.models import ModelCapability

        models = await self.registry.list_models(capability=ModelCapability.CHAT)
        assert len(models) >= 1
        for m in models:
            assert ModelCapability.CHAT in m.capabilities

    def test_count(self):
        assert self.registry.count >= 5


# --- Engine Manager E2E ------------------------------------------------------


class TestEngineManagerE2E:
    """Engine manager init, generate (degraded), health."""

    @pytest.mark.asyncio
    async def test_initialize_and_health(self):
        from backend.ai.src.services.engine_manager import EngineManager

        mgr = EngineManager(
            endpoints={
                "vllm": "http://localhost:8100",
                "tgi": "http://localhost:8101",
                "ollama": "http://localhost:11434",
            },
            failure_threshold=3,
            recovery_timeout=30.0,
        )
        await mgr.initialize()
        health = mgr.get_health()
        assert "engines" in health
        assert "vllm" in health["engines"]
        assert "tgi" in health["engines"]
        assert "ollama" in health["engines"]
        await mgr.shutdown()

    @pytest.mark.asyncio
    async def test_generate_degraded_mode(self):
        from backend.ai.src.services.engine_manager import EngineManager

        mgr = EngineManager(
            endpoints={"vllm": "http://localhost:8100"},
            failure_threshold=1,
            recovery_timeout=60.0,
        )
        await mgr.initialize()
        result = await mgr.generate(
            prompt="test degraded",
            model_id="default",
            max_tokens=64,
        )
        assert "content" in result
        assert "engine" in result
        await mgr.shutdown()

    @pytest.mark.asyncio
    async def test_get_health_structure(self):
        from backend.ai.src.services.engine_manager import EngineManager

        mgr = EngineManager(
            endpoints={"vllm": "http://localhost:8100"},
            failure_threshold=3,
            recovery_timeout=30.0,
        )
        await mgr.initialize()
        health = mgr.get_health()
        assert isinstance(health, dict)
        assert "engines" in health
        assert "circuits" in health
        assert "pool" in health
        await mgr.shutdown()

    @pytest.mark.asyncio
    async def test_resolve_engine(self):
        from backend.ai.src.services.engine_manager import EngineManager

        mgr = EngineManager(
            endpoints={"vllm": "http://localhost:8100"},
        )
        await mgr.initialize()
        engine = mgr.resolve_engine("default")
        assert engine is not None
        await mgr.shutdown()


# --- Request Queue E2E -------------------------------------------------------


class TestRequestQueueE2E:
    """Queue enqueue, dequeue, priority ordering."""

    @pytest.mark.asyncio
    async def test_enqueue_dequeue(self):
        from src.core.queue import RequestQueue, QueuedRequest, Priority

        q = RequestQueue()
        req_high = QueuedRequest(payload={"prompt": "high"}, model="default", priority=Priority.HIGH)
        req_low = QueuedRequest(payload={"prompt": "low"}, model="default", priority=Priority.LOW)
        await q.enqueue(req_low)
        await q.enqueue(req_high)
        item = await q.dequeue()
        assert item.payload["prompt"] == "high"

    @pytest.mark.asyncio
    async def test_queue_depth(self):
        from src.core.queue import RequestQueue, QueuedRequest

        q = RequestQueue()
        assert q.depth == 0
        await q.enqueue(QueuedRequest(payload={"prompt": "test"}))
        assert q.depth == 1

    @pytest.mark.asyncio
    async def test_queue_stats(self):
        from src.core.queue import RequestQueue

        q = RequestQueue()
        stats = await q.get_stats()
        assert isinstance(stats, dict)


# --- Shared Utils E2E --------------------------------------------------------


class TestSharedUtilsE2E:
    """Verify shared utility functions produce valid identifiers."""

    def test_uuid_v1(self):
        from backend.shared.utils import new_uuid

        uid = new_uuid()
        assert uid.version == 1

    def test_uri_format(self):
        from backend.shared.utils import build_uri

        uri = build_uri("k8s", "deployment", "e2e-test")
        assert uri == "eco-base://k8s/deployment/e2e-test"

    def test_urn_format(self):
        from backend.shared.utils import build_urn, new_uuid

        uid = new_uuid()
        urn = build_urn("k8s", "deployment", "e2e-test", uid)
        assert urn.startswith("urn:eco-base:")
        assert "e2e-test" in urn

    def test_governance_stamp(self):
        from backend.shared.utils import governance_stamp

        stamp = governance_stamp()
        assert stamp["schema_version"] == "v1"
        assert stamp["generated_by"] == "yaml-toolkit-v1"

    def test_qyaml_metadata_complete(self):
        from backend.shared.utils import build_qyaml_metadata

        meta = build_qyaml_metadata("e2e-svc", "eco-base", "Deployment", "gke-prod")
        for block in ["document_metadata", "governance_info", "registry_binding", "vector_alignment_map"]:
            assert block in meta
        assert meta["document_metadata"]["schema_version"] == "v1"
        assert "eco-base://" in meta["document_metadata"]["uri"]
        assert "urn:eco-base:" in meta["document_metadata"]["urn"]
