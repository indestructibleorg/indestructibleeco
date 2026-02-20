"""Inference Adapter Resilience Layer.

URI: indestructibleeco://backend/ai/engines/inference/resilience

Provides connection pooling, circuit breaking, and retry with exponential
backoff for all inference engine adapters. Adapters import and use
ResilientClient instead of creating raw httpx.AsyncClient per request.
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)

# Default retry configuration
DEFAULT_MAX_RETRIES = 2
DEFAULT_RETRY_BASE_DELAY = 0.5
DEFAULT_RETRY_MAX_DELAY = 8.0
DEFAULT_RETRY_MULTIPLIER = 2.0


class CircuitState:
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class AdapterCircuitBreaker:
    """Lightweight per-adapter circuit breaker."""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        recovery_timeout: float = 30.0,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = 0.0

    @property
    def state(self) -> str:
        if self._state == CircuitState.OPEN:
            if time.monotonic() - self._last_failure_time >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
        return self._state

    def allow_request(self) -> bool:
        s = self.state
        return s in (CircuitState.CLOSED, CircuitState.HALF_OPEN)

    def record_success(self) -> None:
        self._failure_count = 0
        self._state = CircuitState.CLOSED

    def record_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = time.monotonic()
        if self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN
            logger.warning("Circuit OPEN for %s after %d failures", self.name, self._failure_count)


class ResilientClient:
    """HTTP client with connection pooling, circuit breaker, and retry.

    Usage in adapters:
        self._client = ResilientClient(name="vllm", endpoint="http://localhost:8001")
        response = await self._client.post("/v1/chat/completions", json=payload)
    """

    def __init__(
        self,
        name: str,
        endpoint: str,
        timeout: float = 120.0,
        max_connections: int = 20,
        max_keepalive: int = 10,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_base_delay: float = DEFAULT_RETRY_BASE_DELAY,
        circuit_failure_threshold: int = 3,
        circuit_recovery_timeout: float = 30.0,
    ) -> None:
        self.name = name
        self.endpoint = endpoint.rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay
        self._circuit = AdapterCircuitBreaker(
            name=name,
            failure_threshold=circuit_failure_threshold,
            recovery_timeout=circuit_recovery_timeout,
        )
        self._pool: Optional[httpx.AsyncClient] = None
        self._max_connections = max_connections
        self._max_keepalive = max_keepalive

    async def _get_pool(self) -> httpx.AsyncClient:
        if self._pool is None:
            limits = httpx.Limits(
                max_connections=self._max_connections,
                max_keepalive_connections=self._max_keepalive,
            )
            self._pool = httpx.AsyncClient(
                base_url=self.endpoint,
                limits=limits,
                timeout=httpx.Timeout(self._timeout, connect=5.0),
            )
        return self._pool

    async def close(self) -> None:
        if self._pool:
            await self._pool.aclose()
            self._pool = None

    @property
    def circuit_state(self) -> str:
        return self._circuit.state

    async def request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Execute HTTP request with circuit breaker + retry."""
        if not self._circuit.allow_request():
            raise ConnectionError(
                f"Circuit breaker OPEN for {self.name}: requests rejected"
            )

        last_exc: Optional[Exception] = None
        for attempt in range(self._max_retries + 1):
            try:
                pool = await self._get_pool()
                response = await pool.request(method, path, **kwargs)

                # 4xx errors: fail fast, no retry
                if 400 <= response.status_code < 500:
                    self._circuit.record_success()
                    return response

                # 5xx errors: retry
                if response.status_code >= 500:
                    last_exc = httpx.HTTPStatusError(
                        f"Server error {response.status_code}",
                        request=response.request,
                        response=response,
                    )
                    if attempt < self._max_retries:
                        delay = self._retry_base_delay * (DEFAULT_RETRY_MULTIPLIER ** attempt)
                        delay = min(delay, DEFAULT_RETRY_MAX_DELAY)
                        logger.warning(
                            "%s: attempt %d/%d got %d, retrying in %.1fs",
                            self.name, attempt + 1, self._max_retries + 1,
                            response.status_code, delay,
                        )
                        await asyncio.sleep(delay)
                        continue

                self._circuit.record_success()
                return response

            except (httpx.ConnectError, httpx.TimeoutException, ConnectionError, OSError) as exc:
                last_exc = exc
                if attempt < self._max_retries:
                    delay = self._retry_base_delay * (DEFAULT_RETRY_MULTIPLIER ** attempt)
                    delay = min(delay, DEFAULT_RETRY_MAX_DELAY)
                    logger.warning(
                        "%s: attempt %d/%d failed (%s), retrying in %.1fs",
                        self.name, attempt + 1, self._max_retries + 1,
                        type(exc).__name__, delay,
                    )
                    await asyncio.sleep(delay)
                    continue

        self._circuit.record_failure()
        raise ConnectionError(
            f"{self.name}: all {self._max_retries + 1} attempts failed: {last_exc}"
        ) from last_exc

    async def post(self, path: str, **kwargs: Any) -> httpx.Response:
        return await self.request("POST", path, **kwargs)

    async def get(self, path: str, **kwargs: Any) -> httpx.Response:
        return await self.request("GET", path, **kwargs)
