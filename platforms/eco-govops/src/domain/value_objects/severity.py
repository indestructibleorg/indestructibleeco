"""Severity value objects for the Governance Operations Platform.

Defines the Severity enum used across scan findings, gate conditions, and
compliance events, plus a SeverityThreshold dataclass for configurable
severity-based filtering and comparison.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Numeric weights — higher number means more severe
# ---------------------------------------------------------------------------
_SEVERITY_WEIGHTS: dict[str, int] = {
    "critical": 50,
    "high": 40,
    "medium": 30,
    "low": 20,
    "info": 10,
}


class Severity(str, enum.Enum):
    """Ordered severity levels for governance findings.

    The ordering is CRITICAL > HIGH > MEDIUM > LOW > INFO.  Comparison
    operators are supported so that ``Severity.HIGH >= Severity.MEDIUM``
    evaluates to ``True``.
    """

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

    # -- rich comparison via numeric weight ----------------------------------

    @property
    def weight(self) -> int:
        """Return the numeric weight for this severity level."""
        return _SEVERITY_WEIGHTS[self.value]

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Severity):
            return NotImplemented
        return self.weight < other.weight

    def __le__(self, other: object) -> bool:
        if not isinstance(other, Severity):
            return NotImplemented
        return self.weight <= other.weight

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, Severity):
            return NotImplemented
        return self.weight > other.weight

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, Severity):
            return NotImplemented
        return self.weight >= other.weight

    # -- convenience ---------------------------------------------------------

    @property
    def is_actionable(self) -> bool:
        """Return True for severities that typically require remediation."""
        return self in {Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM}

    @property
    def is_blocking(self) -> bool:
        """Return True for severities that should block a deployment gate."""
        return self in {Severity.CRITICAL, Severity.HIGH}

    @classmethod
    def from_string(cls, raw: str) -> Severity:
        """Parse a case-insensitive string into a Severity member.

        Raises ``ValueError`` if *raw* does not match any member.
        """
        normalised = raw.strip().lower()
        try:
            return cls(normalised)
        except ValueError:
            valid = ", ".join(m.value for m in cls)
            raise ValueError(
                f"Unknown severity '{raw}'. Valid values: {valid}"
            ) from None


@dataclass(frozen=True, slots=True)
class SeverityThreshold:
    """Configurable threshold used to decide whether findings are acceptable.

    A threshold specifies the *minimum_severity* that is considered relevant
    and optional per-severity *max_counts* that cap how many findings of each
    level are tolerable before a gate/check fails.

    Attributes:
        minimum_severity: Only findings at this severity or above are counted.
        max_counts: Per-severity maximum allowed counts.  Keys are Severity
            members; missing keys mean "unlimited".
        metadata: Arbitrary additional context (policy name, ticket, etc.).
    """

    minimum_severity: Severity = Severity.LOW
    max_counts: dict[Severity, int] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for sev, count in self.max_counts.items():
            if count < 0:
                raise ValueError(
                    f"max_counts[{sev.value}] must be non-negative, got {count}"
                )
        logger.debug(
            "severity_threshold_created",
            minimum=self.minimum_severity.value,
            max_counts={s.value: c for s, c in self.max_counts.items()},
        )

    # -- evaluation ----------------------------------------------------------

    def is_relevant(self, severity: Severity) -> bool:
        """Return True if *severity* meets or exceeds the minimum threshold."""
        return severity >= self.minimum_severity

    def exceeds(self, severity: Severity, count: int) -> bool:
        """Return True if *count* findings at *severity* exceed the allowed max.

        If no cap is configured for *severity*, the count is always acceptable.
        """
        if not self.is_relevant(severity):
            return False
        cap = self.max_counts.get(severity)
        if cap is None:
            return False
        return count > cap

    def evaluate_counts(self, counts: dict[Severity, int]) -> bool:
        """Evaluate a full set of severity counts against this threshold.

        Returns True when **all** counts are within limits (i.e. the check
        passes).  Returns False if any single severity exceeds its cap.
        """
        for severity, count in counts.items():
            if self.exceeds(severity, count):
                logger.warning(
                    "severity_threshold_exceeded",
                    severity=severity.value,
                    count=count,
                    cap=self.max_counts.get(severity),
                )
                return False
        return True

    def failing_severities(self, counts: dict[Severity, int]) -> list[Severity]:
        """Return the list of severity levels whose counts exceed caps."""
        return [
            sev
            for sev, count in counts.items()
            if self.exceeds(sev, count)
        ]

    def with_max(self, severity: Severity, max_count: int) -> SeverityThreshold:
        """Return a new threshold with an updated cap for *severity*."""
        updated = {**self.max_counts, severity: max_count}
        return SeverityThreshold(
            minimum_severity=self.minimum_severity,
            max_counts=updated,
            metadata=self.metadata,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the threshold to a plain dictionary."""
        return {
            "minimum_severity": self.minimum_severity.value,
            "max_counts": {s.value: c for s, c in self.max_counts.items()},
            "metadata": self.metadata,
        }
