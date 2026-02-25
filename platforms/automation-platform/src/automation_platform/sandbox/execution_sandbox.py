"""SandboxedExecutor — wraps task execution inside a ProcessSandbox from the shared kernel.

Creates a sandbox per task, injects env vars, enforces resource limits and timeout,
and returns an ExecutionResult.
"""

from __future__ import annotations

import shlex
from typing import Any

from platform_shared.sandbox import (
    ExecutionResult,
    ProcessSandbox,
    SandboxConfig,
    SandboxRuntime,
)
from platform_shared.sandbox.resource import ResourceLimits

from automation_platform.domain.entities import Task
from automation_platform.domain.value_objects import ExecutionMode, TaskStatus


# Default resource limits per execution mode
_MODE_LIMITS: dict[ExecutionMode, ResourceLimits] = {
    ExecutionMode.INSTANT: ResourceLimits(cpu_cores=0.5, memory_mb=128, max_processes=8),
    ExecutionMode.FAST: ResourceLimits(cpu_cores=1.0, memory_mb=256, max_processes=16),
    ExecutionMode.STANDARD: ResourceLimits(cpu_cores=2.0, memory_mb=512, max_processes=32),
    ExecutionMode.BACKGROUND: ResourceLimits(cpu_cores=4.0, memory_mb=1024, max_processes=64),
}

# Timeout per mode (seconds)
_MODE_TIMEOUTS: dict[ExecutionMode, float] = {
    ExecutionMode.INSTANT: 1.0,
    ExecutionMode.FAST: 5.0,
    ExecutionMode.STANDARD: 30.0,
    ExecutionMode.BACKGROUND: 300.0,
}


class SandboxedExecutor:
    """Executes tasks inside isolated ProcessSandbox instances from the shared kernel.

    Each task gets its own sandbox with mode-appropriate resource limits,
    environment variables, and a timeout. The sandbox is destroyed after execution.
    """

    def __init__(
        self,
        sandbox_runtime: SandboxRuntime | None = None,
        env_vars: dict[str, str] | None = None,
    ) -> None:
        self._runtime: SandboxRuntime = sandbox_runtime or ProcessSandbox()
        self._base_env: dict[str, str] = env_vars or {}
        self._execution_count: int = 0

    @property
    def runtime(self) -> SandboxRuntime:
        return self._runtime

    @property
    def execution_count(self) -> int:
        return self._execution_count

    async def execute_task(self, task: Task) -> ExecutionResult:
        """Run a task's command inside a fresh sandbox.

        Steps:
          1. Build a SandboxConfig with mode-appropriate limits
          2. Create the sandbox
          3. Execute the command
          4. Update the task entity with results
          5. Destroy the sandbox
          6. Return the raw ExecutionResult
        """
        mode = task.mode
        resource_limits = _MODE_LIMITS.get(mode, _MODE_LIMITS[ExecutionMode.STANDARD])
        timeout = _MODE_TIMEOUTS.get(mode, _MODE_TIMEOUTS[ExecutionMode.STANDARD])

        env_vars = {
            **self._base_env,
            "TASK_ID": task.id,
            "EXECUTION_MODE": mode.value,
        }

        config = SandboxConfig(
            name=f"task-{task.id}",
            resource_limits=resource_limits,
            timeout_seconds=timeout,
            env_vars=env_vars,
        )

        sandbox_id = await self._runtime.create(config)
        try:
            # Parse the command string into a list for subprocess execution
            command = shlex.split(task.command) if task.command else ["echo", "no-command"]

            task.mark_running()
            result: ExecutionResult = await self._runtime.execute(sandbox_id, command)
            self._execution_count += 1

            if result.success:
                task.mark_completed({
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "exit_code": result.exit_code,
                    "duration_seconds": result.duration_seconds,
                })
            elif result.timed_out:
                task.mark_timed_out()
            else:
                task.mark_failed(
                    f"Command exited with code {result.exit_code}: {result.stderr}"
                )

            return result
        finally:
            await self._runtime.destroy(sandbox_id)

    async def execute_many(self, tasks: list[Task]) -> list[ExecutionResult]:
        """Execute multiple tasks sequentially, each in its own sandbox."""
        results: list[ExecutionResult] = []
        for task in tasks:
            try:
                result = await self.execute_task(task)
                results.append(result)
            except Exception:
                # Task already marked failed in execute_task; create a placeholder result
                results.append(
                    ExecutionResult(
                        sandbox_id="error",
                        exit_code=-1,
                        stdout="",
                        stderr=str(task.error or "Unknown error"),
                        duration_seconds=0.0,
                    )
                )
        return results

    def stats(self) -> dict[str, Any]:
        return {
            "execution_count": self._execution_count,
            "runtime_type": type(self._runtime).__name__,
        }
