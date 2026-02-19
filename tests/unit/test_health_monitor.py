"""Unit tests for EngineHealthMonitor."""
import pytest
import asyncio

from backend.ai.src.services.health_monitor import (
    EngineHealthMonitor,
    HealthMonitorConfig,
)


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