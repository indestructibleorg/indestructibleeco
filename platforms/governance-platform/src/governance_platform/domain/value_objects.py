"""Governance value objects — immutable, identity-less domain primitives."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PolicySeverity(str, Enum):
    """How critical a policy violation is."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    @property
    def numeric(self) -> int:
        """Numeric weight for severity ordering (higher = more severe)."""
        return {
            PolicySeverity.CRITICAL: 4,
            PolicySeverity.HIGH: 3,
            PolicySeverity.MEDIUM: 2,
            PolicySeverity.LOW: 1,
        }[self]

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, PolicySeverity):
            return NotImplemented
        return self.numeric < other.numeric


class GateVerdict(str, Enum):
    """Outcome of a quality gate evaluation."""

    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    SKIP = "skip"


class ComplianceLevel(str, Enum):
    """Degree of compliance with governance requirements."""

    FULL = "full"
    PARTIAL = "partial"
    NONE = "none"


class ArbitrationDecision(str, Enum):
    """Which retrieval source to prefer during reasoning arbitration."""

    INTERNAL = "internal"
    EXTERNAL = "external"
    HYBRID = "hybrid"
    REJECT = "reject"


@dataclass(frozen=True, slots=True)
class ReasoningConfidence:
    """Confidence score for a reasoning result, clamped to [0.0, 1.0]."""

    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            object.__setattr__(self, "value", max(0.0, min(1.0, self.value)))

    def __float__(self) -> float:
        return self.value

    def __lt__(self, other: object) -> bool:
        if isinstance(other, ReasoningConfidence):
            return self.value < other.value
        if isinstance(other, (int, float)):
            return self.value < other
        return NotImplemented

    def __gt__(self, other: object) -> bool:
        if isinstance(other, ReasoningConfidence):
            return self.value > other.value
        if isinstance(other, (int, float)):
            return self.value > other
        return NotImplemented

    def __ge__(self, other: object) -> bool:
        if isinstance(other, ReasoningConfidence):
            return self.value >= other.value
        if isinstance(other, (int, float)):
            return self.value >= other
        return NotImplemented

    def __le__(self, other: object) -> bool:
        if isinstance(other, ReasoningConfidence):
            return self.value <= other.value
        if isinstance(other, (int, float)):
            return self.value <= other
        return NotImplemented
