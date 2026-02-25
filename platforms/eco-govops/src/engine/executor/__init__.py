"""Executor subsystem — async task execution with retry and concurrency control.

Exports:
    TaskExecutor  -- Priority-ordered concurrent task runner.
    TaskResult    -- Outcome dataclass for an executed task.
    TaskStatus    -- Lifecycle enum for task states.
    TaskPriority  -- Priority levels for queue ordering.
    ExecutorConfig -- Pydantic configuration model.
"""

from engine.executor.task_executor import (
    ExecutorConfig,
    TaskExecutor,
    TaskPriority,
    TaskResult,
    TaskStatus,
)

__all__ = [
    "ExecutorConfig",
    "TaskExecutor",
    "TaskPriority",
    "TaskResult",
    "TaskStatus",
]
