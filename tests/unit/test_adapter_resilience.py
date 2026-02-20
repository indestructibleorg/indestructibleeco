"""Unit tests for inference adapter resilience layer (Step 22)."""
import asyncio
import os
import sys
import time

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.ai.engines.inference.resilience import (
    ResilientClient,
    AdapterCircuitBreaker,
    CircuitState,
)


class TestAdapterCircuitBreaker:
    def test_initial_state_closed(self):
        cb = AdapterCircuitBreaker("test")
        assert cb.state == CircuitState.CLOSED
        assert cb.allow_request() is True

    def test_opens_after_threshold(self):
        cb = AdapterCircuitBreaker("test", failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.allow_request() is False

    def test_half_open_after_recovery(self):
        cb = AdapterCircuitBreaker("test", failure_threshold=1, recovery_timeout=0.1)
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        time.sleep(0.15)
        assert cb.state == CircuitState.HALF_OPEN
        assert cb.allow_request() is True

    def test_success_resets(self):
        cb = AdapterCircuitBreaker("test", failure_threshold=2)
        cb.record_failure()
        cb.record_success()
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED  # reset by success

    def test_closed_after_half_open_success(self):
        cb = AdapterCircuitBreaker("test", failure_threshold=1, recovery_timeout=0.05)
        cb.record_failure()
        time.sleep(0.1)
        assert cb.state == CircuitState.HALF_OPEN
        cb.record_success()
        assert cb.state == CircuitState.CLOSED


class TestResilientClient:
    def test_creation(self):
        client = ResilientClient(name="test", endpoint="http://localhost:9999")
        assert client.name == "test"
        assert client.endpoint == "http://localhost:9999"
        assert client.circuit_state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_open_rejects(self):
        client = ResilientClient(
            name="test",
            endpoint="http://localhost:9999",
            circuit_failure_threshold=1,
        )
        # Force circuit open
        client._circuit.record_failure()
        assert client.circuit_state == CircuitState.OPEN
        with pytest.raises(ConnectionError, match="Circuit breaker OPEN"):
            await client.post("/test")

    @pytest.mark.asyncio
    async def test_connection_error_retries(self):
        client = ResilientClient(
            name="test",
            endpoint="http://localhost:1",  # unreachable
            max_retries=1,
            retry_base_delay=0.01,
            circuit_failure_threshold=5,
        )
        with pytest.raises(ConnectionError, match="all 2 attempts failed"):
            await client.get("/health")
        await client.close()

    @pytest.mark.asyncio
    async def test_close_pool(self):
        client = ResilientClient(name="test", endpoint="http://localhost:9999")
        await client.close()
        assert client._pool is None


class TestResilientClientIntegration:
    def test_multiple_clients_independent(self):
        c1 = ResilientClient(name="vllm", endpoint="http://vllm:8001")
        c2 = ResilientClient(name="tgi", endpoint="http://tgi:8002")
        c1._circuit.record_failure()
        c1._circuit.record_failure()
        c1._circuit.record_failure()
        assert c1.circuit_state == CircuitState.OPEN
        assert c2.circuit_state == CircuitState.CLOSED
