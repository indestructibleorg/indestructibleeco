"""Domain layer — entities, value objects, events, and exceptions."""

from automation_platform.domain.entities import Agent, Pipeline, Stage, Task
from automation_platform.domain.events import (
    PipelineCompleted,
    PipelineFailed,
    PipelineStarted,
    StageCompleted,
    StageStarted,
    TaskCompleted,
    TaskDispatched,
)
from automation_platform.domain.exceptions import (
    AgentPoolExhaustedError,
    PipelineNotFoundError,
    StageExecutionError,
    TaskTimeoutError,
)
from automation_platform.domain.value_objects import (
    AgentStatus,
    AgentType,
    ExecutionMode,
    PipelineStatus,
    StageBudget,
    StageStatus,
    TaskStatus,
)

__all__ = [
    # Entities
    "Pipeline",
    "Stage",
    "Agent",
    "Task",
    # Value objects
    "ExecutionMode",
    "PipelineStatus",
    "AgentType",
    "AgentStatus",
    "StageStatus",
    "StageBudget",
    "TaskStatus",
    # Events
    "PipelineStarted",
    "PipelineCompleted",
    "PipelineFailed",
    "StageStarted",
    "StageCompleted",
    "TaskDispatched",
    "TaskCompleted",
    # Exceptions
    "PipelineNotFoundError",
    "StageExecutionError",
    "AgentPoolExhaustedError",
    "TaskTimeoutError",
]
