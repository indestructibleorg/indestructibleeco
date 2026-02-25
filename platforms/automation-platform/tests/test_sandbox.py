"""Tests for the sandbox layer — SandboxedExecutor using ProcessSandbox from _shared."""

from __future__ import annotations

import sys
from typing import Any

import pytest

from platform_shared.sandbox import (
    ExecutionResult,
    ProcessSandbox,
    SandboxConfig,
    SandboxRuntime,
    SandboxStatus,
)

from automation_platform.domain.entities import Task
from automation_platform.domain.value_objects import ExecutionMode, TaskStatus
from automation_platform.sandbox.execution_sandbox import SandboxedExecutor


# =============================================================================
# SandboxedExecutor with real ProcessSandbox
# =============================================================================


class TestSandboxedExecutorWithProcessSandbox:
    """Tests that run real subprocess commands inside ProcessSandbox."""

    @pytest.mark.asyncio
    async def test_execute_echo_command(self) -> None:
        sandbox = ProcessSandbox()
        executor = SandboxedExecutor(sandbox_runtime=sandbox)
        task = Task(command="echo hello-from-sandbox", mode=ExecutionMode.STANDARD)

        result = await executor.execute_task(task)

        assert result.success is True
        assert result.exit_code == 0
        assert "hello-from-sandbox" in result.stdout
        assert task.status == TaskStatus.COMPLETED
        assert executor.execution_count == 1

    @pytest.mark.asyncio
    async def test_execute_python_command(self) -> None:
        sandbox = ProcessSandbox()
        executor = SandboxedExecutor(sandbox_runtime=sandbox)
        task = Task(
            command=f"{sys.executable} -c \"print('automation')\"",
            mode=ExecutionMode.FAST,
        )

        result = await executor.execute_task(task)

        assert result.success is True
        assert "automation" in result.stdout

    @pytest.mark.asyncio
    async def test_failed_command(self) -> None:
        sandbox = ProcessSandbox()
        executor = SandboxedExecutor(sandbox_runtime=sandbox)
        task = Task(
            command=f"{sys.executable} -c \"import sys; sys.exit(1)\"",
            mode=ExecutionMode.STANDARD,
        )

        result = await executor.execute_task(task)

        assert result.exit_code == 1
        assert task.status == TaskStatus.FAILED

    @pytest.mark.asyncio
    async def test_env_vars_injected(self) -> None:
        sandbox = ProcessSandbox()
        executor = SandboxedExecutor(
            sandbox_runtime=sandbox,
            env_vars={"CUSTOM_VAR": "test_value"},
        )
        task = Task(
            command=f"{sys.executable} -c \"import os; print(os.environ.get('CUSTOM_VAR', ''))\"",
            mode=ExecutionMode.STANDARD,
        )

        result = await executor.execute_task(task)

        assert result.success is True
        assert "test_value" in result.stdout

    @pytest.mark.asyncio
    async def test_task_id_in_env(self) -> None:
        sandbox = ProcessSandbox()
        executor = SandboxedExecutor(sandbox_runtime=sandbox)
        task = Task(
            command=f"{sys.executable} -c \"import os; print(os.environ.get('TASK_ID', ''))\"",
            mode=ExecutionMode.STANDARD,
        )

        result = await executor.execute_task(task)

        assert result.success is True
        assert task.id in result.stdout

    @pytest.mark.asyncio
    async def test_execution_mode_in_env(self) -> None:
        sandbox = ProcessSandbox()
        executor = SandboxedExecutor(sandbox_runtime=sandbox)
        task = Task(
            command=(
                f"{sys.executable} -c "
                "\"import os; print(os.environ.get('EXECUTION_MODE', ''))\""
            ),
            mode=ExecutionMode.FAST,
        )

        result = await executor.execute_task(task)

        assert result.success is True
        assert "fast" in result.stdout

    @pytest.mark.asyncio
    async def test_sandbox_destroyed_after_execution(self) -> None:
        sandbox = ProcessSandbox()
        executor = SandboxedExecutor(sandbox_runtime=sandbox)
        task = Task(command="echo cleanup-test", mode=ExecutionMode.STANDARD)

        await executor.execute_task(task)

        # After execution, sandbox should have been destroyed (no lingering sandboxes)
        remaining = await sandbox.list_sandboxes()
        assert len(remaining) == 0

    @pytest.mark.asyncio
    async def test_execute_many(self) -> None:
        sandbox = ProcessSandbox()
        executor = SandboxedExecutor(sandbox_runtime=sandbox)
        tasks = [
            Task(command="echo task-0", mode=ExecutionMode.STANDARD),
            Task(command="echo task-1", mode=ExecutionMode.STANDARD),
            Task(command="echo task-2", mode=ExecutionMode.STANDARD),
        ]

        results = await executor.execute_many(tasks)

        assert len(results) == 3
        assert all(r.success for r in results)
        assert executor.execution_count == 3

    @pytest.mark.asyncio
    async def test_stats(self) -> None:
        sandbox = ProcessSandbox()
        executor = SandboxedExecutor(sandbox_runtime=sandbox)

        stats = executor.stats()
        assert stats["execution_count"] == 0
        assert stats["runtime_type"] == "ProcessSandbox"

        await executor.execute_task(Task(command="echo stats", mode=ExecutionMode.STANDARD))
        stats = executor.stats()
        assert stats["execution_count"] == 1


# =============================================================================
# SandboxedExecutor with mock runtime (unit-level)
# =============================================================================


class _MockSandboxRuntime(SandboxRuntime):
    """Minimal mock for testing SandboxedExecutor logic without subprocess."""

    def __init__(self) -> None:
        self._sandboxes: dict[str, SandboxStatus] = {}
        self.created: list[SandboxConfig] = []
        self.destroyed: list[str] = []
        self._counter = 0

    async def create(self, config: SandboxConfig) -> str:
        self._counter += 1
        sid = f"mock-sb-{self._counter}"
        self._sandboxes[sid] = SandboxStatus.READY
        self.created.append(config)
        return sid

    async def execute(self, sandbox_id: str, command: list[str]) -> ExecutionResult:
        return ExecutionResult(
            sandbox_id=sandbox_id,
            exit_code=0,
            stdout=f"mock: {' '.join(command)}",
            stderr="",
            duration_seconds=0.001,
        )

    async def get_status(self, sandbox_id: str) -> SandboxStatus:
        return self._sandboxes.get(sandbox_id, SandboxStatus.DESTROYED)

    async def destroy(self, sandbox_id: str) -> None:
        self._sandboxes.pop(sandbox_id, None)
        self.destroyed.append(sandbox_id)

    async def list_sandboxes(self) -> dict[str, SandboxStatus]:
        return dict(self._sandboxes)


class TestSandboxedExecutorMocked:
    @pytest.mark.asyncio
    async def test_creates_and_destroys_sandbox(self) -> None:
        mock_rt = _MockSandboxRuntime()
        executor = SandboxedExecutor(sandbox_runtime=mock_rt)
        task = Task(command="echo test", mode=ExecutionMode.INSTANT)

        await executor.execute_task(task)

        assert len(mock_rt.created) == 1
        assert len(mock_rt.destroyed) == 1
        assert mock_rt.created[0].name == f"task-{task.id}"

    @pytest.mark.asyncio
    async def test_resource_limits_per_mode(self) -> None:
        mock_rt = _MockSandboxRuntime()
        executor = SandboxedExecutor(sandbox_runtime=mock_rt)

        # INSTANT mode
        await executor.execute_task(Task(command="echo a", mode=ExecutionMode.INSTANT))
        instant_config = mock_rt.created[0]
        assert instant_config.resource_limits.memory_mb == 128

        # BACKGROUND mode
        await executor.execute_task(Task(command="echo b", mode=ExecutionMode.BACKGROUND))
        bg_config = mock_rt.created[1]
        assert bg_config.resource_limits.memory_mb == 1024

    @pytest.mark.asyncio
    async def test_env_vars_injected_into_config(self) -> None:
        mock_rt = _MockSandboxRuntime()
        executor = SandboxedExecutor(
            sandbox_runtime=mock_rt,
            env_vars={"APP_NAME": "automation"},
        )
        task = Task(command="echo env", mode=ExecutionMode.STANDARD)

        await executor.execute_task(task)

        config = mock_rt.created[0]
        assert config.env_vars["APP_NAME"] == "automation"
        assert config.env_vars["TASK_ID"] == task.id
        assert config.env_vars["EXECUTION_MODE"] == "standard"

    @pytest.mark.asyncio
    async def test_task_marked_completed_on_success(self) -> None:
        mock_rt = _MockSandboxRuntime()
        executor = SandboxedExecutor(sandbox_runtime=mock_rt)
        task = Task(command="echo ok", mode=ExecutionMode.FAST)

        await executor.execute_task(task)

        assert task.status == TaskStatus.COMPLETED
        assert "stdout" in task.result
