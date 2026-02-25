"""Tests for DataSandbox — isolated data processing environment."""

import pytest

from data_platform.sandbox.data_sandbox import DataSandbox
from platform_shared.sandbox.runtime import ProcessSandbox, SandboxConfig, SandboxStatus
from platform_shared.sandbox.resource import ResourceLimits


class TestDataSandboxInit:
    def test_default_config(self):
        sandbox = DataSandbox()
        assert sandbox._memory_mb == 256
        assert sandbox._timeout_seconds == 30.0
        assert sandbox._max_processes == 4

    def test_custom_config(self):
        sandbox = DataSandbox(memory_mb=512, timeout_seconds=60.0, max_processes=8)
        assert sandbox._memory_mb == 512
        assert sandbox._timeout_seconds == 60.0
        assert sandbox._max_processes == 8


class TestDataSandboxLifecycle:
    @pytest.mark.asyncio
    async def test_initialize_creates_sandbox(self):
        sandbox = DataSandbox()
        await sandbox.initialize()
        assert sandbox._sandbox_id is not None
        status = await sandbox.get_status()
        assert status == "ready"
        await sandbox.destroy()

    @pytest.mark.asyncio
    async def test_destroy_cleans_up(self):
        sandbox = DataSandbox()
        await sandbox.initialize()
        assert sandbox._sandbox_id is not None
        await sandbox.destroy()
        assert sandbox._sandbox_id is None

    @pytest.mark.asyncio
    async def test_status_not_initialized(self):
        sandbox = DataSandbox()
        status = await sandbox.get_status()
        assert status == "not_initialized"

    @pytest.mark.asyncio
    async def test_double_destroy_safe(self):
        sandbox = DataSandbox()
        await sandbox.initialize()
        await sandbox.destroy()
        # Second destroy should not raise
        await sandbox.destroy()


class TestDataSandboxExecution:
    @pytest.mark.asyncio
    async def test_execute_simple_transform(self):
        sandbox = DataSandbox(timeout_seconds=10.0)
        try:
            result = await sandbox.execute_transform(
                data=[{"x": 1}, {"x": 2}, {"x": 3}],
                transform_code="result = [r['x'] * 2 for r in data]",
            )
            assert result["success"] is True
            assert result["result"] == [2, 4, 6]
        finally:
            await sandbox.destroy()

    @pytest.mark.asyncio
    async def test_execute_filter_transform(self):
        sandbox = DataSandbox(timeout_seconds=10.0)
        try:
            result = await sandbox.execute_transform(
                data=[{"name": "Alice", "age": 30}, {"name": "Bob", "age": 17}],
                transform_code="result = [r for r in data if r['age'] >= 18]",
            )
            assert result["success"] is True
            assert len(result["result"]) == 1
            assert result["result"][0]["name"] == "Alice"
        finally:
            await sandbox.destroy()

    @pytest.mark.asyncio
    async def test_execute_aggregation(self):
        sandbox = DataSandbox(timeout_seconds=10.0)
        try:
            result = await sandbox.execute_transform(
                data=[{"val": 10}, {"val": 20}, {"val": 30}],
                transform_code="result = sum(r['val'] for r in data)",
            )
            assert result["success"] is True
            assert result["result"] == 60
        finally:
            await sandbox.destroy()

    @pytest.mark.asyncio
    async def test_execute_with_error(self):
        sandbox = DataSandbox(timeout_seconds=10.0)
        try:
            result = await sandbox.execute_transform(
                data=[{"x": 1}],
                transform_code="result = 1 / 0",
            )
            assert result["success"] is False
            assert "error" in result or "exit_code" in result
        finally:
            await sandbox.destroy()

    @pytest.mark.asyncio
    async def test_execute_auto_initializes(self):
        sandbox = DataSandbox(timeout_seconds=10.0)
        assert sandbox._sandbox_id is None
        try:
            result = await sandbox.execute_transform(
                data=[{"x": 1}],
                transform_code="result = data",
            )
            assert sandbox._sandbox_id is not None
            assert result["success"] is True
        finally:
            await sandbox.destroy()

    @pytest.mark.asyncio
    async def test_execute_empty_data(self):
        sandbox = DataSandbox(timeout_seconds=10.0)
        try:
            result = await sandbox.execute_transform(
                data=[],
                transform_code="result = len(data)",
            )
            assert result["success"] is True
            assert result["result"] == 0
        finally:
            await sandbox.destroy()

    @pytest.mark.asyncio
    async def test_duration_reported(self):
        sandbox = DataSandbox(timeout_seconds=10.0)
        try:
            result = await sandbox.execute_transform(
                data=[{"x": 1}],
                transform_code="result = data",
            )
            assert "duration_seconds" in result
            assert result["duration_seconds"] >= 0
        finally:
            await sandbox.destroy()


class TestDataSandboxIsolation:
    @pytest.mark.asyncio
    async def test_uses_process_sandbox(self):
        sandbox = DataSandbox()
        assert isinstance(sandbox._sandbox, ProcessSandbox)

    @pytest.mark.asyncio
    async def test_resource_limits_passed(self):
        sandbox = DataSandbox(memory_mb=128, max_processes=2)
        await sandbox.initialize()
        try:
            # The sandbox should be created with our limits
            sid = sandbox._sandbox_id
            assert sid is not None
            state = sandbox._sandbox._sandboxes[sid]
            assert state.config.resource_limits.memory_mb == 128
            assert state.config.resource_limits.max_processes == 2
        finally:
            await sandbox.destroy()
