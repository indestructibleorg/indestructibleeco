"""Domain exceptions for the automation platform."""

from __future__ import annotations

from platform_shared.domain.errors import PlatformError


class PipelineNotFoundError(PlatformError):
    """Raised when a pipeline cannot be located by id."""

    def __init__(self, pipeline_id: str) -> None:
        super().__init__(
            f"Pipeline not found: {pipeline_id}",
            code="PIPELINE_NOT_FOUND",
        )
        self.pipeline_id = pipeline_id


class StageExecutionError(PlatformError):
    """Raised when a pipeline stage fails during execution."""

    def __init__(self, stage_name: str, reason: str) -> None:
        super().__init__(
            f"Stage '{stage_name}' failed: {reason}",
            code="STAGE_EXECUTION_ERROR",
        )
        self.stage_name = stage_name
        self.reason = reason


class AgentPoolExhaustedError(PlatformError):
    """Raised when no agents are available to handle a task."""

    def __init__(self, agent_type: str, pool_size: int) -> None:
        super().__init__(
            f"No available agents of type '{agent_type}' in pool of {pool_size}",
            code="AGENT_POOL_EXHAUSTED",
        )
        self.agent_type = agent_type
        self.pool_size = pool_size


class TaskTimeoutError(PlatformError):
    """Raised when a task exceeds its time budget."""

    def __init__(self, task_id: str, timeout_seconds: float) -> None:
        super().__init__(
            f"Task '{task_id}' timed out after {timeout_seconds}s",
            code="TASK_TIMEOUT",
        )
        self.task_id = task_id
        self.timeout_seconds = timeout_seconds
