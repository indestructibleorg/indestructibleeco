"""Tests for governance domain layer — entities, value objects, events, exceptions."""

from __future__ import annotations

import pytest

from governance_platform.domain.entities import (
    CheckResult,
    ComplianceReport,
    GateCheck,
    Policy,
    PolicyResult,
    PolicyRule,
    QualityGate,
    ReasoningQuery,
    ReasoningResult,
)
from governance_platform.domain.value_objects import (
    ArbitrationDecision,
    ComplianceLevel,
    GateVerdict,
    PolicySeverity,
    ReasoningConfidence,
)
from governance_platform.domain.events import (
    GateFailed,
    GatePassed,
    PolicyEvaluated,
    ReasoningCompleted,
    ViolationDetected,
)
from governance_platform.domain.exceptions import (
    GovernanceError,
    PolicyEvaluationError,
    QualityGateError,
    ReasoningError,
    SandboxPolicyError,
)


# -- PolicySeverity -----------------------------------------------------------


class TestPolicySeverity:
    def test_values(self):
        assert PolicySeverity.CRITICAL.value == "critical"
        assert PolicySeverity.HIGH.value == "high"
        assert PolicySeverity.MEDIUM.value == "medium"
        assert PolicySeverity.LOW.value == "low"

    def test_numeric_ordering(self):
        assert PolicySeverity.CRITICAL.numeric == 4
        assert PolicySeverity.HIGH.numeric == 3
        assert PolicySeverity.MEDIUM.numeric == 2
        assert PolicySeverity.LOW.numeric == 1

    def test_comparison(self):
        assert PolicySeverity.LOW < PolicySeverity.MEDIUM
        assert PolicySeverity.MEDIUM < PolicySeverity.HIGH
        assert PolicySeverity.HIGH < PolicySeverity.CRITICAL

    def test_str_enum(self):
        assert str(PolicySeverity.CRITICAL) == "PolicySeverity.CRITICAL"
        assert PolicySeverity("critical") == PolicySeverity.CRITICAL


# -- GateVerdict --------------------------------------------------------------


class TestGateVerdict:
    def test_values(self):
        assert GateVerdict.PASS.value == "pass"
        assert GateVerdict.FAIL.value == "fail"
        assert GateVerdict.WARN.value == "warn"
        assert GateVerdict.SKIP.value == "skip"


# -- ComplianceLevel ----------------------------------------------------------


class TestComplianceLevel:
    def test_values(self):
        assert ComplianceLevel.FULL.value == "full"
        assert ComplianceLevel.PARTIAL.value == "partial"
        assert ComplianceLevel.NONE.value == "none"


# -- ArbitrationDecision ------------------------------------------------------


class TestArbitrationDecision:
    def test_values(self):
        assert ArbitrationDecision.INTERNAL.value == "internal"
        assert ArbitrationDecision.EXTERNAL.value == "external"
        assert ArbitrationDecision.HYBRID.value == "hybrid"
        assert ArbitrationDecision.REJECT.value == "reject"


# -- ReasoningConfidence ------------------------------------------------------


class TestReasoningConfidence:
    def test_valid_range(self):
        c = ReasoningConfidence(0.85)
        assert c.value == 0.85
        assert float(c) == 0.85

    def test_clamp_high(self):
        c = ReasoningConfidence(1.5)
        assert c.value == 1.0

    def test_clamp_low(self):
        c = ReasoningConfidence(-0.3)
        assert c.value == 0.0

    def test_comparison(self):
        low = ReasoningConfidence(0.3)
        high = ReasoningConfidence(0.9)
        assert low < high
        assert high > low
        assert low < 0.5
        assert high > 0.5
        assert low <= 0.3
        assert high >= 0.9

    def test_frozen(self):
        c = ReasoningConfidence(0.5)
        with pytest.raises(AttributeError):
            c.value = 0.9  # type: ignore[misc]


# -- PolicyRule ---------------------------------------------------------------


class TestPolicyRule:
    def test_creation(self):
        rule = PolicyRule(field="status", operator="eq", value="active")
        assert rule.field == "status"
        assert rule.operator == "eq"
        assert rule.value == "active"

    def test_frozen(self):
        rule = PolicyRule(field="x", operator="eq", value=1)
        with pytest.raises(AttributeError):
            rule.field = "y"  # type: ignore[misc]


# -- Policy -------------------------------------------------------------------


class TestPolicy:
    def test_default_id_generated(self):
        p = Policy(name="Test")
        assert p.id.startswith("pol-")
        assert p.name == "Test"
        assert p.severity == PolicySeverity.MEDIUM
        assert p.enabled is True

    def test_custom_fields(self):
        p = Policy(
            id="custom-id",
            name="Custom",
            rules=[PolicyRule(field="a", operator="eq", value=1)],
            severity=PolicySeverity.CRITICAL,
            enabled=False,
        )
        assert p.id == "custom-id"
        assert len(p.rules) == 1
        assert p.severity == PolicySeverity.CRITICAL
        assert p.enabled is False


# -- QualityGate --------------------------------------------------------------


class TestQualityGate:
    def test_default_id(self):
        g = QualityGate(name="Test Gate")
        assert g.id.startswith("gate-")
        assert g.threshold == 1.0

    def test_with_checks(self):
        g = QualityGate(
            id="g1",
            name="Gate",
            checks=[GateCheck(name="c1", field="f", operator="eq", expected=True)],
            threshold=0.8,
        )
        assert len(g.checks) == 1
        assert g.threshold == 0.8


# -- ComplianceReport ---------------------------------------------------------


class TestComplianceReport:
    def test_default_state(self):
        r = ComplianceReport(gate_id="g1")
        assert r.passed is False
        assert r.score == 0.0
        assert r.verdict == GateVerdict.FAIL
        assert r.compliance_level == ComplianceLevel.NONE


# -- ReasoningQuery -----------------------------------------------------------


class TestReasoningQuery:
    def test_creation(self):
        q = ReasoningQuery(question="What is governance?")
        assert q.query_id.startswith("rq-")
        assert q.question == "What is governance?"
        assert q.sources == []


# -- ReasoningResult ----------------------------------------------------------


class TestReasoningResult:
    def test_creation(self):
        r = ReasoningResult(query_id="rq-123", answer="Test answer", decision="internal")
        assert r.query_id == "rq-123"
        assert r.answer == "Test answer"
        assert r.trail == []


# -- Events -------------------------------------------------------------------


class TestEvents:
    def test_policy_evaluated(self):
        e = PolicyEvaluated(policy_id="p1", policy_name="Test", passed=True)
        assert e.policy_id == "p1"
        assert e.passed is True
        assert e.source == "governance-platform"
        assert e.event_id  # non-empty

    def test_gate_passed(self):
        e = GatePassed(gate_id="g1", score=0.95, checks_passed=3, checks_total=3)
        assert e.gate_id == "g1"
        assert e.score == 0.95

    def test_gate_failed(self):
        e = GateFailed(gate_id="g1", score=0.5, failures=["check_a"])
        assert e.score == 0.5
        assert "check_a" in e.failures

    def test_violation_detected(self):
        e = ViolationDetected(
            policy_id="p1",
            rule_field="env",
            rule_operator="eq",
            expected="prod",
            actual="dev",
            severity="high",
        )
        assert e.actual == "dev"
        assert e.severity == "high"

    def test_reasoning_completed(self):
        e = ReasoningCompleted(query_id="rq-1", decision="hybrid", confidence=0.88)
        assert e.decision == "hybrid"
        assert e.confidence == 0.88


# -- Exceptions ---------------------------------------------------------------


class TestExceptions:
    def test_governance_error(self):
        e = GovernanceError("something broke")
        assert str(e) == "something broke"
        assert e.code == "GOVERNANCE_ERROR"

    def test_policy_evaluation_error(self):
        e = PolicyEvaluationError("bad rule", policy_id="p1")
        assert e.policy_id == "p1"
        assert e.code == "POLICY_EVALUATION_ERROR"

    def test_quality_gate_error(self):
        e = QualityGateError("gate failed", gate_id="g1")
        assert e.gate_id == "g1"

    def test_reasoning_error(self):
        e = ReasoningError("no answer", query_id="rq-1")
        assert e.query_id == "rq-1"

    def test_sandbox_policy_error(self):
        e = SandboxPolicyError("timeout", sandbox_id="sb-1")
        assert e.sandbox_id == "sb-1"
        assert e.code == "SANDBOX_POLICY_ERROR"

    def test_inheritance(self):
        """All governance exceptions inherit from GovernanceError → PlatformError."""
        from platform_shared.domain.errors import PlatformError

        assert issubclass(GovernanceError, PlatformError)
        assert issubclass(PolicyEvaluationError, GovernanceError)
        assert issubclass(QualityGateError, GovernanceError)
        assert issubclass(ReasoningError, GovernanceError)
        assert issubclass(SandboxPolicyError, GovernanceError)
