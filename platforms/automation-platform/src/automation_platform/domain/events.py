"""Domain events — frozen dataclasses representing things that happened."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class PipelineStarted:
    pipeline_id: str
    pipeline_name: str
    stage_count: int
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    timestamp: float = field(default_factory=time.time)


@dataclass(frozen=True, slots=True)
class PipelineCompleted:
    pipeline_id: str
    pipeline_name: str
    duration_seconds: float
    stages_completed: int
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    timestamp: float = field(default_factory=time.time)


@dataclass(frozen=True, slots=True)
class PipelineFailed:
    pipeline_id: str
    pipeline_name: str
    failed_stage: str
    error: str
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    timestamp: float = field(default_factory=time.time)


@dataclass(frozen=True, slots=True)
class StageStarted:
    pipeline_id: str
    stage_name: str
    agent_type: str
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    timestamp: float = field(default_factory=time.time)


@dataclass(frozen=True, slots=True)
class StageCompleted:
    pipeline_id: str
    stage_name: str
    duration_seconds: float
    task_count: int
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    timestamp: float = field(default_factory=time.time)


@dataclass(frozen=True, slots=True)
class TaskDispatched:
    task_id: str
    command: str
    agent_id: str
    mode: str
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    timestamp: float = field(default_factory=time.time)


@dataclass(frozen=True, slots=True)
class TaskCompleted:
    task_id: str
    success: bool
    duration_seconds: float
    result: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    timestamp: float = field(default_factory=time.time)
