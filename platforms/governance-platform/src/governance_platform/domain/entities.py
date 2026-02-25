"""Governance domain entities — the core business objects."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from governance_platform.domain.value_objects import (
    ComplianceLevel,
    GateVerdict,
    PolicySeverity,
)


@dataclass(frozen=True, slots=True)
class PolicyRule:
    """A single rule within a policy: field <operator> value."""

    field: str
    operator: str  # eq, ne, gt, lt, contains, matches_regex
    value: Any


@dataclass(slots=True)
class Policy:
    """A governance policy containing one or more rules."""

    id: str = field(default_factory=lambda: f"pol-{uuid.uuid4().hex[:12]}")
    name: str = ""
    rules: list[PolicyRule] = field(default_factory=list)
    severity: PolicySeverity = PolicySeverity.MEDIUM
    description: str = ""
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class PolicyResult:
    """The result of evaluating a single policy against an operation."""

    policy_id: str
    policy_name: str
    passed: bool
    violations: list[str] = field(default_factory=list)
    severity: PolicySeverity = PolicySeverity.MEDIUM


@dataclass(slots=True)
class QualityGate:
    """A quality gate with a set of checks and a pass/fail threshold."""

    id: str = field(default_factory=lambda: f"gate-{uuid.uuid4().hex[:12]}")
    name: str = ""
    checks: list[GateCheck] = field(default_factory=list)
    threshold: float = 1.0  # 0.0-1.0 — fraction of checks that must pass


@dataclass(frozen=True, slots=True)
class GateCheck:
    """A single check within a quality gate."""

    name: str
    field: str
    operator: str  # eq, ne, gt, lt, gte, lte, contains, not_empty
    expected: Any


@dataclass(slots=True)
class ComplianceReport:
    """Result of running a quality gate against data."""

    gate_id: str
    gate_name: str = ""
    results: list[CheckResult] = field(default_factory=list)
    passed: bool = False
    score: float = 0.0
    verdict: GateVerdict = GateVerdict.FAIL
    compliance_level: ComplianceLevel = ComplianceLevel.NONE


@dataclass(frozen=True, slots=True)
class CheckResult:
    """Result of a single gate check."""

    check_name: str
    passed: bool
    actual: Any = None
    expected: Any = None
    message: str = ""


@dataclass(slots=True)
class ReasoningQuery:
    """A query to the dual-path reasoning engine."""

    query_id: str = field(default_factory=lambda: f"rq-{uuid.uuid4().hex[:12]}")
    question: str = ""
    sources: list[str] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ReasoningResult:
    """The final answer from the reasoning engine, with decision trail."""

    query_id: str
    answer: str
    decision: str = ""  # ArbitrationDecision value
    internal_answer: str = ""
    internal_confidence: float = 0.0
    external_answer: str = ""
    external_confidence: float = 0.0
    trail: list[str] = field(default_factory=list)
