"""Governance domain events — emitted when significant governance actions occur."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class GovernanceEvent:
    """Base class for all governance events."""

    event_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    timestamp: float = field(default_factory=time.time)
    source: str = "governance-platform"


@dataclass(frozen=True, slots=True)
class PolicyEvaluated(GovernanceEvent):
    """Emitted after a set of policies are evaluated against an operation."""

    policy_id: str = ""
    policy_name: str = ""
    passed: bool = True
    violation_count: int = 0
    severity: str = "medium"
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class GatePassed(GovernanceEvent):
    """Emitted when a quality gate passes."""

    gate_id: str = ""
    gate_name: str = ""
    score: float = 0.0
    checks_passed: int = 0
    checks_total: int = 0


@dataclass(frozen=True, slots=True)
class GateFailed(GovernanceEvent):
    """Emitted when a quality gate fails."""

    gate_id: str = ""
    gate_name: str = ""
    score: float = 0.0
    checks_passed: int = 0
    checks_total: int = 0
    failures: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ViolationDetected(GovernanceEvent):
    """Emitted when a policy violation is detected."""

    policy_id: str = ""
    policy_name: str = ""
    rule_field: str = ""
    rule_operator: str = ""
    expected: Any = None
    actual: Any = None
    severity: str = "medium"
    message: str = ""


@dataclass(frozen=True, slots=True)
class ReasoningCompleted(GovernanceEvent):
    """Emitted when a dual-path reasoning query completes."""

    query_id: str = ""
    question: str = ""
    decision: str = ""
    confidence: float = 0.0
    source_used: str = ""
