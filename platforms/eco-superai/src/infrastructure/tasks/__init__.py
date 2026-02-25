"""Background task infrastructure — async task runner and scheduling."""
from __future__ import annotations

import asyncio
from typing import Any, Callable, Coroutine

import structlog

logger = structlog.get_logger(__name__)

TaskFunc = Callable[..., Coroutine[Any, Any, Any]]


class TaskRunner:
    """Simple async background task runner."""

    def __init__(self) -> None:
        self._tasks: dict[str, asyncio.Task] = {}

    def submit(self, name: str, coro: Coroutine) -> None:
        if name in self._tasks and not self._tasks[name].done():
            logger.warning("task_already_running", name=name)
            return
        task = asyncio.create_task(self._run_with_logging(name, coro))
        self._tasks[name] = task
        logger.info("task_submitted", name=name)

    async def _run_with_logging(self, name: str, coro: Coroutine) -> Any:
        try:
            result = await coro
            logger.info("task_completed", name=name)
            return result
        except asyncio.CancelledError:
            logger.info("task_cancelled", name=name)
            raise
        except Exception as e:
            logger.error("task_failed", name=name, error=str(e))
            raise

    def cancel(self, name: str) -> bool:
        task = self._tasks.get(name)
        if task and not task.done():
            task.cancel()
            return True
        return False

    def cancel_all(self) -> int:
        count = 0
        for name, task in self._tasks.items():
            if not task.done():
                task.cancel()
                count += 1
        return count

    def get_status(self, name: str) -> str:
        task = self._tasks.get(name)
        if task is None:
            return "unknown"
        if task.done():
            return "failed" if task.exception() else "completed"
        if task.cancelled():
            return "cancelled"
        return "running"

    def list_tasks(self) -> list[dict[str, str]]:
        return [{"name": name, "status": self.get_status(name)} for name in self._tasks]


# Singleton
_runner: TaskRunner | None = None


def get_task_runner() -> TaskRunner:
    global _runner
    if _runner is None:
        _runner = TaskRunner()
    return _runner


__all__ = ["TaskRunner", "get_task_runner"]