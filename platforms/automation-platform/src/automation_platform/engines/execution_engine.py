"""InstantExecutionEngine — async, multi-mode task execution with SLA budgets.

Selects execution mode based on estimated complexity, respects SLA ceilings:
  INSTANT  < 100ms
  FAST     < 500ms
  STANDARD < 5s
  BACKGROUND — no strict SLA
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Callable, Awaitable

from platform_shared.protocols.engine import Engine, EngineStatus

from automation_platform.domain.entities import Task
from automation_platform.domain.events import TaskCompleted, TaskDispatched
from automation_platform.domain.exceptions import TaskTimeoutError
from automation_platform.domain.value_objects import ExecutionMode, StageBudget, TaskStatus


# SLA ceilings per mode (in seconds)
_SLA_CEILINGS: dict[ExecutionMode, float] = {
    ExecutionMode.INSTANT: 0.1,
    ExecutionMode.FAST: 0.5,
    ExecutionMode.STANDARD: 5.0,
    ExecutionMode.BACKGROUND: 300.0,
}


def _estimate_mode(task: Task) -> ExecutionMode:
    """Heuristic: pick execution mode based on input data size and command complexity."""
    data_size = len(str(task.input_data))
    cmd_len = len(task.command)

    if data_size < 100 and cmd_len < 20:
        return ExecutionMode.INSTANT
    if data_size < 1_000 and cmd_len < 100:
        return ExecutionMode.FAST
    if data_size < 50_000:
        return ExecutionMode.STANDARD
    return ExecutionMode.BACKGROUND


# Type alias for the handler that actually runs the task
TaskHandler = Callable[[Task], Awaitable[dict[str, Any]]]


async def _default_handler(task: Task) -> dict[str, Any]:
    """Default handler — simulates work with a trivial async sleep."""
    await asyncio.sleep(0)
    return {"output": f"Executed: {task.command}", "input_keys": list(task.input_data.keys())}


class InstantExecutionEngine:
    """Async execution engine that selects mode based on task complexity and enforces SLA budgets.

    Satisfies the shared-kernel ``Engine`` protocol.
    """

    def __init__(
        self,
        handler: TaskHandler | None = None,
        max_concurrent: int = 50,
    ) -> None:
        self._handler = handler or _default_handler
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._status: EngineStatus = EngineStatus.IDLE
        self._tasks_run: int = 0
        self._tasks_failed: int = 0
        self._events: list[Any] = []

    # -- Engine protocol -------------------------------------------------------

    @property
    def name(self) -> str:
        return "InstantExecutionEngine"

    @property
    def status(self) -> EngineStatus:
        return self._status

    async def start(self) -> None:
        self._status = EngineStatus.RUNNING

    async def stop(self) -> None:
        self._status = EngineStatus.STOPPED

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Engine-protocol compatible entry: wraps payload into a Task and runs it."""
        task = Task(
            command=payload.get("command", ""),
            input_data=payload.get("input_data", {}),
            mode=ExecutionMode(payload["mode"]) if "mode" in payload else ExecutionMode.STANDARD,
        )
        result_task = await self.execute_task(task)
        return {
            "task_id": result_task.id,
            "status": result_task.status.value,
            "result": result_task.result,
            "duration": result_task.duration_seconds,
            "mode": result_task.mode.value,
        }

    # -- Core API --------------------------------------------------------------

    async def execute_task(self, task: Task) -> Task:
        """Execute a single task, selecting mode if not explicitly set, enforcing SLA."""
        if task.mode == ExecutionMode.STANDARD and task.command:
            # Auto-select a more specific mode
            task.mode = _estimate_mode(task)

        sla = _SLA_CEILINGS[task.mode]

        async with self._semaphore:
            task.mark_running()
            self._status = EngineStatus.RUNNING

            self._events.append(
                TaskDispatched(
                    task_id=task.id,
                    command=task.command,
                    agent_id="engine",
                    mode=task.mode.value,
                )
            )

            start = time.monotonic()
            try:
                result = await asyncio.wait_for(self._handler(task), timeout=sla)
                elapsed = time.monotonic() - start
                task.mark_completed(result)
                self._tasks_run += 1

                self._events.append(
                    TaskCompleted(
                        task_id=task.id,
                        success=True,
                        duration_seconds=elapsed,
                        result=result,
                    )
                )
            except asyncio.TimeoutError:
                elapsed = time.monotonic() - start
                task.mark_timed_out()
                self._tasks_failed += 1
                self._events.append(
                    TaskCompleted(
                        task_id=task.id,
                        success=False,
                        duration_seconds=elapsed,
                    )
                )
                raise TaskTimeoutError(task.id, sla)
            except Exception as exc:
                elapsed = time.monotonic() - start
                task.mark_failed(str(exc))
                self._tasks_failed += 1
                self._events.append(
                    TaskCompleted(
                        task_id=task.id,
                        success=False,
                        duration_seconds=elapsed,
                    )
                )
                raise

        return task

    # -- Observability ---------------------------------------------------------

    @property
    def events(self) -> list[Any]:
        return list(self._events)

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "tasks_run": self._tasks_run,
            "tasks_failed": self._tasks_failed,
            "status": self._status.value,
        }
