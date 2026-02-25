"""Domain entities — Pipeline, Stage, Agent, Task."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from automation_platform.domain.value_objects import (
    AgentStatus,
    AgentType,
    ExecutionMode,
    PipelineStatus,
    StageBudget,
    StageStatus,
    TaskStatus,
)


@dataclass(slots=True)
class Task:
    """A single unit of work to be dispatched to an agent."""

    id: str = field(default_factory=lambda: f"task-{uuid.uuid4().hex[:12]}")
    command: str = ""
    input_data: dict[str, Any] = field(default_factory=dict)
    result: dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    mode: ExecutionMode = ExecutionMode.STANDARD
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    completed_at: float | None = None
    error: str | None = None

    @property
    def duration_seconds(self) -> float | None:
        if self.started_at is None:
            return None
        end = self.completed_at or time.time()
        return end - self.started_at

    def mark_running(self) -> None:
        self.status = TaskStatus.RUNNING
        self.started_at = time.time()

    def mark_completed(self, result: dict[str, Any] | None = None) -> None:
        self.status = TaskStatus.COMPLETED
        self.completed_at = time.time()
        if result is not None:
            self.result = result

    def mark_failed(self, error: str) -> None:
        self.status = TaskStatus.FAILED
        self.completed_at = time.time()
        self.error = error

    def mark_timed_out(self) -> None:
        self.status = TaskStatus.TIMED_OUT
        self.completed_at = time.time()
        self.error = "Task execution timed out"


@dataclass(slots=True)
class Stage:
    """A named phase within a pipeline, executed by a specific agent type."""

    name: str
    budget: StageBudget = field(default_factory=StageBudget)
    agent_type: AgentType = AgentType.ANALYZER
    status: StageStatus = StageStatus.PENDING
    tasks: list[Task] = field(default_factory=list)
    started_at: float | None = None
    completed_at: float | None = None
    error: str | None = None

    @property
    def duration_seconds(self) -> float | None:
        if self.started_at is None:
            return None
        end = self.completed_at or time.time()
        return end - self.started_at

    def mark_running(self) -> None:
        self.status = StageStatus.RUNNING
        self.started_at = time.time()

    def mark_completed(self) -> None:
        self.status = StageStatus.COMPLETED
        self.completed_at = time.time()

    def mark_failed(self, error: str) -> None:
        self.status = StageStatus.FAILED
        self.completed_at = time.time()
        self.error = error


@dataclass(slots=True)
class Agent:
    """An execution agent in the pool."""

    id: str = field(default_factory=lambda: f"agent-{uuid.uuid4().hex[:12]}")
    type: AgentType = AgentType.ANALYZER
    status: AgentStatus = AgentStatus.IDLE
    current_task_id: str | None = None
    tasks_completed: int = 0
    tasks_failed: int = 0
    created_at: float = field(default_factory=time.time)
    last_heartbeat: float = field(default_factory=time.time)

    @property
    def is_available(self) -> bool:
        return self.status == AgentStatus.IDLE

    def assign_task(self, task_id: str) -> None:
        self.status = AgentStatus.BUSY
        self.current_task_id = task_id

    def complete_task(self) -> None:
        self.status = AgentStatus.IDLE
        self.current_task_id = None
        self.tasks_completed += 1
        self.last_heartbeat = time.time()

    def fail_task(self) -> None:
        self.status = AgentStatus.IDLE
        self.current_task_id = None
        self.tasks_failed += 1
        self.last_heartbeat = time.time()

    def heartbeat(self) -> None:
        self.last_heartbeat = time.time()


@dataclass(slots=True)
class Pipeline:
    """A multi-stage pipeline that orchestrates sequential execution of stages."""

    id: str = field(default_factory=lambda: f"pipe-{uuid.uuid4().hex[:12]}")
    name: str = ""
    stages: list[Stage] = field(default_factory=list)
    status: PipelineStatus = PipelineStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    completed_at: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_seconds(self) -> float | None:
        if self.started_at is None:
            return None
        end = self.completed_at or time.time()
        return end - self.started_at

    @property
    def current_stage(self) -> Stage | None:
        for stage in self.stages:
            if stage.status == StageStatus.RUNNING:
                return stage
        return None

    @property
    def completed_stages(self) -> list[Stage]:
        return [s for s in self.stages if s.status == StageStatus.COMPLETED]

    def mark_running(self) -> None:
        self.status = PipelineStatus.RUNNING
        self.started_at = time.time()

    def mark_completed(self) -> None:
        self.status = PipelineStatus.COMPLETED
        self.completed_at = time.time()

    def mark_failed(self) -> None:
        self.status = PipelineStatus.FAILED
        self.completed_at = time.time()

    def mark_rolled_back(self) -> None:
        self.status = PipelineStatus.ROLLED_BACK
        self.completed_at = time.time()
