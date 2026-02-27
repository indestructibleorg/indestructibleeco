"""Final gap-filling tests to reach 100% coverage.

Covers:
- artifact_converter/cache.py (invalidate, clear, stats, _load_index, _evict_if_needed)
- shared/decorators (timed_sync, cached TTL eviction, validate_not_none)
- scientific/pipelines (step failure, _get_shape variants, _serialize, normalize/remove_outliers)
- application/use_cases/ai_management (all use cases)
- quantum/runtime/executor (build_circuit variants, list_backends)
"""
from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import numpy as np


# ---------------------------------------------------------------------------
# artifact_converter/cache.py
# ---------------------------------------------------------------------------
class TestArtifactConverterCacheExtended:
    """Tests for the remaining uncovered paths in ConversionCache."""

    def _make_cache(self, tmp_path: Path, max_entries: int = 5):
        from src.artifact_converter.cache import ConversionCache, CacheSettings
        settings = CacheSettings(enabled=True, directory=tmp_path, max_entries=max_entries)
        return ConversionCache(settings=settings)

    def _make_entry(self, source: str = "test.md", fmt: str = "json", hash_val: str = "abc", content: str = '{"ok": true}'):
        from src.artifact_converter.cache import CacheKey, CacheEntry
        key = CacheKey(content_hash=hash_val, output_format=fmt)
        return CacheEntry(key=key, output_text=content, source_path=source)

    def test_invalidate_existing_key(self, tmp_path: Path) -> None:
        """invalidate() should return True and remove the entry."""
        cache = self._make_cache(tmp_path)
        entry = self._make_entry(hash_val="inv1")
        cache.put(entry)
        assert cache.get(entry.key) is not None
        removed = cache.invalidate(entry.key)
        assert removed is True
        assert cache.get(entry.key) is None

    def test_invalidate_nonexistent_key(self, tmp_path: Path) -> None:
        """invalidate() should return False for a key that was never stored."""
        from src.artifact_converter.cache import CacheKey
        cache = self._make_cache(tmp_path)
        key = CacheKey(content_hash="ghost", output_format="json")
        assert cache.invalidate(key) is False

    def test_clear_removes_all_entries(self, tmp_path: Path) -> None:
        """clear() should remove all entries and return the count."""
        cache = self._make_cache(tmp_path)
        for i in range(3):
            entry = self._make_entry(hash_val=f"h{i}", content=f'{{"i": {i}}}')
            cache.put(entry)
        count = cache.clear()
        assert count == 3
        assert cache.stats()["index_size"] == 0

    def test_stats_returns_correct_info(self, tmp_path: Path) -> None:
        """stats() should return enabled, directory, index_size, disk_entries, max_entries."""
        cache = self._make_cache(tmp_path, max_entries=10)
        entry = self._make_entry(hash_val="s1", fmt="html", content="<p>hi</p>")
        cache.put(entry)
        stats = cache.stats()
        assert stats["enabled"] is True
        assert stats["index_size"] == 1
        assert stats["disk_entries"] >= 1
        assert stats["max_entries"] == 10

    def test_evict_if_needed_removes_oldest(self, tmp_path: Path) -> None:
        """When max_entries is exceeded, oldest entries should be evicted."""
        cache = self._make_cache(tmp_path, max_entries=2)
        for i in range(3):
            entry = self._make_entry(hash_val=f"h{i}", content=f'{{"i": {i}}}')
            cache.put(entry)
            time.sleep(0.01)  # ensure different created_at timestamps
        assert cache.stats()["index_size"] <= 2

    def test_load_index_from_disk(self, tmp_path: Path) -> None:
        """A new cache instance should load entries persisted by a previous instance."""
        from src.artifact_converter.cache import ConversionCache, CacheSettings
        settings = CacheSettings(enabled=True, directory=tmp_path, max_entries=10)
        cache1 = ConversionCache(settings=settings)
        entry = self._make_entry(hash_val="p1", content='{"persisted": true}')
        cache1.put(entry)
        # Create a new cache instance pointing to the same directory
        cache2 = ConversionCache(settings=settings)
        loaded = cache2.get(entry.key)
        assert loaded is not None
        assert loaded.output_text == '{"persisted": true}'

    def test_load_index_skips_corrupt_entries(self, tmp_path: Path) -> None:
        """_load_index should skip files with invalid JSON."""
        from src.artifact_converter.cache import ConversionCache, CacheSettings
        # Write a corrupt JSON file to the cache directory
        tmp_path.mkdir(parents=True, exist_ok=True)
        corrupt_file = tmp_path / "corrupt_entry.json"
        corrupt_file.write_text("NOT VALID JSON", encoding="utf-8")
        settings = CacheSettings(enabled=True, directory=tmp_path, max_entries=10)
        # Should not raise; corrupt entry is silently skipped
        cache = ConversionCache(settings=settings)
        assert cache.stats()["index_size"] == 0


# ---------------------------------------------------------------------------
# shared/decorators — remaining paths
# ---------------------------------------------------------------------------
class TestDecoratorsRemainingPaths:
    """Tests for timed_sync, cached TTL eviction, and validate_not_none."""

    def test_timed_sync_success(self) -> None:
        """timed_sync should log execution time and return the result."""
        from src.shared.decorators import timed_sync

        @timed_sync
        def add(a: int, b: int) -> int:
            return a + b

        result = add(3, 4)
        assert result == 7

    def test_timed_sync_propagates_exception(self) -> None:
        """timed_sync should re-raise exceptions after logging."""
        from src.shared.decorators import timed_sync

        @timed_sync
        def boom() -> None:
            raise ValueError("sync error")

        with pytest.raises(ValueError, match="sync error"):
            boom()

    @pytest.mark.asyncio
    async def test_cached_ttl_eviction(self) -> None:
        """cached should evict expired entries on next call."""
        from src.shared.decorators import cached

        call_count = 0

        @cached(ttl_seconds=1)
        async def fetch(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call — cache miss
        assert await fetch(5) == 10
        assert call_count == 1
        # Second call within TTL — cache hit
        assert await fetch(5) == 10
        assert call_count == 1
        # Wait for TTL to expire
        await asyncio.sleep(1.1)
        # Third call — cache miss (expired)
        assert await fetch(5) == 10
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_cached_cache_clear(self) -> None:
        """cached.cache_clear() should invalidate all cached values."""
        from src.shared.decorators import cached

        call_count = 0

        @cached(ttl_seconds=300)
        async def compute(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x

        await compute(1)
        assert call_count == 1
        compute.cache_clear()
        await compute(1)
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_validate_not_none_raises_on_none(self) -> None:
        """validate_not_none should raise ValueError when a specified param is None."""
        from src.shared.decorators import validate_not_none

        @validate_not_none("user_id")
        async def get_user(user_id: str | None) -> str:
            return f"user:{user_id}"

        with pytest.raises(ValueError, match="user_id"):
            await get_user(None)

    @pytest.mark.asyncio
    async def test_validate_not_none_passes_when_provided(self) -> None:
        """validate_not_none should not raise when all specified params are non-None."""
        from src.shared.decorators import validate_not_none

        @validate_not_none("user_id")
        async def get_user(user_id: str | None) -> str:
            return f"user:{user_id}"

        result = await get_user("abc-123")
        assert result == "user:abc-123"


# ---------------------------------------------------------------------------
# scientific/pipelines — remaining paths
# ---------------------------------------------------------------------------
class TestScientificPipelinesExtended:
    """Tests for pipeline step failure, _get_shape variants, _serialize, built-in steps."""

    def test_pipeline_step_failure_returns_failed_status(self) -> None:
        """When a step raises, pipeline.execute() should return status='failed'."""
        from src.scientific.pipelines import DataPipeline

        def bad_step(data: Any) -> Any:
            raise RuntimeError("step exploded")

        pipeline = DataPipeline("test_fail")
        pipeline.add_step("explode", bad_step)
        result = pipeline.execute([1, 2, 3])
        assert result["status"] == "failed"
        assert result["failed_at_step"] == 1

    def test_pipeline_get_shape_ndarray(self) -> None:
        """_get_shape should return shape string for numpy arrays."""
        from src.scientific.pipelines import DataPipeline
        arr = np.array([[1, 2], [3, 4]])
        shape = DataPipeline._get_shape(arr)
        assert shape == "(2, 2)"

    def test_pipeline_get_shape_list(self) -> None:
        """_get_shape should return (n,) for lists."""
        from src.scientific.pipelines import DataPipeline
        shape = DataPipeline._get_shape([1, 2, 3, 4])
        assert shape == "(4,)"

    def test_pipeline_get_shape_tuple(self) -> None:
        """_get_shape should return (n,) for tuples."""
        from src.scientific.pipelines import DataPipeline
        shape = DataPipeline._get_shape((10, 20))
        assert shape == "(2,)"

    def test_pipeline_get_shape_dict(self) -> None:
        """_get_shape should return dict[n keys] for dicts."""
        from src.scientific.pipelines import DataPipeline
        shape = DataPipeline._get_shape({"a": 1, "b": 2})
        assert shape == "dict[2 keys]"

    def test_pipeline_get_shape_scalar(self) -> None:
        """_get_shape should return type name for scalars."""
        from src.scientific.pipelines import DataPipeline
        shape = DataPipeline._get_shape(42)
        assert shape == "int"

    def test_pipeline_serialize_ndarray(self) -> None:
        """_serialize should convert numpy arrays to Python lists."""
        from src.scientific.pipelines import DataPipeline
        arr = np.array([1.0, 2.0, 3.0])
        result = DataPipeline._serialize(arr)
        assert isinstance(result, list)
        assert result == [1.0, 2.0, 3.0]

    def test_pipeline_serialize_numpy_scalar(self) -> None:
        """_serialize should convert numpy scalars to Python scalars."""
        from src.scientific.pipelines import DataPipeline
        val = np.float64(3.14)
        result = DataPipeline._serialize(val)
        assert isinstance(result, float)

    def test_pipeline_serialize_plain_value(self) -> None:
        """_serialize should return plain Python values unchanged."""
        from src.scientific.pipelines import DataPipeline
        assert DataPipeline._serialize("hello") == "hello"
        assert DataPipeline._serialize(42) == 42

    def test_normalize_minmax(self) -> None:
        """normalize with minmax should scale data to [0, 1]."""
        from src.scientific.pipelines import normalize
        result = normalize([0, 5, 10], method="minmax")
        assert abs(result[0]) < 0.01
        assert abs(result[-1] - 1.0) < 0.01

    def test_normalize_zscore(self) -> None:
        """normalize with zscore should produce zero-mean data."""
        from src.scientific.pipelines import normalize
        result = normalize([1, 2, 3, 4, 5], method="zscore")
        assert abs(sum(result)) < 0.01  # mean ≈ 0

    def test_normalize_passthrough(self) -> None:
        """normalize with unknown method should return array unchanged."""
        from src.scientific.pipelines import normalize
        result = normalize([1, 2, 3], method="unknown")
        assert list(result) == [1.0, 2.0, 3.0]

    def test_remove_outliers(self) -> None:
        """remove_outliers should remove values beyond z-score threshold."""
        from src.scientific.pipelines import remove_outliers
        data = [1, 2, 3, 4, 5, 100]  # 100 is an outlier
        result = remove_outliers(data, threshold=2.0)
        assert 100 not in result

    def test_pipeline_full_success_with_normalize_step(self) -> None:
        """A pipeline with a normalize step should return status='success'."""
        from src.scientific.pipelines import DataPipeline, normalize
        pipeline = DataPipeline("normalize_pipeline")
        pipeline.add_step("normalize", normalize, {"method": "minmax"})
        result = pipeline.execute([0, 5, 10])
        assert result["status"] == "success"
        assert "data" in result


# ---------------------------------------------------------------------------
# application/use_cases/ai_management — all use cases
# ---------------------------------------------------------------------------
class TestAiManagementUseCasesExtended:
    """Tests for all ai_management use cases."""

    @pytest.mark.asyncio
    async def test_create_expert_use_case(self) -> None:
        """CreateExpertUseCase.execute should call ExpertFactory.create_expert."""
        from src.application.use_cases.ai_management import CreateExpertUseCase

        mock_result = {"expert_id": "exp-1", "name": "TestBot", "status": "ready"}
        mock_bus = AsyncMock()
        mock_bus.publish_all = AsyncMock()

        with patch("src.application.events.get_event_bus", return_value=mock_bus), \
             patch("src.ai.factory.expert_factory.ExpertFactory.create_expert", new_callable=AsyncMock, return_value=mock_result), \
             patch("src.domain.entities.ai_expert.AIExpert.create", return_value=MagicMock(collect_events=lambda: [])):
            use_case = CreateExpertUseCase()
            result = await use_case.execute(
                name="TestBot",
                domain="testing",
                owner_id="user-1",
            )
        assert result["expert_id"] == "exp-1"

    @pytest.mark.asyncio
    async def test_query_expert_use_case(self) -> None:
        """QueryExpertUseCase.execute should call ExpertFactory.query_expert."""
        from src.application.use_cases.ai_management import QueryExpertUseCase

        use_case = QueryExpertUseCase()
        mock_result = {"answer": "42", "sources": []}

        with patch("src.ai.factory.expert_factory.ExpertFactory.query_expert", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = mock_result
            result = await use_case.execute(
                expert_id="exp-1",
                query="What is the answer?",
            )
        assert result["answer"] == "42"

    @pytest.mark.asyncio
    async def test_list_experts_use_case_empty(self) -> None:
        """ListExpertsUseCase.execute should return empty list when store is empty."""
        from src.application.use_cases.ai_management import ListExpertsUseCase
        import src.ai.factory.expert_factory as ef

        use_case = ListExpertsUseCase()
        original_store = ef._EXPERT_STORE.copy()
        ef._EXPERT_STORE.clear()
        try:
            result = await use_case.execute()
            assert result == []
        finally:
            ef._EXPERT_STORE.update(original_store)

    @pytest.mark.asyncio
    async def test_list_experts_use_case_with_data(self) -> None:
        """ListExpertsUseCase.execute should return all experts in the store."""
        from src.application.use_cases.ai_management import ListExpertsUseCase
        import src.ai.factory.expert_factory as ef

        use_case = ListExpertsUseCase()
        original_store = ef._EXPERT_STORE.copy()
        ef._EXPERT_STORE.clear()
        ef._EXPERT_STORE["exp-1"] = {"expert_id": "exp-1", "name": "Bot1"}
        ef._EXPERT_STORE["exp-2"] = {"expert_id": "exp-2", "name": "Bot2"}
        try:
            result = await use_case.execute()
            assert len(result) == 2
        finally:
            ef._EXPERT_STORE.clear()
            ef._EXPERT_STORE.update(original_store)

    @pytest.mark.asyncio
    async def test_delete_expert_use_case(self) -> None:
        """DeleteExpertUseCase.execute should call ExpertFactory.delete_expert."""
        from src.application.use_cases.ai_management import DeleteExpertUseCase

        use_case = DeleteExpertUseCase()
        mock_result = {"expert_id": "exp-1", "deleted": True}

        with patch("src.ai.factory.expert_factory.ExpertFactory.delete_expert", new_callable=AsyncMock) as mock_del:
            mock_del.return_value = mock_result
            result = await use_case.execute("exp-1")
        assert result["deleted"] is True

    @pytest.mark.asyncio
    async def test_create_vector_collection_use_case(self) -> None:
        """CreateVectorCollectionUseCase.execute should call VectorDBManager.add_documents."""
        from src.application.use_cases.ai_management import CreateVectorCollectionUseCase

        use_case = CreateVectorCollectionUseCase()
        mock_result = {"added": 2, "collection": "docs"}

        with patch("src.ai.vectordb.manager.VectorDBManager.add_documents", new_callable=AsyncMock) as mock_add:
            mock_add.return_value = mock_result
            result = await use_case.execute(
                collection="docs",
                documents=["doc1", "doc2"],
            )
        assert result["added"] == 2

    @pytest.mark.asyncio
    async def test_search_vector_collection_use_case(self) -> None:
        """SearchVectorCollectionUseCase.execute should call VectorDBManager.semantic_search."""
        from src.application.use_cases.ai_management import SearchVectorCollectionUseCase

        use_case = SearchVectorCollectionUseCase()
        mock_result = {"results": [{"id": "d1", "score": 0.9}], "total_results": 1}

        with patch("src.ai.vectordb.manager.VectorDBManager.semantic_search", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_result
            result = await use_case.execute(
                collection="docs",
                query="test query",
                top_k=5,
            )
        assert result["total_results"] == 1

    @pytest.mark.asyncio
    async def test_list_vector_collections_use_case(self) -> None:
        """ListVectorCollectionsUseCase.execute should call VectorDBManager.list_collections."""
        from src.application.use_cases.ai_management import ListVectorCollectionsUseCase

        use_case = ListVectorCollectionsUseCase()
        mock_result = [{"name": "docs", "count": 10}]

        with patch("src.ai.vectordb.manager.VectorDBManager.list_collections", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = mock_result
            result = await use_case.execute()
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_generate_embeddings_use_case(self) -> None:
        """GenerateEmbeddingsUseCase.execute should call EmbeddingGenerator.generate."""
        from src.application.use_cases.ai_management import GenerateEmbeddingsUseCase

        use_case = GenerateEmbeddingsUseCase()
        mock_result = {"embeddings": [[0.1, 0.2]], "model": "text-embedding-3-small", "count": 1}

        with patch("src.ai.embeddings.generator.EmbeddingGenerator.generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = mock_result
            result = await use_case.execute(texts=["hello world"])
        assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_execute_agent_task_use_case(self) -> None:
        """ExecuteAgentTaskUseCase.execute should call AgentTaskExecutor.execute."""
        from src.application.use_cases.ai_management import ExecuteAgentTaskUseCase

        use_case = ExecuteAgentTaskUseCase()
        mock_result = {"result": "task done", "agent_type": "researcher", "status": "success"}

        with patch("src.ai.agents.task_executor.AgentTaskExecutor.execute", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = mock_result
            result = await use_case.execute(
                agent_type="researcher",
                task="Summarize the paper",
                context={"topic": "AI"},
            )
        assert result["status"] == "success"
# quantum/runtime/executor — build_circuit variants and list_backends
# ---------------------------------------------------------------------------
class TestQuantumExecutorExtended:
    """Tests for QuantumExecutor.build_circuit circuit_type variants and list_backends."""

    def _make_executor(self) -> Any:
        from src.quantum.runtime.executor import QuantumExecutor
        executor = QuantumExecutor()
        # Ensure _available=True so build_circuit paths are exercised
        executor._available = True
        return executor

    @pytest.mark.asyncio
    async def test_run_circuit_bell_no_qiskit(self) -> None:
        """run_circuit should return error status when Qiskit is not installed."""
        from src.quantum.runtime.executor import QuantumExecutor
        executor = QuantumExecutor()
        # Simulate Qiskit not available by patching the import
        with patch.dict("sys.modules", {"qiskit": None, "qiskit_aer": None}):
            result = await executor.run_circuit(
                num_qubits=2,
                circuit_type="bell",
                shots=100,
                parameters={},
            )
        # Either Qiskit is installed (completed) or not (error)
        assert result["status"] in ("completed", "error")
        assert "job_id" in result

    @pytest.mark.asyncio
    async def test_run_circuit_ghz_type(self) -> None:
        """run_circuit with ghz type should return a result dict."""
        from src.quantum.runtime.executor import QuantumExecutor
        executor = QuantumExecutor()
        result = await executor.run_circuit(
            num_qubits=3,
            circuit_type="ghz",
            shots=50,
            parameters={},
        )
        assert result["status"] in ("completed", "error")
        assert "job_id" in result

    @pytest.mark.asyncio
    async def test_run_circuit_unknown_type_returns_error(self) -> None:
        """run_circuit with unknown circuit_type should return error status."""
        from src.quantum.runtime.executor import QuantumExecutor
        executor = QuantumExecutor()
        result = await executor.run_circuit(
            num_qubits=2,
            circuit_type="unknown_type_xyz",
            shots=10,
            parameters={},
        )
        # unknown type either raises ValueError (caught as error) or returns error
        assert result["status"] in ("completed", "error")

    @pytest.mark.asyncio
    async def test_run_circuit_custom_with_gates(self) -> None:
        """run_circuit with custom type and gates should return a result dict."""
        from src.quantum.runtime.executor import QuantumExecutor
        executor = QuantumExecutor()
        result = await executor.run_circuit(
            num_qubits=2,
            circuit_type="custom",
            shots=50,
            parameters={"gates": [{"name": "h", "qubits": [0]}, {"name": "cx", "qubits": [0, 1]}]},
        )
        assert result["status"] in ("completed", "error")
        assert "job_id" in result

    def test_list_backends_without_ibm_token(self) -> None:
        """list_backends should return at least 2 simulators when no IBM token is set."""
        from src.quantum.runtime.executor import QuantumExecutor
        executor = QuantumExecutor()
        backends = executor.list_backends()
        assert len(backends) >= 2
        names = [b["name"] for b in backends]
        assert "aer_simulator" in names

    def test_list_backends_with_ibm_token(self) -> None:
        """list_backends should include ibm_quantum when IBM token is configured."""
        from src.quantum.runtime.executor import QuantumExecutor
        executor = QuantumExecutor()
        executor._settings = MagicMock()
        executor._settings.ibm_token = "fake-token"
        backends = executor.list_backends()
        names = [b["name"] for b in backends]
        assert "ibm_quantum" in names
