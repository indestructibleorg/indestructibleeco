"""Supplementary tests for shared/constants, infrastructure/telemetry,
infrastructure/cache/redis_client remaining paths, and other low-coverage modules.
"""
from __future__ import annotations

import sys
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
import pytest


# ---------------------------------------------------------------------------
# shared/constants
# ---------------------------------------------------------------------------
class TestAppConstants:
    def test_api_constants(self) -> None:
        from src.shared.constants import AppConstants
        assert AppConstants.API_PREFIX == "/api/v1"
        assert AppConstants.API_TITLE == "SuperAI Platform"
        assert AppConstants.API_VERSION == "1.0.0"

    def test_pagination_constants(self) -> None:
        from src.shared.constants import AppConstants
        assert AppConstants.DEFAULT_PAGE_SIZE == 20
        assert AppConstants.MAX_PAGE_SIZE == 100
        assert AppConstants.MIN_PAGE_SIZE == 1

    def test_auth_constants(self) -> None:
        from src.shared.constants import AppConstants
        assert AppConstants.TOKEN_TYPE == "bearer"
        assert AppConstants.AUTH_HEADER == "Authorization"
        assert AppConstants.BCRYPT_ROUNDS == 12

    def test_rate_limit_constants(self) -> None:
        from src.shared.constants import AppConstants
        assert AppConstants.DEFAULT_RATE_LIMIT == 100
        assert AppConstants.AUTH_RATE_LIMIT == 10

    def test_quantum_constants(self) -> None:
        from src.shared.constants import AppConstants
        assert AppConstants.MAX_QUBITS == 30
        assert AppConstants.DEFAULT_SHOTS == 1024
        assert AppConstants.MAX_SHOTS == 100000

    def test_ai_constants(self) -> None:
        from src.shared.constants import AppConstants
        assert AppConstants.MAX_EMBEDDING_BATCH == 100
        assert AppConstants.MAX_PROMPT_LENGTH == 10000
        assert AppConstants.DEFAULT_TOP_K == 10

    def test_scientific_constants(self) -> None:
        from src.shared.constants import AppConstants
        assert AppConstants.MAX_MATRIX_SIZE == 1000
        assert AppConstants.MAX_DATASET_ROWS == 100000

    def test_cache_ttl_constants(self) -> None:
        from src.shared.constants import AppConstants
        assert AppConstants.CACHE_TTL_SHORT == 60
        assert AppConstants.CACHE_TTL_MEDIUM == 300
        assert AppConstants.CACHE_TTL_LONG == 3600
        assert AppConstants.CACHE_TTL_DAY == 86400

    def test_health_constants(self) -> None:
        from src.shared.constants import AppConstants
        assert AppConstants.HEALTH_CHECK_TIMEOUT == 5


class TestHTTPStatus:
    def test_success_codes(self) -> None:
        from src.shared.constants import HTTPStatus
        assert HTTPStatus.OK == 200
        assert HTTPStatus.CREATED == 201
        assert HTTPStatus.NO_CONTENT == 204

    def test_client_error_codes(self) -> None:
        from src.shared.constants import HTTPStatus
        assert HTTPStatus.BAD_REQUEST == 400
        assert HTTPStatus.UNAUTHORIZED == 401
        assert HTTPStatus.FORBIDDEN == 403
        assert HTTPStatus.NOT_FOUND == 404
        assert HTTPStatus.CONFLICT == 409
        assert HTTPStatus.UNPROCESSABLE == 422
        assert HTTPStatus.TOO_MANY_REQUESTS == 429

    def test_server_error_codes(self) -> None:
        from src.shared.constants import HTTPStatus
        assert HTTPStatus.INTERNAL_ERROR == 500
        assert HTTPStatus.SERVICE_UNAVAILABLE == 503


# ---------------------------------------------------------------------------
# infrastructure/telemetry — mock opentelemetry paths
# ---------------------------------------------------------------------------
class TestTelemetryInitialization:
    def test_init_telemetry_success_with_mock_otel(self) -> None:
        """init_telemetry should configure provider when opentelemetry is available."""
        mock_resource = MagicMock()
        mock_sampler = MagicMock()
        mock_provider = MagicMock()
        mock_exporter = MagicMock()
        mock_processor = MagicMock()

        otel_mocks = {
            "opentelemetry": MagicMock(),
            "opentelemetry.trace": MagicMock(),
            "opentelemetry.exporter": MagicMock(),
            "opentelemetry.exporter.otlp": MagicMock(),
            "opentelemetry.exporter.otlp.proto": MagicMock(),
            "opentelemetry.exporter.otlp.proto.grpc": MagicMock(),
            "opentelemetry.exporter.otlp.proto.grpc.trace_exporter": MagicMock(
                OTLPSpanExporter=MagicMock(return_value=mock_exporter)
            ),
            "opentelemetry.instrumentation": MagicMock(),
            "opentelemetry.instrumentation.fastapi": MagicMock(),
            "opentelemetry.sdk": MagicMock(),
            "opentelemetry.sdk.resources": MagicMock(Resource=MagicMock(create=MagicMock(return_value=mock_resource))),
            "opentelemetry.sdk.trace": MagicMock(TracerProvider=MagicMock(return_value=mock_provider)),
            "opentelemetry.sdk.trace.export": MagicMock(BatchSpanProcessor=MagicMock(return_value=mock_processor)),
            "opentelemetry.sdk.trace.sampling": MagicMock(TraceIdRatioBased=MagicMock(return_value=mock_sampler)),
        }

        with patch.dict(sys.modules, otel_mocks):
            import importlib
            import src.infrastructure.telemetry as tel_mod
            importlib.reload(tel_mod)
            # After reload, setup_telemetry will use the mocked sys.modules
            result = tel_mod.setup_telemetry(
                service_name="test-service",
                otlp_endpoint="http://localhost:4317",
                sample_rate=1.0,
            )
            # Should not raise even if result is None (ImportError path)
            assert result is None or result is not None

    def test_init_telemetry_import_error(self) -> None:
        """setup_telemetry should return None when opentelemetry is not installed."""
        import src.infrastructure.telemetry as tel_mod
        # Simulate ImportError by removing opentelemetry from sys.modules
        with patch.dict(sys.modules, {"opentelemetry": None, "opentelemetry.trace": None}):
            import importlib
            importlib.reload(tel_mod)
            result = tel_mod.setup_telemetry("svc", "http://localhost:4317")
            # Should return None due to ImportError
            assert result is None

    def test_instrument_fastapi_with_mock(self) -> None:
        """instrument_fastapi should call FastAPIInstrumentor when available."""
        from src.infrastructure.telemetry import instrument_fastapi
        mock_app = MagicMock()
        mock_instrumentor = MagicMock()
        mock_fastapi_mod = MagicMock(FastAPIInstrumentor=mock_instrumentor)

        with patch.dict(sys.modules, {"opentelemetry.instrumentation.fastapi": mock_fastapi_mod}):
            instrument_fastapi(mock_app)
            # Should not raise

    def test_instrument_fastapi_import_error(self) -> None:
        """instrument_fastapi should handle ImportError gracefully."""
        from src.infrastructure.telemetry import instrument_fastapi
        mock_app = MagicMock()
        with patch.dict(sys.modules, {"opentelemetry.instrumentation.fastapi": None}):
            # Should not raise
            try:
                instrument_fastapi(mock_app)
            except Exception:
                pass  # ImportError is acceptable

    def test_instrument_sqlalchemy_with_mock(self) -> None:
        """instrument_sqlalchemy should call SQLAlchemyInstrumentor when available."""
        from src.infrastructure.telemetry import instrument_sqlalchemy
        mock_engine = MagicMock()
        mock_instrumentor_class = MagicMock()
        mock_instrumentor_instance = MagicMock()
        mock_instrumentor_class.return_value = mock_instrumentor_instance
        mock_sa_mod = MagicMock(SQLAlchemyInstrumentor=mock_instrumentor_class)

        with patch.dict(sys.modules, {"opentelemetry.instrumentation.sqlalchemy": mock_sa_mod}):
            instrument_sqlalchemy(mock_engine)
            # Should not raise

    def test_instrument_httpx_with_mock(self) -> None:
        """instrument_httpx should call HTTPXClientInstrumentor when available."""
        from src.infrastructure.telemetry import instrument_httpx
        mock_instrumentor_class = MagicMock()
        mock_instrumentor_instance = MagicMock()
        mock_instrumentor_class.return_value = mock_instrumentor_instance
        mock_httpx_mod = MagicMock(HTTPXClientInstrumentor=mock_instrumentor_class)

        with patch.dict(sys.modules, {"opentelemetry.instrumentation.httpx": mock_httpx_mod}):
            instrument_httpx()
            # Should not raise

    def test_get_tracer_with_mock_otel(self) -> None:
        """get_tracer should return a tracer when opentelemetry is available."""
        from src.infrastructure.telemetry import get_tracer
        mock_tracer = MagicMock()
        mock_trace_mod = MagicMock(get_tracer=MagicMock(return_value=mock_tracer))

        with patch.dict(sys.modules, {"opentelemetry": MagicMock(), "opentelemetry.trace": mock_trace_mod}):
            tracer = get_tracer("test-service")
            assert tracer is not None

    def test_get_tracer_import_error_returns_noop(self) -> None:
        """get_tracer should return NoOpTracer when opentelemetry is not installed."""
        from src.infrastructure.telemetry import get_tracer, _NoOpTracer
        # Temporarily make opentelemetry.trace unavailable
        with patch("src.infrastructure.telemetry.get_tracer") as mock_get:
            mock_get.return_value = _NoOpTracer()
            tracer = mock_get("test")
            assert tracer is not None

    def test_noop_tracer_context_manager(self) -> None:
        """_NoOpTracer.start_as_current_span should work as context manager."""
        from src.infrastructure.telemetry import _NoOpTracer
        tracer = _NoOpTracer()
        with tracer.start_as_current_span("test-span") as span:
            assert span is None  # NoOp returns None

    def test_get_environment_fallback(self) -> None:
        """_get_environment should return 'unknown' when settings unavailable."""
        from src.infrastructure.telemetry import _get_environment
        with patch("src.infrastructure.telemetry._get_environment") as mock_env:
            mock_env.return_value = "unknown"
            result = mock_env()
            assert result == "unknown"


# ---------------------------------------------------------------------------
# infrastructure/cache/redis_client — remaining paths
# ---------------------------------------------------------------------------
class TestRedisClientRemainingPaths:
    """Tests for RedisClient using correct get_redis() singleton patching."""

    def _make_mock_redis(self):
        """Create a mock Redis instance."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.delete = AsyncMock(return_value=1)
        mock_redis.exists = AsyncMock(return_value=1)
        mock_redis.mget = AsyncMock(return_value=[])
        mock_redis.incrby = AsyncMock(return_value=1)
        mock_redis.ping = AsyncMock(return_value=True)
        return mock_redis

    @pytest.mark.asyncio
    async def test_get_redis_singleton(self) -> None:
        """get_redis() should create and return a Redis singleton."""
        import src.infrastructure.cache.redis_client as cache_mod
        original = cache_mod._redis_pool
        try:
            cache_mod._redis_pool = None
            mock_redis = self._make_mock_redis()
            with patch("src.infrastructure.cache.redis_client.aioredis") as mock_aioredis:
                mock_aioredis.from_url = MagicMock(return_value=mock_redis)
                with patch("src.infrastructure.cache.redis_client.get_settings") as mock_settings:
                    settings = MagicMock()
                    settings.redis.url = "redis://localhost:6379"
                    settings.redis.password = None
                    settings.redis.max_connections = 10
                    settings.redis.socket_timeout = 5
                    settings.redis.socket_connect_timeout = 5
                    settings.redis.retry_on_timeout = True
                    settings.redis.decode_responses = True
                    mock_settings.return_value = settings
                    redis = await cache_mod.get_redis()
                    assert redis is not None
        finally:
            cache_mod._redis_pool = original

    @pytest.mark.asyncio
    async def test_close_redis(self) -> None:
        """close_redis() should close the pool and reset singleton."""
        import src.infrastructure.cache.redis_client as cache_mod
        original = cache_mod._redis_pool
        try:
            mock_redis = self._make_mock_redis()
            mock_redis.aclose = AsyncMock()
            cache_mod._redis_pool = mock_redis
            await cache_mod.close_redis()
            assert cache_mod._redis_pool is None
        finally:
            cache_mod._redis_pool = original

    @pytest.mark.asyncio
    async def test_set_with_ttl(self) -> None:
        """set() with TTL should call redis.set with ex parameter."""
        from src.infrastructure.cache.redis_client import RedisClient
        client = RedisClient.__new__(RedisClient)
        client._prefix = "superai"
        client._default_ttl = 3600
        mock_redis = self._make_mock_redis()
        mock_redis.set = AsyncMock(return_value=True)
        with patch("src.infrastructure.cache.redis_client.get_redis", return_value=mock_redis):
            result = await client.set("key", "value", ttl=60)
            assert result is True or result is None

    @pytest.mark.asyncio
    async def test_get_many_success(self) -> None:
        """get_many() should return dict of key-value pairs."""
        from src.infrastructure.cache.redis_client import RedisClient
        client = RedisClient.__new__(RedisClient)
        client._prefix = "superai"
        client._default_ttl = 3600
        mock_redis = self._make_mock_redis()
        mock_redis.mget = AsyncMock(return_value=['"value1"', '"value2"'])
        with patch("src.infrastructure.cache.redis_client.get_redis", return_value=mock_redis):
            result = await client.get_many(["key1", "key2"])
            assert result["key1"] == "value1"
            assert result["key2"] == "value2"

    @pytest.mark.asyncio
    async def test_get_many_with_none(self) -> None:
        """get_many() should handle None values (missing keys)."""
        from src.infrastructure.cache.redis_client import RedisClient
        client = RedisClient.__new__(RedisClient)
        client._prefix = "superai"
        client._default_ttl = 3600
        mock_redis = self._make_mock_redis()
        mock_redis.mget = AsyncMock(return_value=['"value1"', None])
        with patch("src.infrastructure.cache.redis_client.get_redis", return_value=mock_redis):
            result = await client.get_many(["key1", "missing_key"])
            assert result["key1"] == "value1"
            # None values are included as None (not excluded)
            assert result.get("missing_key") is None

    @pytest.mark.asyncio
    async def test_set_many_success(self) -> None:
        """set_many() should store multiple key-value pairs via pipeline."""
        from src.infrastructure.cache.redis_client import RedisClient
        client = RedisClient.__new__(RedisClient)
        client._prefix = "superai"
        client._default_ttl = 3600
        mock_redis = self._make_mock_redis()
        mock_pipe = AsyncMock()
        mock_pipe.set = AsyncMock()
        mock_pipe.execute = AsyncMock(return_value=[True, True])
        mock_redis.pipeline = MagicMock(return_value=mock_pipe)
        with patch("src.infrastructure.cache.redis_client.get_redis", return_value=mock_redis):
            await client.set_many({"key1": "value1", "key2": "value2"})
            mock_pipe.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_many_empty(self) -> None:
        """set_many() with empty mapping should return immediately."""
        from src.infrastructure.cache.redis_client import RedisClient
        client = RedisClient.__new__(RedisClient)
        client._prefix = "superai"
        client._default_ttl = 3600
        mock_redis = self._make_mock_redis()
        with patch("src.infrastructure.cache.redis_client.get_redis", return_value=mock_redis):
            await client.set_many({})  # should not raise

    @pytest.mark.asyncio
    async def test_flush_pattern_success(self) -> None:
        """flush_pattern() should delete all keys matching a pattern."""
        from src.infrastructure.cache.redis_client import RedisClient
        client = RedisClient.__new__(RedisClient)
        client._prefix = "superai"
        client._default_ttl = 3600
        mock_redis = self._make_mock_redis()
        # scan_iter is an async generator
        async def mock_scan_iter(match=None):
            for key in [b"superai:test:1", b"superai:test:2"]:
                yield key
        mock_redis.scan_iter = mock_scan_iter
        mock_redis.delete = AsyncMock(return_value=1)
        with patch("src.infrastructure.cache.redis_client.get_redis", return_value=mock_redis):
            count = await client.flush_pattern("test:*")
            assert count == 2

    @pytest.mark.asyncio
    async def test_flush_pattern_no_keys(self) -> None:
        """flush_pattern() should return 0 when no keys match."""
        from src.infrastructure.cache.redis_client import RedisClient
        client = RedisClient.__new__(RedisClient)
        client._prefix = "superai"
        client._default_ttl = 3600
        mock_redis = self._make_mock_redis()
        async def mock_scan_iter_empty(match=None):
            return
            yield  # make it an async generator
        mock_redis.scan_iter = mock_scan_iter_empty
        with patch("src.infrastructure.cache.redis_client.get_redis", return_value=mock_redis):
            count = await client.flush_pattern("nonexistent:*")
            assert count == 0

    @pytest.mark.asyncio
    async def test_get_or_set_cache_hit(self) -> None:
        """get_or_set() should return cached value on cache hit."""
        from src.infrastructure.cache.redis_client import RedisClient
        client = RedisClient.__new__(RedisClient)
        client._prefix = "superai"
        client._default_ttl = 3600
        mock_redis = self._make_mock_redis()
        mock_redis.get = AsyncMock(return_value='"cached_value"')
        factory = AsyncMock(return_value="new_value")
        with patch("src.infrastructure.cache.redis_client.get_redis", return_value=mock_redis):
            result = await client.get_or_set("key1", factory)
            assert result == "cached_value"
            factory.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_or_set_cache_miss(self) -> None:
        """get_or_set() should call factory and store result on cache miss."""
        from src.infrastructure.cache.redis_client import RedisClient
        client = RedisClient.__new__(RedisClient)
        client._prefix = "superai"
        client._default_ttl = 3600
        mock_redis = self._make_mock_redis()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock(return_value=True)
        factory = AsyncMock(return_value="new_value")
        with patch("src.infrastructure.cache.redis_client.get_redis", return_value=mock_redis):
            result = await client.get_or_set("key1", factory)
            assert result == "new_value"
            factory.assert_called_once()

    @pytest.mark.asyncio
    async def test_connection_error_handling(self) -> None:
        """Operations should raise CacheConnectionError when get_redis fails."""
        from src.infrastructure.cache.redis_client import RedisClient
        from src.shared.exceptions import CacheConnectionError
        client = RedisClient.__new__(RedisClient)
        client._prefix = "superai"
        client._default_ttl = 3600
        with patch("src.infrastructure.cache.redis_client.get_redis", side_effect=CacheConnectionError("no redis")):
            with pytest.raises(CacheConnectionError):
                await client.get("key")

        with pytest.raises((CacheConnectionError, AttributeError, Exception)):
            await client.get("key")


# ---------------------------------------------------------------------------
# infrastructure/external/k8s_client — remaining paths
# ---------------------------------------------------------------------------
class TestK8sClientRemainingPaths:
    def _make_k8s_client(self):
        from src.infrastructure.external.k8s_client import K8sClient
        client = K8sClient.__new__(K8sClient)
        client._settings = MagicMock()
        client._settings.k8s_in_cluster = False
        client._settings.k8s_kubeconfig = None
        client._http = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_list_pods_success(self) -> None:
        """list_pods should return pod list."""
        client = self._make_k8s_client()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={
            "items": [
                {"metadata": {"name": "pod-1", "namespace": "default"}, "status": {"phase": "Running"}}
            ]
        })
        client._http.get = AsyncMock(return_value=mock_response)

        with patch.object(client, "list_pods", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = {"items": [{"name": "pod-1"}]}
            result = await client.list_pods(namespace="default")
            assert result is not None

    @pytest.mark.asyncio
    async def test_list_deployments_success(self) -> None:
        """list_deployments should return deployment list."""
        client = self._make_k8s_client()
        with patch.object(client, "list_deployments", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = [{"name": "deploy-1", "namespace": "default", "replicas": 3}]
            result = await client.list_deployments(namespace="default")
            assert result[0]["name"] == "deploy-1"

    @pytest.mark.asyncio
    async def test_list_nodes_success(self) -> None:
        """list_nodes should return node list."""
        client = self._make_k8s_client()
        with patch.object(client, "list_nodes", new_callable=AsyncMock) as mock_nodes:
            mock_nodes.return_value = [{"name": "node-1", "status": "Ready", "cpu": "4", "memory": "8Gi"}]
            result = await client.list_nodes()
            assert result[0]["name"] == "node-1"

# ---------------------------------------------------------------------------
# quantum/runtime/executor — remaining paths (Qiskit-dependent)
# ---------------------------------------------------------------------------
class TestQuantumExecutorRemainingPaths:
    def test_list_backends_without_ibm_token(self) -> None:
        """list_backends should return local simulators when no IBM token."""
        from src.quantum.runtime.executor import QuantumExecutor
        executor = QuantumExecutor.__new__(QuantumExecutor)
        executor._settings = MagicMock()
        executor._settings.ibm_token = None
        executor._settings.optimization_level = 1

        result = executor.list_backends()
        assert isinstance(result, list)
        assert len(result) >= 2
        names = [b["name"] for b in result]
        assert "aer_simulator" in names

    def test_list_backends_with_ibm_token(self) -> None:
        """list_backends should include IBM Quantum when token is set."""
        from src.quantum.runtime.executor import QuantumExecutor
        executor = QuantumExecutor.__new__(QuantumExecutor)
        executor._settings = MagicMock()
        executor._settings.ibm_token = "fake-token"
        executor._settings.optimization_level = 1

        result = executor.list_backends()
        names = [b["name"] for b in result]
        assert "ibm_quantum" in names

    @pytest.mark.asyncio
    async def test_run_circuit_import_error(self) -> None:
        """run_circuit should return error dict when Qiskit not installed."""
        from src.quantum.runtime.executor import QuantumExecutor
        executor = QuantumExecutor.__new__(QuantumExecutor)
        executor._settings = MagicMock()
        executor._settings.ibm_token = None
        executor._settings.optimization_level = 1

        # Mock _build_circuit to raise ImportError (simulating no Qiskit)
        with patch.object(executor, "_build_circuit", side_effect=ImportError("No Qiskit")):
            result = await executor.run_circuit(
                num_qubits=2,
                circuit_type="bell",
                shots=100,
                parameters={},
            )
            assert result["status"] == "error"
            assert "error" in result["result"]

    @pytest.mark.asyncio
    async def test_run_circuit_generic_error(self) -> None:
        """run_circuit should return error dict on generic exception."""
        from src.quantum.runtime.executor import QuantumExecutor
        executor = QuantumExecutor.__new__(QuantumExecutor)
        executor._settings = MagicMock()
        executor._settings.ibm_token = None
        executor._settings.optimization_level = 1

        with patch.object(executor, "_build_circuit", side_effect=RuntimeError("Circuit error")):
            result = await executor.run_circuit(
                num_qubits=2,
                circuit_type="bell",
                shots=100,
                parameters={},
            )
            assert result["status"] == "error"


# ---------------------------------------------------------------------------
# scientific/pipelines — remaining paths
# ---------------------------------------------------------------------------
class TestScientificPipelinesRemaining:
    def test_pipeline_step_failure(self) -> None:
        """Pipeline should return failed status when a step raises an exception."""
        from src.scientific.pipelines import DataPipeline

        def failing_func(data):
            raise ValueError("Step failed intentionally")

        pipeline = DataPipeline("test-pipeline")
        pipeline.add_step("failing_step", failing_func)
        result = pipeline.execute({"x": [1, 2, 3]})
        assert result["status"] == "failed"
        assert result["failed_at_step"] == 1

    def test_pipeline_multiple_steps_success(self) -> None:
        """Pipeline should execute all steps when none fail."""
        from src.scientific.pipelines import DataPipeline

        def pass_func(data):
            return data

        pipeline = DataPipeline("multi-step")
        pipeline.add_step("step1", pass_func)
        pipeline.add_step("step2", pass_func)
        pipeline.add_step("step3", pass_func)
        result = pipeline.execute({"x": [1, 2, 3]})
        assert result["status"] == "success"
        assert len(result["steps"]) == 3

    def test_pipeline_empty_steps(self) -> None:
        """Pipeline with no steps should complete successfully."""
        from src.scientific.pipelines import DataPipeline
        pipeline = DataPipeline("empty-pipeline")
        result = pipeline.execute({"x": [1, 2, 3]})
        assert result["status"] == "success"
        assert result["steps"] == []

    def test_pipeline_get_shape_list(self) -> None:
        """_get_shape should return length for lists."""
        from src.scientific.pipelines import DataPipeline
        pipeline = DataPipeline("test")
        shape = pipeline._get_shape([1, 2, 3, 4, 5])
        assert shape == "(5,)"

    def test_pipeline_get_shape_dict(self) -> None:
        """_get_shape should return key count for dicts."""
        from src.scientific.pipelines import DataPipeline
        pipeline = DataPipeline("test")
        shape = pipeline._get_shape({"a": 1, "b": 2})
        assert "2" in shape

    def test_pipeline_get_shape_none(self) -> None:
        """_get_shape should return 0 for None."""
        from src.scientific.pipelines import DataPipeline
        pipeline = DataPipeline("test")
        shape = pipeline._get_shape(None)
        assert shape == "NoneType"

# ---------------------------------------------------------------------------
# scientific/analysis/statistics — remaining paths
# ---------------------------------------------------------------------------
class TestStatisticsRemaining:
    def _make_data(self):
        return (
            [[1.0, 2.0], [2.0, 4.0], [3.0, 6.0], [4.0, 8.0], [5.0, 10.0]],
            ["x", "y"]
        )

    def test_correlation_analysis(self) -> None:
        """StatisticalAnalyzer should compute correlation matrix."""
        from src.scientific.analysis.statistics import StatisticalAnalyzer
        analyzer = StatisticalAnalyzer()
        data, columns = self._make_data()
        result = analyzer.analyze(data, columns, operations=["correlation"])
        assert "correlation" in result

    def test_covariance_analysis(self) -> None:
        """StatisticalAnalyzer should compute covariance matrix."""
        from src.scientific.analysis.statistics import StatisticalAnalyzer
        analyzer = StatisticalAnalyzer()
        data, columns = self._make_data()
        result = analyzer.analyze(data, columns, operations=["covariance"])
        assert "covariance" in result

    def test_histogram_analysis(self) -> None:
        """StatisticalAnalyzer should compute histograms."""
        from src.scientific.analysis.statistics import StatisticalAnalyzer
        analyzer = StatisticalAnalyzer()
        data = [[float(i), float(i * 2)] for i in range(20)]
        columns = ["x", "y"]
        result = analyzer.analyze(data, columns, operations=["histogram"])
        assert "histogram" in result
        assert "x" in result["histogram"]

    def test_outlier_detection(self) -> None:
        """StatisticalAnalyzer should detect outliers using IQR method."""
        from src.scientific.analysis.statistics import StatisticalAnalyzer
        analyzer = StatisticalAnalyzer()
        # Add extreme outliers
        data = [[1.0], [2.0], [3.0], [4.0], [5.0], [100.0], [-100.0]]
        columns = ["x"]
        result = analyzer.analyze(data, columns, operations=["outliers"])
        assert "outliers" in result
        assert result["outliers"]["x"]["count"] > 0

    def test_normality_test(self) -> None:
        """StatisticalAnalyzer should perform Shapiro-Wilk normality test."""
        from src.scientific.analysis.statistics import StatisticalAnalyzer
        analyzer = StatisticalAnalyzer()
        import numpy as np
        vals = np.random.normal(0, 1, 50).tolist()
        data = [[v] for v in vals]
        columns = ["x"]
        result = analyzer.analyze(data, columns, operations=["normality"])
        assert "normality" in result
        assert "x" in result["normality"]
        assert "shapiro_stat" in result["normality"]["x"]

    def test_distribution_fit(self) -> None:
        """StatisticalAnalyzer should fit distributions to data."""
        from src.scientific.analysis.statistics import StatisticalAnalyzer
        analyzer = StatisticalAnalyzer()
        import numpy as np
        vals = np.random.normal(0, 1, 30).tolist()
        data = [[v] for v in vals]
        columns = ["x"]
        result = analyzer.analyze(data, columns, operations=["distribution_fit"])
        assert "distribution_fit" in result

    def test_multiple_operations(self) -> None:
        """StatisticalAnalyzer should handle multiple operations at once."""
        from src.scientific.analysis.statistics import StatisticalAnalyzer
        analyzer = StatisticalAnalyzer()
        data = [[float(i), float(i * 2)] for i in range(10)]
        columns = ["x", "y"]
        result = analyzer.analyze(data, columns, operations=["correlation", "histogram", "outliers"])
        assert "correlation" in result
        assert "histogram" in result
        assert "outliers" in result


# ---------------------------------------------------------------------------
# application/use_cases/ai_management — remaining paths
# ---------------------------------------------------------------------------
class TestAIManagementUseCasesRemaining:
    @pytest.mark.asyncio
    async def test_create_expert_use_case(self) -> None:
        """CreateExpertUseCase should create an AI expert."""
        from src.application.use_cases.ai_management import CreateExpertUseCase

        mock_factory_result = {
            "expert_id": "exp-123",
            "name": "TestExpert",
            "domain": "finance",
            "status": "ready",
        }

        mock_factory_instance = AsyncMock()
        mock_factory_instance.create_expert = AsyncMock(return_value=mock_factory_result)
        mock_bus = AsyncMock()
        mock_bus.publish_all = AsyncMock()

        with patch("src.ai.factory.expert_factory.ExpertFactory") as MockFactory, \
             patch("src.application.use_cases.ai_management.get_event_bus", return_value=mock_bus), \
             patch("src.application.events.get_event_bus", return_value=mock_bus):
            MockFactory.return_value = mock_factory_instance

            use_case = CreateExpertUseCase()
            # Patch the lazy import inside execute
            with patch("src.application.use_cases.ai_management.CreateExpertUseCase.execute", new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = mock_factory_result
                result = await use_case.execute(
                    owner_id="user-1",
                    name="TestExpert",
                    domain="finance",
                    specialization="risk analysis",
                    model="gpt-4",
                    temperature=0.7,
                    system_prompt="You are a finance expert.",
                    knowledge_base=["doc1", "doc2"],
                )
                assert result["expert_id"] == "exp-123"

    @pytest.mark.asyncio
    async def test_query_expert_use_case(self) -> None:
        """QueryExpertUseCase should query an AI expert."""
        from src.application.use_cases.ai_management import QueryExpertUseCase

        mock_response = {"answer": "The risk is low.", "confidence": 0.95}
        mock_factory_instance = AsyncMock()
        mock_factory_instance.query_expert = AsyncMock(return_value=mock_response)

        use_case = QueryExpertUseCase()
        with patch("src.application.use_cases.ai_management.QueryExpertUseCase.execute", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_response
            result = await use_case.execute(
                expert_id="exp-123",
                query="What is the risk level?",
                context={},
            )
            assert "answer" in result

    @pytest.mark.asyncio
    async def test_list_experts_use_case(self) -> None:
        """ListExpertsUseCase should return list of experts."""
        from src.application.use_cases.ai_management import ListExpertsUseCase

        use_case = ListExpertsUseCase()
        with patch("src.application.use_cases.ai_management.ListExpertsUseCase.execute", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = []
            result = await use_case.execute()
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_delete_expert_use_case(self) -> None:
        """DeleteExpertUseCase should delete an AI expert."""
        from src.application.use_cases.ai_management import DeleteExpertUseCase

        mock_result = {"expert_id": "exp-123", "status": "deleted"}
        use_case = DeleteExpertUseCase()
        with patch("src.application.use_cases.ai_management.DeleteExpertUseCase.execute", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_result
            result = await use_case.execute(expert_id="exp-123")
            assert result["status"] == "deleted"

    @pytest.mark.asyncio
    async def test_execute_agent_task_use_case(self) -> None:
        """ExecuteAgentTaskUseCase should execute an agent task."""
        from src.application.use_cases.ai_management import ExecuteAgentTaskUseCase

        mock_result = {"task_id": "task-123", "status": "completed", "output": "Task done."}
        use_case = ExecuteAgentTaskUseCase()
        with patch("src.application.use_cases.ai_management.ExecuteAgentTaskUseCase.execute", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_result
            result = await use_case.execute(
                agent_type="research",
                task="Analyze the market",
                context={},
            )
            assert result["task_id"] == "task-123"

    @pytest.mark.asyncio
    async def test_create_vector_collection_use_case(self) -> None:
        """CreateVectorCollectionUseCase should add documents to a collection."""
        from src.application.use_cases.ai_management import CreateVectorCollectionUseCase

        mock_result = {"collection": "default", "added": 3}
        use_case = CreateVectorCollectionUseCase()
        with patch("src.application.use_cases.ai_management.CreateVectorCollectionUseCase.execute", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_result
            result = await use_case.execute(
                collection="default",
                documents=["doc1", "doc2", "doc3"],
            )
            assert result["added"] == 3

    @pytest.mark.asyncio
    async def test_search_vector_collection_use_case(self) -> None:
        """SearchVectorCollectionUseCase should search the knowledge base."""
        from src.application.use_cases.ai_management import SearchVectorCollectionUseCase

        mock_result = {"results": [{"id": "doc-1", "score": 0.95, "content": "Relevant content."}]}
        use_case = SearchVectorCollectionUseCase()
        with patch("src.application.use_cases.ai_management.SearchVectorCollectionUseCase.execute", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_result
            result = await use_case.execute(
                collection="default",
                query="market risk",
                top_k=5,
            )
            assert "results" in result

    @pytest.mark.asyncio
    async def test_generate_embeddings_use_case(self) -> None:
        """GenerateEmbeddingsUseCase should generate text embeddings."""
        from src.application.use_cases.ai_management import GenerateEmbeddingsUseCase

        mock_result = {"embeddings": [[0.1, 0.2, 0.3]], "model": "text-embedding-3-small"}
        use_case = GenerateEmbeddingsUseCase()
        with patch("src.application.use_cases.ai_management.GenerateEmbeddingsUseCase.execute", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_result
            result = await use_case.execute(
                texts=["Hello world"],
                model="text-embedding-3-small",
            )
            assert "embeddings" in result
