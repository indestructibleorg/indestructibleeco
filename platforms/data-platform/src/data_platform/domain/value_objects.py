"""Value objects — immutable, identity-less domain concepts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EvidenceType(str, Enum):
    """Classification of evidence records."""

    FILE = "file"
    LOG = "log"
    METRIC = "metric"
    EVENT = "event"
    ASSERTION = "assertion"


class PipelinePhase(str, Enum):
    """Stages of a data pipeline lifecycle."""

    INGEST = "ingest"
    VALIDATE = "validate"
    TRANSFORM = "transform"
    STORE = "store"


class ReplayMode(str, Enum):
    """How a replay session advances through events."""

    SEQUENTIAL = "sequential"
    FAST_FORWARD = "fast_forward"
    STEP_BY_STEP = "step_by_step"


@dataclass(frozen=True, slots=True)
class QualityScore:
    """A bounded quality score (0.0 to 1.0) with pass/fail semantics.

    A score >= threshold is considered passing.
    """

    value: float
    threshold: float = 0.8

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            raise ValueError(f"QualityScore value must be 0.0-1.0, got {self.value}")
        if not 0.0 <= self.threshold <= 1.0:
            raise ValueError(f"QualityScore threshold must be 0.0-1.0, got {self.threshold}")

    @property
    def passed(self) -> bool:
        return self.value >= self.threshold

    @property
    def failed(self) -> bool:
        return not self.passed

    def __str__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return f"QualityScore({self.value:.3f}, {status})"
