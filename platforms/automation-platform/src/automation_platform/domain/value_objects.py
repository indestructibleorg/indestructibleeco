"""Value objects — enums and immutable descriptors for the automation domain."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ExecutionMode(str, Enum):
    """How fast the task must complete."""

    INSTANT = "instant"        # < 100ms
    FAST = "fast"              # < 500ms
    STANDARD = "standard"      # < 5s
    BACKGROUND = "background"  # no strict SLA


class PipelineStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class AgentType(str, Enum):
    ANALYZER = "analyzer"
    GENERATOR = "generator"
    VALIDATOR = "validator"
    DEPLOYER = "deployer"


class AgentStatus(str, Enum):
    IDLE = "idle"
    BUSY = "busy"
    FAILED = "failed"
    DRAINING = "draining"
    OFFLINE = "offline"


class TaskStatus(str, Enum):
    PENDING = "pending"
    DISPATCHED = "dispatched"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"


@dataclass(frozen=True, slots=True)
class StageBudget:
    """Time and resource budget for a single pipeline stage."""

    timeout_seconds: float = 30.0
    max_retries: int = 1
    mode: ExecutionMode = ExecutionMode.STANDARD

    @property
    def sla_seconds(self) -> float:
        """SLA ceiling based on execution mode."""
        sla_map = {
            ExecutionMode.INSTANT: 0.1,
            ExecutionMode.FAST: 0.5,
            ExecutionMode.STANDARD: 5.0,
            ExecutionMode.BACKGROUND: float("inf"),
        }
        return sla_map[self.mode]
