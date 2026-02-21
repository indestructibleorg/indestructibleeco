"""Unit tests for EngineHealthMonitor."""
import pytest
import asyncio
from unittest.mock import AsyncMock, Mock

from backend.ai.src.services.health_monitor import (
    EngineHealthMonitor,
    HealthMonitorConfig,
)
from src.schemas.models import ModelStatus, ModelInfo


@pytest.fixture
def config():
    return HealthMonitorConfig(
        probe_interval=0.1,
        stale_cleanup_interval=0.1,
        registry_sync_interval=0.1,
        max_consecutive_failures=3,
        degraded_mode_threshold=0,
    )


@pytest.fixture
def monitor(config):
    return EngineHealthMonitor(config=config)


class TestHealthMonitorConfig:
    def test_defaults(self):
        cfg = HealthMonitorConfig()
        assert cfg.probe_interval == 30.0
        assert cfg.stale_cleanup_interval == 300.0
        assert cfg.registry_sync_interval == 60.0
        assert cfg.max_consecutive_failures == 10
        assert cfg.degraded_mode_threshold == 0

    def test_custom(self):
        cfg = HealthMonitorConfig(probe_interval=5.0, max_consecutive_failures=5)
        assert cfg.probe_interval == 5.0
        assert cfg.max_consecutive_failures == 5


class TestEngineHealthMonitor:
    @pytest.mark.asyncio
    async def test_start_stop_no_deps(self, monitor):
        await monitor.start()
        assert monitor.is_running is True
        assert len(monitor._tasks) == 0  # no deps = no tasks
        await monitor.stop()
        assert monitor.is_running is False

    @pytest.mark.asyncio
    async def test_start_idempotent(self, monitor):
        await monitor.start()
        await monitor.start()
        assert monitor.is_running is True
        await monitor.stop()

    @pytest.mark.asyncio
    async def test_stop_idempotent(self, monitor):
        await monitor.start()
        await monitor.stop()
        await monitor.stop()
        assert monitor.is_running is False

    @pytest.mark.asyncio
    async def test_probe_now_no_engine(self, monitor):
        results = await monitor.probe_now()
        assert results == {}
        assert monitor.total_probes == 1

    @pytest.mark.asyncio
    async def test_stats(self, monitor):
        stats = monitor.get_stats()
        assert stats["running"] is False
        assert stats["total_probes"] == 0
        assert stats["total_recoveries"] == 0
        assert stats["is_degraded"] is False
        assert "config" in stats
        assert stats["config"]["probe_interval"] == 0.1

    @pytest.mark.asyncio
    async def test_stats_after_start(self, config):
        mon = EngineHealthMonitor(config=config)
        await mon.start()
        stats = mon.get_stats()
        assert stats["running"] is True
        assert stats["uptime_seconds"] >= 0
        await mon.stop()

    @pytest.mark.asyncio
    async def test_degraded_mode_detection(self, config):
        config.max_consecutive_failures = 2
        mon = EngineHealthMonitor(config=config)

        mon._update_degraded_state({"vllm": False, "tgi": False})
        assert mon.consecutive_all_down == 1
        assert mon.is_degraded is False

        mon._update_degraded_state({"vllm": False, "tgi": False})
        assert mon.consecutive_all_down == 2
        assert mon.is_degraded is True

    @pytest.mark.asyncio
    async def test_degraded_mode_recovery(self, config):
        config.max_consecutive_failures = 1
        mon = EngineHealthMonitor(config=config)

        mon._update_degraded_state({"vllm": False})
        assert mon.is_degraded is True

        mon._update_degraded_state({"vllm": True})
        assert mon.is_degraded is False
        assert mon.consecutive_all_down == 0

    @pytest.mark.asyncio
    async def test_with_engine_manager(self, config):
        from backend.ai.src.services.engine_manager import EngineManager

        mgr = EngineManager(
            endpoints={"test-engine": "http://localhost:19999"},
            failure_threshold=3,
            recovery_timeout=0.1,
        )
        mon = EngineHealthMonitor(config=config, engine_manager=mgr)
        await mon.start()
        assert mon.is_running is True
        assert len(mon._tasks) == 1  # probe loop only

        results = await mon.probe_now()
        assert "test-engine" in results
        assert mon.total_probes == 1

        await mon.stop()

    @pytest.mark.asyncio
    async def test_with_worker(self, config):
        from backend.ai.src.services.worker import InferenceWorker

        worker = InferenceWorker(engine_manager=None, max_queue_size=10, stale_timeout=0.0)
        await worker.start(concurrency=1)

        mon = EngineHealthMonitor(config=config, inference_worker=worker)
        await mon.start()
        assert len(mon._tasks) == 1  # stale cleanup loop only
        await mon.stop()
        await worker.shutdown()

    @pytest.mark.asyncio
    async def test_with_all_deps(self, config):
        from backend.ai.src.services.engine_manager import EngineManager
        from backend.ai.src.services.worker import InferenceWorker
        from src.core.registry import ModelRegistry

        mgr = EngineManager(
            endpoints={"test": "http://localhost:19999"},
            failure_threshold=3,
            recovery_timeout=0.1,
        )
        registry = ModelRegistry()
        worker = InferenceWorker(engine_manager=None, max_queue_size=10, stale_timeout=0.0)
        await worker.start(concurrency=1)

        mon = EngineHealthMonitor(
            config=config,
            engine_manager=mgr,
            model_registry=registry,
            inference_worker=worker,
        )
        await mon.start()
        assert len(mon._tasks) == 3  # probe + registry sync + stale cleanup

        stats = mon.get_stats()
        assert stats["running"] is True

        await mon.stop()
        await worker.shutdown()

    @pytest.mark.asyncio
    async def test_probe_loop_runs(self, config):
        from backend.ai.src.services.engine_manager import EngineManager

        mgr = EngineManager(
            endpoints={"test": "http://localhost:19999"},
            failure_threshold=3,
            recovery_timeout=0.1,
        )
        config.probe_interval = 0.05
        mon = EngineHealthMonitor(config=config, engine_manager=mgr)
        await mon.start()

        await asyncio.sleep(0.2)

        assert mon.total_probes >= 1
        await mon.stop()


class TestSyncRegistry:
    """Tests for EngineHealthMonitor._sync_registry method."""

    @pytest.mark.asyncio
    async def test_downgrade_ready_to_registered_no_engines(self, config):
        """Test READY->REGISTERED downgrade when no engines are available."""
        # Create mock registry
        mock_registry = Mock()
        mock_model = ModelInfo(
            model_id="test-model",
            compatible_engines=["vllm", "tgi"],
            status=ModelStatus.READY,
        )
        mock_registry.list_models = AsyncMock(return_value=[mock_model])
        mock_registry.update_status = AsyncMock()

        # Create mock engine manager with NO available engines
        mock_engine_mgr = Mock()
        mock_engine_mgr.list_available_engines = Mock(return_value=[])

        # Create monitor with mocked dependencies
        mon = EngineHealthMonitor(
            config=config,
            engine_manager=mock_engine_mgr,
            model_registry=mock_registry,
        )

        # Call _sync_registry
        await mon._sync_registry()

        # Assert update_status was called exactly once with correct parameters
        mock_registry.update_status.assert_called_once_with(
            "test-model", ModelStatus.REGISTERED, None
        )
        assert mon.total_registry_syncs == 1

    @pytest.mark.asyncio
    async def test_no_downgrade_when_model_not_ready(self, config):
        """Test that models not in READY status are not downgraded."""
        mock_registry = Mock()
        mock_model = ModelInfo(
            model_id="test-model",
            compatible_engines=["vllm"],
            status=ModelStatus.REGISTERED,  # Not READY
        )
        mock_registry.list_models = AsyncMock(return_value=[mock_model])
        mock_registry.update_status = AsyncMock()

        mock_engine_mgr = Mock()
        mock_engine_mgr.list_available_engines = Mock(return_value=[])

        mon = EngineHealthMonitor(
            config=config,
            engine_manager=mock_engine_mgr,
            model_registry=mock_registry,
        )

        await mon._sync_registry()

        # update_status should NOT be called for non-READY models
        mock_registry.update_status.assert_not_called()

    @pytest.mark.asyncio
    async def test_downgrade_handles_keyerror(self, config):
        """Test that KeyError during downgrade is handled gracefully."""
        mock_registry = Mock()
        mock_model = ModelInfo(
            model_id="test-model",
            compatible_engines=["vllm"],
            status=ModelStatus.READY,
        )
        mock_registry.list_models = AsyncMock(return_value=[mock_model])
        # Simulate KeyError when updating status
        mock_registry.update_status = AsyncMock(side_effect=KeyError("Model not found"))

        mock_engine_mgr = Mock()
        mock_engine_mgr.list_available_engines = Mock(return_value=[])

        mon = EngineHealthMonitor(
            config=config,
            engine_manager=mock_engine_mgr,
            model_registry=mock_registry,
        )

        # Should not raise exception - error is caught and logged
        await mon._sync_registry()

        # Verify update_status was called (even though it raised)
        mock_registry.update_status.assert_called_once()
        assert mon.total_registry_syncs == 1

    @pytest.mark.asyncio
    async def test_downgrade_handles_valueerror(self, config):
        """Test that ValueError during downgrade is handled gracefully."""
        mock_registry = Mock()
        mock_model = ModelInfo(
            model_id="test-model",
            compatible_engines=["vllm"],
            status=ModelStatus.READY,
        )
        mock_registry.list_models = AsyncMock(return_value=[mock_model])
        # Simulate ValueError when updating status
        mock_registry.update_status = AsyncMock(
            side_effect=ValueError("Invalid status transition")
        )

        mock_engine_mgr = Mock()
        mock_engine_mgr.list_available_engines = Mock(return_value=[])

        mon = EngineHealthMonitor(
            config=config,
            engine_manager=mock_engine_mgr,
            model_registry=mock_registry,
        )

        # Should not raise exception - error is caught and logged
        await mon._sync_registry()

        # Verify update_status was called (even though it raised)
        mock_registry.update_status.assert_called_once()
        assert mon.total_registry_syncs == 1

    @pytest.mark.asyncio
    async def test_upgrade_registered_to_ready_with_available_engine(self, config):
        """Test REGISTERED->READY upgrade when engines become available."""
        mock_registry = Mock()
        mock_model = ModelInfo(
            model_id="test-model",
            compatible_engines=["vllm", "tgi"],
            status=ModelStatus.REGISTERED,
        )
        mock_registry.list_models = AsyncMock(return_value=[mock_model])
        mock_registry.update_status = AsyncMock()

        mock_engine_mgr = Mock()
        mock_engine_mgr.list_available_engines = Mock(return_value=["vllm"])

        mon = EngineHealthMonitor(
            config=config,
            engine_manager=mock_engine_mgr,
            model_registry=mock_registry,
        )

        await mon._sync_registry()

        # Should upgrade to READY with the first available compatible engine
        mock_registry.update_status.assert_called_once_with(
            "test-model", ModelStatus.READY, "vllm"
        )

    @pytest.mark.asyncio
    async def test_no_change_when_ready_and_engines_available(self, config):
        """Test that READY models with available engines are not updated."""
        mock_registry = Mock()
        mock_model = ModelInfo(
            model_id="test-model",
            compatible_engines=["vllm"],
            status=ModelStatus.READY,
        )
        mock_registry.list_models = AsyncMock(return_value=[mock_model])
        mock_registry.update_status = AsyncMock()

        mock_engine_mgr = Mock()
        mock_engine_mgr.list_available_engines = Mock(return_value=["vllm"])

        mon = EngineHealthMonitor(
            config=config,
            engine_manager=mock_engine_mgr,
            model_registry=mock_registry,
        )

        await mon._sync_registry()

        # No update needed - model is already READY and engines are available
        mock_registry.update_status.assert_not_called()

    @pytest.mark.asyncio
    async def test_upgrade_breaks_after_first_available_engine(self, config):
        """Test that upgrade only calls update_status once with first compatible engine."""
        mock_registry = Mock()
        mock_model = ModelInfo(
            model_id="test-model",
            compatible_engines=["vllm", "tgi", "sglang"],
            status=ModelStatus.REGISTERED,
        )
        mock_registry.list_models = AsyncMock(return_value=[mock_model])
        mock_registry.update_status = AsyncMock()

        mock_engine_mgr = Mock()
        # All compatible engines are available
        mock_engine_mgr.list_available_engines = Mock(
            return_value=["vllm", "tgi", "sglang"]
        )

        mon = EngineHealthMonitor(
            config=config,
            engine_manager=mock_engine_mgr,
            model_registry=mock_registry,
        )

        await mon._sync_registry()

        # Should only be called once with the first available compatible engine
        assert mock_registry.update_status.call_count == 1
        # The first compatible engine is 'vllm'
        mock_registry.update_status.assert_called_once_with(
            "test-model", ModelStatus.READY, "vllm"
        )