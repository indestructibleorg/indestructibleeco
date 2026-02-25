"""Compliance status value objects for the Governance Operations Platform.

Provides the ComplianceStatus enum representing the possible compliance states
of a governance module, and the ComplianceScore dataclass that captures a
quantitative compliance assessment with grade mapping.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Grade boundaries — maps a numeric 0-100 score to a letter grade A-F.
# ---------------------------------------------------------------------------
_GRADE_BOUNDARIES: list[tuple[float, str]] = [
    (90.0, "A"),
    (80.0, "B"),
    (70.0, "C"),
    (60.0, "D"),
    (0.0, "F"),
]


class ComplianceStatus(str, enum.Enum):
    """Represents the compliance posture of a governed module.

    Values:
        COMPLIANT: Fully passes all governance checks.
        NON_COMPLIANT: One or more governance checks have failed.
        PARTIALLY_COMPLIANT: Some checks pass, others pending or degraded.
        UNKNOWN: Module has not been scanned yet or data is stale.
        EXEMPT: Module is explicitly excluded from compliance enforcement.
    """

    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    UNKNOWN = "unknown"
    EXEMPT = "exempt"

    # -- convenience helpers ------------------------------------------------

    @property
    def is_passing(self) -> bool:
        """Return True when the status is considered acceptable for gate passage."""
        return self in {
            ComplianceStatus.COMPLIANT,
            ComplianceStatus.EXEMPT,
        }

    @property
    def requires_action(self) -> bool:
        """Return True if the status demands human or automated intervention."""
        return self in {
            ComplianceStatus.NON_COMPLIANT,
            ComplianceStatus.PARTIALLY_COMPLIANT,
        }

    @classmethod
    def from_score(cls, score: float) -> ComplianceStatus:
        """Derive a compliance status from a numeric score (0-100).

        Thresholds:
            >= 90  -> COMPLIANT
            >= 60  -> PARTIALLY_COMPLIANT
            <  60  -> NON_COMPLIANT
        """
        if score >= 90.0:
            return cls.COMPLIANT
        if score >= 60.0:
            return cls.PARTIALLY_COMPLIANT
        return cls.NON_COMPLIANT


def _score_to_grade(score: float) -> str:
    """Map a 0-100 score to a letter grade A-F."""
    for threshold, grade in _GRADE_BOUNDARIES:
        if score >= threshold:
            return grade
    return "F"


@dataclass(frozen=True, slots=True)
class ComplianceScore:
    """Quantitative compliance assessment attached to a module or scan cycle.

    Attributes:
        score: Numeric value in the range [0.0, 100.0].
        grade: Letter grade automatically derived from *score* when not given.
        details: Arbitrary breakdown (e.g. per-rule scores, timestamps).
    """

    score: float
    grade: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Validate bounds
        if not (0.0 <= self.score <= 100.0):
            raise ValueError(
                f"ComplianceScore.score must be between 0 and 100, got {self.score}"
            )
        # Auto-derive grade when not explicitly provided
        if not self.grade:
            object.__setattr__(self, "grade", _score_to_grade(self.score))
        logger.debug(
            "compliance_score_created",
            score=self.score,
            grade=self.grade,
        )

    # -- derived helpers ----------------------------------------------------

    @property
    def status(self) -> ComplianceStatus:
        """Derive the categorical ComplianceStatus from the numeric score."""
        return ComplianceStatus.from_score(self.score)

    @property
    def is_passing(self) -> bool:
        """Shortcut: does this score translate to a passing status?"""
        return self.status.is_passing

    def meets_threshold(self, minimum: float) -> bool:
        """Return True if the score meets or exceeds *minimum*."""
        if not (0.0 <= minimum <= 100.0):
            raise ValueError(f"Threshold must be between 0 and 100, got {minimum}")
        return self.score >= minimum

    def delta(self, other: ComplianceScore) -> float:
        """Compute the signed difference ``self.score - other.score``."""
        return self.score - other.score

    def with_details(self, **extra: Any) -> ComplianceScore:
        """Return a new ComplianceScore with merged details (immutable update)."""
        merged = {**self.details, **extra}
        return ComplianceScore(score=self.score, grade=self.grade, details=merged)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary for transport / persistence."""
        return {
            "score": self.score,
            "grade": self.grade,
            "status": self.status.value,
            "is_passing": self.is_passing,
            "details": self.details,
        }
