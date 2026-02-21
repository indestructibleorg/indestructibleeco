"""Engine Health Monitor — Periodic engine probing, circuit recovery, registry sync.

Runs as a background asyncio task during the application lifespan.
Periodically re-probes engines, recovers half-open circuits, syncs
model registry with engine availability, and cleans up stale worker jobs.

URI: indestructibleeco://backend/ai/services/health_monitor
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class HealthMonitorConfig:
    """Configuration for the health monitor."""

    def __init__(
        self,
        probe_interval: float = 30.0,
        stale_cleanup_interval: float = 300.0,
        registry_sync_interval: float = 60.0,
        max_consecutive_failures: int = 10,
        degraded_mode_threshold: int = 0,
    ) -> None:
        self.probe_interval = probe_interval
        self.stale_cleanup_interval = stale_cleanup_interval
        self.registry_sync_interval = registry_sync_interval
        self.max_consecutive_failures = max_consecutive_failures
        self.degraded_mode_threshold = degraded_mode_threshold


class EngineHealthMonitor:
    """Background health monitor for inference engines.

    Responsibilities:
        - Periodic engine health probing via EngineManager._probe_engine
        - Circuit breaker recovery: re-probe engines with OPEN circuits
          after recovery_timeout to transition to HALF_OPEN -> CLOSED
        - Registry sync: update ModelRegistry status based on engine availability
        - Worker cleanup: periodically remove stale completed/failed jobs
        - Degraded mode detection: track when all engines are unavailable

    Lifecycle:
        monitor = EngineHealthMonitor(config, engine_manager, registry, worker)
        await monitor.start()
        ...
        await monitor.stop()
    """

    def __init__(
        self,
        config: Optional[HealthMonitorConfig] = None,
        engine_manager: Any = None,
        model_registry: Any = None,
        inference_worker: Any = None,
    ) -> None:
        self._config = config or HealthMonitorConfig()
        self._engine_manager = engine_manager
        self._model_registry = model_registry
        self._inference_worker = inference_worker

        self._running = False
        self._tasks: List[asyncio.Task[None]] = []
        self._start_time: float = 0.0

        # Metrics
        self.total_probes: int = 0
        self.total_recoveries: int = 0
        self.total_registry_syncs: int = 0
        self.total_stale_cleanups: int = 0
        self.consecutive_all_down: int = 0
        self.is_degraded: bool = False
        self.last_probe_time: Optional[float] = None
        self.last_sync_time: Optional[float] = None

    @property
    def is_running(self) -> bool:
        return self._running

    async def start(self) -> None:
        """Start all background monitoring tasks."""
        if self._running:
            return

        self._running = True
        self._start_time = time.time()

        if self._engine_manager is not None:
            self._tasks.append(asyncio.create_task(self._probe_loop()))

        if self._model_registry is not None and self._engine_manager is not None:
            self._tasks.append(asyncio.create_task(self._registry_sync_loop()))

        if self._inference_worker is not None:
            self._tasks.append(asyncio.create_task(self._stale_cleanup_loop()))

        logger.info(
            "HealthMonitor: started %d background tasks (probe=%.0fs, sync=%.0fs, cleanup=%.0fs)",
            len(self._tasks),
            self._config.probe_interval,
            self._config.registry_sync_interval,
            self._config.stale_cleanup_interval,
        )

    async def stop(self) -> None:
        """Stop all background monitoring tasks."""
        if not self._running:
            return

        self._running = False
        for task in self._tasks:
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        logger.info(
            "HealthMonitor: stopped (probes=%d, recoveries=%d, syncs=%d)",
            self.total_probes,
            self.total_recoveries,
            self.total_registry_syncs,
        )

    async def probe_now(self) -> Dict[str, bool]:
        """Run an immediate probe of all engines. Returns {engine: available}."""
        self.total_probes += 1
        self.last_probe_time = time.time()

        if self._engine_manager is None:
            return {}

        results: Dict[str, bool] = {}
        for name in self._engine_manager._endpoints:
            try:
                await self._engine_manager._probe_engine(name)
                health = self._engine_manager._health.get(name)
                results[name] = health.is_available if health else False
            except Exception as exc:
                results[name] = False
                logger.debug("Probe %s failed: %s", name, exc)

        self._update_degraded_state(results)
        return results

    def get_stats(self) -> Dict[str, Any]:
        """Return health monitor statistics."""
        uptime = time.time() - self._start_time if self._start_time else 0
        return {
            "running": self._running,
            "uptime_seconds": round(uptime, 2),
            "total_probes": self.total_probes,
            "total_recoveries": self.total_recoveries,
            "total_registry_syncs": self.total_registry_syncs,
            "total_stale_cleanups": self.total_stale_cleanups,
            "consecutive_all_down": self.consecutive_all_down,
            "is_degraded": self.is_degraded,
            "last_probe_time": (
                datetime.fromtimestamp(self.last_probe_time, tz=timezone.utc).isoformat()
                if self.last_probe_time else None
            ),
            "last_sync_time": (
                datetime.fromtimestamp(self.last_sync_time, tz=timezone.utc).isoformat()
                if self.last_sync_time else None
            ),
            "config": {
                "probe_interval": self._config.probe_interval,
                "registry_sync_interval": self._config.registry_sync_interval,
                "stale_cleanup_interval": self._config.stale_cleanup_interval,
            },
        }

    # ── Background Loops ──────────────────────────────────────────────────────

    async def _probe_loop(self) -> None:
        """Periodically probe all engines and attempt circuit recovery."""
        await asyncio.sleep(self._config.probe_interval)
        while self._running:
            try:
                results = await self.probe_now()
                await self._attempt_circuit_recovery()

                available = sum(1 for v in results.values() if v)
                logger.info(
                    "HealthMonitor: probe complete — %d/%d engines available",
                    available,
                    len(results),
                )
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.warning("HealthMonitor: probe error: %s", exc)

            try:
                await asyncio.sleep(self._config.probe_interval)
            except asyncio.CancelledError:
                break

    async def _registry_sync_loop(self) -> None:
        """Periodically sync ModelRegistry with engine availability."""
        await asyncio.sleep(self._config.registry_sync_interval)
        while self._running:
            try:
                await self._sync_registry()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.warning("HealthMonitor: registry sync error: %s", exc)

            try:
                await asyncio.sleep(self._config.registry_sync_interval)
            except asyncio.CancelledError:
                break

    async def _stale_cleanup_loop(self) -> None:
        """Periodically clean up stale worker jobs."""
        await asyncio.sleep(self._config.stale_cleanup_interval)
        while self._running:
            try:
                if self._inference_worker is not None:
                    removed = await self._inference_worker.cleanup_stale()
                    if removed > 0:
                        self.total_stale_cleanups += removed
                        logger.info("HealthMonitor: cleaned %d stale jobs", removed)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.warning("HealthMonitor: stale cleanup error: %s", exc)

            try:
                await asyncio.sleep(self._config.stale_cleanup_interval)
            except asyncio.CancelledError:
                break

    # ── Internal ──────────────────────────────────────────────────────────────

    async def _attempt_circuit_recovery(self) -> None:
        """For engines with OPEN circuits, check if recovery timeout has elapsed
        and re-probe to transition HALF_OPEN -> CLOSED."""
        if self._engine_manager is None:
            return

        from .circuit_breaker import CircuitState

        for name, breaker in self._engine_manager._breakers.items():
            if breaker.state == CircuitState.HALF_OPEN:
                health = self._engine_manager._health.get(name)
                if health and health.is_available:
                    breaker.record_success()
                    self.total_recoveries += 1
                    logger.info(
                        "HealthMonitor: circuit %s recovered (HALF_OPEN -> CLOSED)",
                        name,
                    )

    async def _sync_registry(self) -> None:
        """Update ModelRegistry model status based on engine availability."""
        if self._model_registry is None or self._engine_manager is None:
            return

        from src.schemas.models import ModelStatus

        available_engines = set(self._engine_manager.list_available_engines())
        models = await self._model_registry.list_models()

        for model in models:
            has_available = bool(set(model.compatible_engines) & available_engines)

            if has_available and model.status not in (ModelStatus.READY, ModelStatus.LOADING):
                for eng in model.compatible_engines:
                    if eng in available_engines:
                        try:
                            await self._model_registry.update_status(
                                model.model_id, ModelStatus.READY, eng
                            )
                        except (KeyError, ValueError):
                            pass
                        break

            elif not has_available and model.status == ModelStatus.READY:
                try:
                    await self._model_registry.update_status(
                        model.model_id, ModelStatus.REGISTERED, None
                    )
                except (KeyError, ValueError):
                    pass

        self.total_registry_syncs += 1
        self.last_sync_time = time.time()

    def _update_degraded_state(self, results: Dict[str, bool]) -> None:
        """Track degraded mode when all engines are unavailable."""
        available = sum(1 for v in results.values() if v)

        if available <= self._config.degraded_mode_threshold:
            self.consecutive_all_down += 1
            if self.consecutive_all_down >= self._config.max_consecutive_failures and not self.is_degraded:
                self.is_degraded = True
                logger.error(
                    "HealthMonitor: DEGRADED MODE — all engines unavailable for %d consecutive probes",
                    self.consecutive_all_down,
                )
        else:
            if self.is_degraded:
                logger.info(
                    "HealthMonitor: recovered from degraded mode — %d engines available",
                    available,
                )
            self.consecutive_all_down = 0
            self.is_degraded = False