"""Task execution engine for the Governance Operations Platform.

Provides priority-ordered, concurrent async task execution with retry logic,
timeout support, and configurable parallelism via ``asyncio.Semaphore``.

@GL-governed
@GL-layer: GL30-49
@GL-semantic: governance-execution
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from enum import StrEnum
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Enums & data models
# ---------------------------------------------------------------------------


class TaskStatus(StrEnum):
    """Lifecycle status of a single task."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


class TaskPriority(StrEnum):
    """Priority levels that determine queue ordering.

    Lower numeric weight means higher execution priority.
    """

    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"

    @property
    def weight(self) -> int:
        """Numeric weight for sorting (lower = higher priority)."""
        _weights = {"critical": 0, "high": 1, "normal": 2, "low": 3}
        return _weights[self.value]


class ExecutorConfig(BaseModel):
    """Configuration for the TaskExecutor.

    Attributes:
        max_concurrency: Maximum number of tasks running in parallel.
        default_timeout_seconds: Per-task timeout if not overridden.
        max_retries: Default retry count for failed tasks.
        retry_backoff_seconds: Base delay between retries (exponential backoff).
    """

    max_concurrency: int = Field(default=5, ge=1, le=100)
    default_timeout_seconds: float = Field(default=60.0, gt=0)
    max_retries: int = Field(default=3, ge=0)
    retry_backoff_seconds: float = Field(default=1.0, ge=0)


@dataclass
class TaskResult:
    """Outcome of executing a single task.

    Attributes:
        task_id: Unique identifier of the task.
        status: Terminal status after execution.
        output: Arbitrary output payload produced by the task callable.
        duration_seconds: Wall-clock execution time in seconds.
        error: Error message when the task failed or timed out.
        attempts: Number of attempts made (including retries).
        completed_at: UTC timestamp of completion.
    """

    task_id: str
    status: TaskStatus
    output: Any = None
    duration_seconds: float = 0.0
    error: str = ""
    attempts: int = 0
    completed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(order=True)
class _QueueEntry:
    """Internal priority-queue wrapper so that ``asyncio.PriorityQueue``
    can order tasks by priority weight, then by submission order."""

    priority_weight: int
    sequence: int
    task: _TaskSpec = field(compare=False)


@dataclass
class _TaskSpec:
    """Internal specification for a submitted task."""

    task_id: str
    name: str
    fn: Callable[..., Awaitable[Any]]
    args: tuple[Any, ...]
    kwargs: dict[str, Any]
    priority: TaskPriority
    timeout_seconds: float | None
    max_retries: int


# ---------------------------------------------------------------------------
# TaskExecutor
# ---------------------------------------------------------------------------


class TaskExecutor:
    """Async task execution engine with retry logic and concurrency control.

    Usage::

        executor = TaskExecutor(ExecutorConfig(max_concurrency=3))
        task_id = await executor.submit("scan-modules", scan_fn, priority=TaskPriority.HIGH)
        results = await executor.run_all()

    Tasks are executed concurrently up to ``max_concurrency``.  Failed tasks
    are retried with exponential back-off.  Each task is individually guarded
    by a timeout.
    """

    def __init__(self, config: ExecutorConfig | None = None) -> None:
        self._config = config or ExecutorConfig()
        self._semaphore = asyncio.Semaphore(self._config.max_concurrency)
        self._queue: asyncio.PriorityQueue[_QueueEntry] = asyncio.PriorityQueue()
        self._sequence: int = 0
        self._results: dict[str, TaskResult] = {}
        self._running: dict[str, asyncio.Task[TaskResult]] = {}
        self._cancelled: bool = False
        logger.info(
            "task_executor_init",
            max_concurrency=self._config.max_concurrency,
            default_timeout=self._config.default_timeout_seconds,
            max_retries=self._config.max_retries,
        )

    # -- submission ---------------------------------------------------------

    async def submit(
        self,
        name: str,
        fn: Callable[..., Awaitable[Any]],
        *args: Any,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout_seconds: float | None = None,
        max_retries: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Submit a task for execution.

        Args:
            name: Human-readable task name (for logging).
            fn: Async callable to execute.
            *args: Positional arguments forwarded to *fn*.
            priority: Execution priority (default ``NORMAL``).
            timeout_seconds: Per-task timeout override; falls back to config default.
            max_retries: Retry override; falls back to config default.
            **kwargs: Keyword arguments forwarded to *fn*.

        Returns:
            The unique ``task_id`` assigned to the submitted task.
        """
        task_id = str(uuid.uuid4())
        spec = _TaskSpec(
            task_id=task_id,
            name=name,
            fn=fn,
            args=args,
            kwargs=kwargs,
            priority=priority,
            timeout_seconds=timeout_seconds or self._config.default_timeout_seconds,
            max_retries=max_retries if max_retries is not None else self._config.max_retries,
        )
        self._sequence += 1
        entry = _QueueEntry(
            priority_weight=priority.weight,
            sequence=self._sequence,
            task=spec,
        )
        await self._queue.put(entry)
        logger.info(
            "task_submitted",
            task_id=task_id,
            name=name,
            priority=priority.value,
        )
        return task_id

    # -- execution ----------------------------------------------------------

    async def run_all(self) -> list[TaskResult]:
        """Drain the queue and execute all submitted tasks concurrently.

        Returns a list of :class:`TaskResult` in completion order.
        """
        self._cancelled = False
        tasks: list[asyncio.Task[TaskResult]] = []

        while not self._queue.empty():
            entry = await self._queue.get()
            coro = self._execute_with_semaphore(entry.task)
            t = asyncio.create_task(coro, name=f"task-{entry.task.name}")
            self._running[entry.task.task_id] = t
            tasks.append(t)

        results = await asyncio.gather(*tasks, return_exceptions=False)
        self._running.clear()

        logger.info(
            "executor_run_complete",
            total=len(results),
            succeeded=sum(1 for r in results if r.status == TaskStatus.COMPLETED),
            failed=sum(1 for r in results if r.status == TaskStatus.FAILED),
        )
        return list(results)

    async def run_one(self, task_id: str) -> TaskResult | None:
        """Execute a single task by ID (if still in the queue).

        Returns the result or ``None`` if the task was not found.
        """
        pending: list[_QueueEntry] = []
        target: _TaskSpec | None = None

        while not self._queue.empty():
            entry = await self._queue.get()
            if entry.task.task_id == task_id:
                target = entry.task
            else:
                pending.append(entry)

        for entry in pending:
            await self._queue.put(entry)

        if target is None:
            return None

        return await self._execute_with_semaphore(target)

    # -- cancellation -------------------------------------------------------

    async def cancel_all(self) -> int:
        """Cancel all running tasks.

        Returns the number of tasks that were cancelled.
        """
        self._cancelled = True
        cancelled_count = 0
        for task_id, task in list(self._running.items()):
            if not task.done():
                task.cancel()
                cancelled_count += 1
                logger.warning("task_cancelled", task_id=task_id)
        return cancelled_count

    # -- internal -----------------------------------------------------------

    async def _execute_with_semaphore(self, spec: _TaskSpec) -> TaskResult:
        """Acquire the semaphore, then execute with retries."""
        async with self._semaphore:
            return await self._execute_with_retries(spec)

    async def _execute_with_retries(self, spec: _TaskSpec) -> TaskResult:
        """Execute a task, retrying on failure up to ``spec.max_retries``."""
        last_error = ""
        attempts = 0

        for attempt in range(1, spec.max_retries + 2):  # +2: 1 initial + retries
            if self._cancelled:
                result = TaskResult(
                    task_id=spec.task_id,
                    status=TaskStatus.CANCELLED,
                    error="Executor was cancelled",
                    attempts=attempts,
                )
                self._results[spec.task_id] = result
                return result

            attempts = attempt
            start = asyncio.get_event_loop().time()

            try:
                output = await asyncio.wait_for(
                    spec.fn(*spec.args, **spec.kwargs),
                    timeout=spec.timeout_seconds,
                )
                duration = asyncio.get_event_loop().time() - start

                result = TaskResult(
                    task_id=spec.task_id,
                    status=TaskStatus.COMPLETED,
                    output=output,
                    duration_seconds=round(duration, 4),
                    attempts=attempts,
                )
                self._results[spec.task_id] = result

                logger.info(
                    "task_completed",
                    task_id=spec.task_id,
                    name=spec.name,
                    duration=result.duration_seconds,
                    attempts=attempts,
                )
                return result

            except asyncio.TimeoutError:
                duration = asyncio.get_event_loop().time() - start
                last_error = f"Task timed out after {spec.timeout_seconds}s"
                logger.warning(
                    "task_timeout",
                    task_id=spec.task_id,
                    name=spec.name,
                    attempt=attempt,
                    timeout=spec.timeout_seconds,
                )

            except asyncio.CancelledError:
                result = TaskResult(
                    task_id=spec.task_id,
                    status=TaskStatus.CANCELLED,
                    error="Task was cancelled",
                    attempts=attempts,
                )
                self._results[spec.task_id] = result
                return result

            except Exception as exc:
                duration = asyncio.get_event_loop().time() - start
                last_error = f"{type(exc).__name__}: {exc}"
                logger.warning(
                    "task_attempt_failed",
                    task_id=spec.task_id,
                    name=spec.name,
                    attempt=attempt,
                    error=last_error,
                )

            # Exponential backoff before retry
            if attempt <= spec.max_retries:
                backoff = self._config.retry_backoff_seconds * (2 ** (attempt - 1))
                await asyncio.sleep(backoff)

        # All retries exhausted
        status = TaskStatus.TIMED_OUT if "timed out" in last_error else TaskStatus.FAILED
        result = TaskResult(
            task_id=spec.task_id,
            status=status,
            error=last_error,
            attempts=attempts,
        )
        self._results[spec.task_id] = result

        logger.error(
            "task_failed",
            task_id=spec.task_id,
            name=spec.name,
            error=last_error,
            attempts=attempts,
        )
        return result

    # -- introspection ------------------------------------------------------

    @property
    def pending_count(self) -> int:
        """Number of tasks still waiting in the queue."""
        return self._queue.qsize()

    @property
    def running_count(self) -> int:
        """Number of tasks currently executing."""
        return sum(1 for t in self._running.values() if not t.done())

    def get_result(self, task_id: str) -> TaskResult | None:
        """Retrieve the result for a previously executed task."""
        return self._results.get(task_id)
