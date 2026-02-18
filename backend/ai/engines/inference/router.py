"""Inference Router - Multi-engine dispatch with load balancing.

Routes inference requests to the optimal engine based on model registry,
engine health, current load, and request characteristics. Implements
failover, retry logic, and request queuing.
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, AsyncIterator

from .base import (
    EngineStatus, InferenceRequest, InferenceResponse, StreamChunk,
)
from .registry import ModelRegistry, ModelEntry

logger = logging.getLogger(__name__)


class InferenceRouter:
    """Routes inference requests across multiple engine backends.

    Routing strategy:
    1. Resolve model ID to candidate entries via registry
    2. Filter by health status (exclude unhealthy)
    3. Select by priority, then round-robin within same priority
    4. Execute with timeout and retry on failure
    5. Failover to next candidate on error
    """

    def __init__(
        self,
        registry: ModelRegistry,
        max_retries: int = 2,
        timeout_seconds: float = 120.0,
    ) -> None:
        self._registry = registry
        self._max_retries = max_retries
        self._timeout = timeout_seconds
        self._health_cache: dict[str, tuple[EngineStatus, float]] = {}
        self._round_robin_idx: dict[str, int] = {}
        self._request_count = 0
        self._error_count = 0

    async def route(self, request: InferenceRequest) -> InferenceResponse:
        """Route a non-streaming inference request.

        Args:
            request: Unified inference request.

        Returns:
            InferenceResponse from the selected engine.

        Raises:
            RuntimeError: If no healthy engine is available.
        """
        entries = self._get_candidates(request.model, "chat")
        if not entries:
            raise RuntimeError(f"No engine available for model: {request.model}")

        last_error: Exception | None = None
        for attempt in range(self._max_retries + 1):
            entry = self._select_entry(request.model, entries)
            try:
                self._request_count += 1
                logger.debug(
                    "Routing %s to %s (attempt %d/%d)",
                    request.model, entry.engine_type.value, attempt + 1, self._max_retries + 1,
                )
                response = await asyncio.wait_for(
                    entry.adapter.generate(request),
                    timeout=self._timeout,
                )
                response.engine = entry.engine_type.value
                return response
            except Exception as e:
                last_error = e
                self._error_count += 1
                self._mark_unhealthy(entry)
                logger.warning(
                    "Engine %s failed for %s (attempt %d): %s",
                    entry.engine_type.value, request.model, attempt + 1, e,
                )
                entries = [e for e in entries if e is not entry]
                if not entries:
                    break

        raise RuntimeError(
            f"All engines failed for model {request.model} after {self._max_retries + 1} attempts: {last_error}"
        )

    async def route_stream(self, request: InferenceRequest) -> AsyncIterator[StreamChunk]:
        """Route a streaming inference request.

        Args:
            request: Unified inference request with stream=True.

        Yields:
            StreamChunk objects from the selected engine.
        """
        entries = self._get_candidates(request.model, "chat")
        if not entries:
            raise RuntimeError(f"No engine available for model: {request.model}")

        entry = self._select_entry(request.model, entries)
        self._request_count += 1

        try:
            async for chunk in entry.adapter.stream(request):
                yield chunk
        except Exception as e:
            self._error_count += 1
            self._mark_unhealthy(entry)
            raise RuntimeError(f"Stream failed on {entry.engine_type.value}: {e}") from e

    async def health_check_all(self) -> dict[str, Any]:
        """Run health checks on all registered adapters."""
        adapters = self._registry.get_all_adapters()
        results = {}

        checks = {name: adapter.health_check() for name, adapter in adapters.items()}
        done = await asyncio.gather(*checks.values(), return_exceptions=True)

        for (name, _), result in zip(checks.items(), done):
            if isinstance(result, Exception):
                results[name] = {"status": "unhealthy", "error": str(result)}
                self._health_cache[name] = (EngineStatus.UNHEALTHY, time.time())
            else:
                results[name] = {
                    "status": result.status.value,
                    "endpoint": result.endpoint,
                    "models": result.models_loaded,
                    "uptime": result.uptime_seconds,
                }
                self._health_cache[name] = (result.status, time.time())

        return results

    def get_stats(self) -> dict[str, Any]:
        """Return router statistics."""
        return {
            "total_requests": self._request_count,
            "total_errors": self._error_count,
            "error_rate": round(self._error_count / max(self._request_count, 1), 4),
            "registered_models": self._registry.model_count,
            "registered_adapters": self._registry.adapter_count,
            "health_cache_size": len(self._health_cache),
        }

    def _get_candidates(self, model_id: str, capability: str) -> list[ModelEntry]:
        """Get healthy candidate entries for a model."""
        all_entries = self._registry.resolve_all(model_id)
        if not all_entries:
            entry = self._registry.resolve(model_id, capability)
            return [entry] if entry else []

        healthy = []
        for entry in all_entries:
            adapter_key = f"{entry.engine_type.value}:{entry.adapter.endpoint}"
            cached = self._health_cache.get(adapter_key)
            if cached and cached[0] == EngineStatus.UNHEALTHY:
                if time.time() - cached[1] < 30:
                    continue
            if capability in entry.capabilities:
                healthy.append(entry)

        return healthy if healthy else all_entries[:1]

    def _select_entry(self, model_id: str, entries: list[ModelEntry]) -> ModelEntry:
        """Select an entry using priority + round-robin."""
        if len(entries) == 1:
            return entries[0]

        max_priority = max(e.priority for e in entries)
        top_entries = [e for e in entries if e.priority == max_priority]

        idx = self._round_robin_idx.get(model_id, 0) % len(top_entries)
        self._round_robin_idx[model_id] = idx + 1
        return top_entries[idx]

    def _mark_unhealthy(self, entry: ModelEntry) -> None:
        """Mark an engine as temporarily unhealthy."""
        key = f"{entry.engine_type.value}:{entry.adapter.endpoint}"
        self._health_cache[key] = (EngineStatus.UNHEALTHY, time.time())