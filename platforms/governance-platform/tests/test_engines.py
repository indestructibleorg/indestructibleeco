"""Tests for governance engines — policy evaluation, quality gates, reasoning."""

from __future__ import annotations

import pytest

from governance_platform.domain.entities import (
    GateCheck,
    Policy,
    PolicyRule,
    QualityGate,
)
from governance_platform.domain.value_objects import (
    ArbitrationDecision,
    ComplianceLevel,
    GateVerdict,
    PolicySeverity,
)
from governance_platform.engines.policy_engine import PolicyEngine
from governance_platform.engines.quality_gate_engine import QualityGateEngine
from governance_platform.engines.reasoning_engine import ReasoningEngine
from platform_shared.protocols.engine import EngineStatus


# =============================================================================
# PolicyEngine
# =============================================================================


class TestPolicyEngineOperators:
    """Test every supported operator."""

    def test_eq_match(self, policy_engine: PolicyEngine):
        policy = Policy(
            id="p1", name="eq-test",
            rules=[PolicyRule(field="status", operator="eq", value="active")],
        )
        results = policy_engine.evaluate({"status": "active"}, [policy])
        assert len(results) == 1
        assert results[0].passed is True
        assert results[0].violations == []

    def test_eq_no_match(self, policy_engine: PolicyEngine):
        policy = Policy(
            id="p1", name="eq-test",
            rules=[PolicyRule(field="status", operator="eq", value="active")],
        )
        results = policy_engine.evaluate({"status": "inactive"}, [policy])
        assert results[0].passed is False
        assert len(results[0].violations) == 1

    def test_ne_match(self, policy_engine: PolicyEngine):
        policy = Policy(
            id="p1", name="ne-test",
            rules=[PolicyRule(field="mode", operator="ne", value="debug")],
        )
        results = policy_engine.evaluate({"mode": "production"}, [policy])
        assert results[0].passed is True

    def test_ne_no_match(self, policy_engine: PolicyEngine):
        policy = Policy(
            id="p1", name="ne-test",
            rules=[PolicyRule(field="mode", operator="ne", value="debug")],
        )
        results = policy_engine.evaluate({"mode": "debug"}, [policy])
        assert results[0].passed is False

    def test_gt_match(self, policy_engine: PolicyEngine):
        policy = Policy(
            id="p1", name="gt-test",
            rules=[PolicyRule(field="version", operator="gt", value=1.0)],
        )
        results = policy_engine.evaluate({"version": 2.5}, [policy])
        assert results[0].passed is True

    def test_gt_no_match(self, policy_engine: PolicyEngine):
        policy = Policy(
            id="p1", name="gt-test",
            rules=[PolicyRule(field="version", operator="gt", value=3.0)],
        )
        results = policy_engine.evaluate({"version": 2.5}, [policy])
        assert results[0].passed is False

    def test_lt_match(self, policy_engine: PolicyEngine):
        policy = Policy(
            id="p1", name="lt-test",
            rules=[PolicyRule(field="risk_score", operator="lt", value=5)],
        )
        results = policy_engine.evaluate({"risk_score": 3}, [policy])
        assert results[0].passed is True

    def test_lt_no_match(self, policy_engine: PolicyEngine):
        policy = Policy(
            id="p1", name="lt-test",
            rules=[PolicyRule(field="risk_score", operator="lt", value=5)],
        )
        results = policy_engine.evaluate({"risk_score": 7}, [policy])
        assert results[0].passed is False

    def test_contains_string_match(self, policy_engine: PolicyEngine):
        policy = Policy(
            id="p1", name="contains-test",
            rules=[PolicyRule(field="tags", operator="contains", value="prod")],
        )
        results = policy_engine.evaluate({"tags": "production-ready"}, [policy])
        assert results[0].passed is True

    def test_contains_list_match(self, policy_engine: PolicyEngine):
        policy = Policy(
            id="p1", name="contains-test",
            rules=[PolicyRule(field="regions", operator="contains", value="us-east-1")],
        )
        results = policy_engine.evaluate({"regions": ["us-east-1", "eu-west-1"]}, [policy])
        assert results[0].passed is True

    def test_contains_no_match(self, policy_engine: PolicyEngine):
        policy = Policy(
            id="p1", name="contains-test",
            rules=[PolicyRule(field="tags", operator="contains", value="prod")],
        )
        results = policy_engine.evaluate({"tags": "development"}, [policy])
        assert results[0].passed is False

    def test_matches_regex_match(self, policy_engine: PolicyEngine):
        policy = Policy(
            id="p1", name="regex-test",
            rules=[PolicyRule(field="email", operator="matches_regex", value=r"^[\w.]+@company\.com$")],
        )
        results = policy_engine.evaluate({"email": "user.name@company.com"}, [policy])
        assert results[0].passed is True

    def test_matches_regex_no_match(self, policy_engine: PolicyEngine):
        policy = Policy(
            id="p1", name="regex-test",
            rules=[PolicyRule(field="email", operator="matches_regex", value=r"^[\w.]+@company\.com$")],
        )
        results = policy_engine.evaluate({"email": "user@gmail.com"}, [policy])
        assert results[0].passed is False


class TestPolicyEngineEdgeCases:
    def test_missing_field_is_violation(self, policy_engine: PolicyEngine):
        policy = Policy(
            id="p1", name="missing-test",
            rules=[PolicyRule(field="nonexistent", operator="eq", value="x")],
        )
        results = policy_engine.evaluate({"other": "y"}, [policy])
        assert results[0].passed is False
        assert "missing" in results[0].violations[0].lower() or "violated" in results[0].violations[0].lower()

    def test_missing_field_ne_passes(self, policy_engine: PolicyEngine):
        """ne operator on a missing field should pass (field is 'not equal' to value)."""
        policy = Policy(
            id="p1", name="missing-ne",
            rules=[PolicyRule(field="nonexistent", operator="ne", value="x")],
        )
        results = policy_engine.evaluate({}, [policy])
        assert results[0].passed is True

    def test_nested_field_access(self, policy_engine: PolicyEngine):
        policy = Policy(
            id="p1", name="nested",
            rules=[PolicyRule(field="config.debug", operator="eq", value=False)],
        )
        results = policy_engine.evaluate({"config": {"debug": False}}, [policy])
        assert results[0].passed is True

    def test_disabled_policy_always_passes(self, policy_engine: PolicyEngine):
        policy = Policy(
            id="p1", name="disabled",
            rules=[PolicyRule(field="x", operator="eq", value="impossible")],
            enabled=False,
        )
        results = policy_engine.evaluate({"x": "something_else"}, [policy])
        assert results[0].passed is True

    def test_multiple_policies(self, policy_engine: PolicyEngine):
        p1 = Policy(id="p1", name="a", rules=[PolicyRule(field="x", operator="eq", value=1)])
        p2 = Policy(id="p2", name="b", rules=[PolicyRule(field="y", operator="eq", value=2)])
        results = policy_engine.evaluate({"x": 1, "y": 999}, [p1, p2])
        assert results[0].passed is True
        assert results[1].passed is False

    def test_multiple_rules_all_must_pass(self, policy_engine: PolicyEngine, sample_policy: Policy):
        """All rules in a policy must pass for the policy to pass."""
        # Only one rule matches
        results = policy_engine.evaluate(
            {"environment": "production", "version": "0.5"},
            [sample_policy],
        )
        assert results[0].passed is False  # version 0.5 not > 1.0

    def test_severity_in_result(self, policy_engine: PolicyEngine):
        policy = Policy(
            id="p1", name="sev", severity=PolicySeverity.CRITICAL,
            rules=[PolicyRule(field="x", operator="eq", value=1)],
        )
        results = policy_engine.evaluate({"x": 999}, [policy])
        assert results[0].severity == PolicySeverity.CRITICAL


class TestPolicyEngineProtocol:
    """Test that PolicyEngine implements the Engine protocol."""

    def test_engine_name(self, policy_engine: PolicyEngine):
        assert policy_engine.name == "policy-engine"

    def test_engine_initial_status(self, policy_engine: PolicyEngine):
        assert policy_engine.status == EngineStatus.IDLE

    async def test_engine_lifecycle(self, policy_engine: PolicyEngine):
        await policy_engine.start()
        assert policy_engine.status == EngineStatus.RUNNING
        await policy_engine.stop()
        assert policy_engine.status == EngineStatus.STOPPED

    async def test_engine_execute(self, policy_engine: PolicyEngine):
        result = await policy_engine.execute({
            "operation": {"env": "prod"},
            "policies": [
                {"id": "p1", "name": "test", "rules": [{"field": "env", "operator": "eq", "value": "prod"}]},
            ],
        })
        assert result["all_passed"] is True

    def test_event_history(self, policy_engine: PolicyEngine):
        policy = Policy(id="p1", name="test", rules=[PolicyRule(field="x", operator="eq", value=1)])
        policy_engine.evaluate({"x": 1}, [policy])
        assert len(policy_engine.evaluation_history) == 1
        assert policy_engine.evaluation_history[0].passed is True

    def test_violation_history(self, policy_engine: PolicyEngine):
        policy = Policy(id="p1", name="test", rules=[PolicyRule(field="x", operator="eq", value=1)])
        policy_engine.evaluate({"x": 999}, [policy])
        assert len(policy_engine.violation_history) == 1


# =============================================================================
# QualityGateEngine
# =============================================================================


class TestQualityGateEngine:
    def test_all_checks_pass(self, gate_engine: QualityGateEngine, sample_gate: QualityGate):
        data = {"coverage_pct": 95.0, "tests_passed": True, "critical_issues": 0}
        report = gate_engine.run_gate(sample_gate, data)
        assert report.passed is True
        assert report.score == 1.0
        assert report.verdict == GateVerdict.PASS
        assert report.compliance_level == ComplianceLevel.FULL

    def test_all_checks_fail(self, gate_engine: QualityGateEngine, sample_gate: QualityGate):
        data = {"coverage_pct": 30.0, "tests_passed": False, "critical_issues": 5}
        report = gate_engine.run_gate(sample_gate, data)
        assert report.passed is False
        assert report.score == 0.0
        assert report.verdict == GateVerdict.FAIL
        assert report.compliance_level == ComplianceLevel.NONE

    def test_partial_pass(self, gate_engine: QualityGateEngine, sample_gate: QualityGate):
        """One of three checks fails — score=2/3, but threshold=1.0 so it should fail."""
        data = {"coverage_pct": 95.0, "tests_passed": True, "critical_issues": 2}
        report = gate_engine.run_gate(sample_gate, data)
        assert report.passed is False
        assert abs(report.score - 2 / 3) < 0.01
        assert report.compliance_level == ComplianceLevel.PARTIAL

    def test_lenient_threshold(self, gate_engine: QualityGateEngine, lenient_gate: QualityGate):
        """With threshold=0.66, 2 out of 3 passing should pass."""
        data = {"readme": "# Project", "test_count": 5, "lint_errors": 3}  # lint fails
        report = gate_engine.run_gate(lenient_gate, data)
        assert report.passed is True  # 2/3 >= 0.66
        assert report.verdict == GateVerdict.PASS

    def test_empty_gate_skips(self, gate_engine: QualityGateEngine):
        gate = QualityGate(id="g-empty", name="Empty", checks=[], threshold=1.0)
        report = gate_engine.run_gate(gate, {})
        assert report.passed is True
        assert report.verdict == GateVerdict.SKIP

    def test_missing_field_fails_check(self, gate_engine: QualityGateEngine):
        gate = QualityGate(
            id="g1", name="Test",
            checks=[GateCheck(name="c1", field="missing_field", operator="eq", expected="x")],
        )
        report = gate_engine.run_gate(gate, {"other": "y"})
        assert report.passed is False
        assert "missing" in report.results[0].message.lower()

    def test_not_empty_operator(self, gate_engine: QualityGateEngine):
        gate = QualityGate(
            id="g1", name="Not-Empty Gate",
            checks=[GateCheck(name="desc", field="description", operator="not_empty", expected=None)],
        )
        # Pass case
        report = gate_engine.run_gate(gate, {"description": "Hello"})
        assert report.passed is True

        # Fail case (empty string)
        report = gate_engine.run_gate(gate, {"description": ""})
        assert report.passed is False

    def test_check_results_detail(self, gate_engine: QualityGateEngine, sample_gate: QualityGate):
        data = {"coverage_pct": 95.0, "tests_passed": True, "critical_issues": 0}
        report = gate_engine.run_gate(sample_gate, data)
        assert len(report.results) == 3
        for cr in report.results:
            assert cr.passed is True

    def test_event_history(self, gate_engine: QualityGateEngine, sample_gate: QualityGate):
        gate_engine.run_gate(sample_gate, {"coverage_pct": 95, "tests_passed": True, "critical_issues": 0})
        gate_engine.run_gate(sample_gate, {"coverage_pct": 10, "tests_passed": False, "critical_issues": 9})
        events = gate_engine.event_history
        assert len(events) == 2
        assert events[0].gate_id == sample_gate.id  # passed
        assert events[1].gate_id == sample_gate.id  # failed


class TestQualityGateEngineProtocol:
    def test_engine_name(self, gate_engine: QualityGateEngine):
        assert gate_engine.name == "quality-gate-engine"

    async def test_engine_lifecycle(self, gate_engine: QualityGateEngine):
        await gate_engine.start()
        assert gate_engine.status == EngineStatus.RUNNING
        await gate_engine.stop()
        assert gate_engine.status == EngineStatus.STOPPED

    async def test_engine_execute(self, gate_engine: QualityGateEngine):
        result = await gate_engine.execute({
            "gate": {
                "id": "g1", "name": "Test",
                "checks": [{"name": "c1", "field": "x", "operator": "eq", "expected": 1}],
                "threshold": 1.0,
            },
            "data": {"x": 1},
        })
        assert result["passed"] is True
        assert result["verdict"] == "pass"


# =============================================================================
# ReasoningEngine
# =============================================================================


class TestReasoningEngine:
    async def test_internal_source_preferred(self, reasoning_engine: ReasoningEngine):
        """Governance questions should prefer internal KB (higher confidence)."""
        result = await reasoning_engine.query("What is the governance policy?")
        assert result.answer
        assert result.decision in ("internal", "hybrid")
        assert result.internal_confidence > 0
        assert len(result.trail) > 0

    async def test_external_only_topic(self, reasoning_engine: ReasoningEngine):
        """Incident questions only exist in external KB."""
        result = await reasoning_engine.query("How to handle an incident?")
        assert result.decision == "external"
        assert result.external_confidence > 0
        assert "incident" in result.answer.lower() or "incident" in result.external_answer.lower()

    async def test_no_match_rejects(self, reasoning_engine: ReasoningEngine):
        """A question with no matching keywords should be rejected."""
        result = await reasoning_engine.query("What is the meaning of life?")
        assert result.decision == "reject"
        assert "unable" in result.answer.lower() or "confident" in result.answer.lower()

    async def test_hybrid_decision(self):
        """When both sources have similar confidence, use HYBRID."""
        engine = ReasoningEngine(
            internal_kb={"test": ("Internal answer about test.", 0.80)},
            external_kb={"test": ("External answer about test.", 0.82)},
        )
        result = await engine.query("Tell me about test")
        # Confidence diff = 0.02 < 0.1, so should be hybrid
        assert result.decision == "hybrid"
        assert "Internal answer" in result.answer
        assert "external answer" in result.answer.lower()

    async def test_decision_trail_populated(self, reasoning_engine: ReasoningEngine):
        result = await reasoning_engine.query("What about security?")
        assert len(result.trail) >= 3  # at least internal, external, arbitration steps
        assert any("[internal]" in step for step in result.trail)
        assert any("[external]" in step for step in result.trail)
        assert any("[arbitration]" in step for step in result.trail)

    async def test_custom_knowledge_base(self):
        engine = ReasoningEngine(
            internal_kb={"custom": ("Custom internal answer.", 0.95)},
            external_kb={},
        )
        result = await engine.query("Tell me about custom topic")
        assert result.decision == "internal"
        assert result.answer == "Custom internal answer."

    async def test_confidence_threshold(self):
        """Low-confidence sources should be rejected."""
        engine = ReasoningEngine(
            internal_kb={"topic": ("Low confidence answer.", 0.2)},
            external_kb={},
            confidence_threshold=0.5,
        )
        result = await engine.query("What about this topic?")
        assert result.decision == "reject"

    async def test_add_knowledge(self, reasoning_engine: ReasoningEngine):
        reasoning_engine.add_internal_knowledge("pandas", "Pandas is a data library.", 0.9)
        result = await reasoning_engine.query("Tell me about pandas")
        assert result.decision == "internal"
        assert "Pandas" in result.answer


class TestReasoningEngineProtocol:
    def test_engine_name(self, reasoning_engine: ReasoningEngine):
        assert reasoning_engine.name == "reasoning-engine"

    async def test_engine_lifecycle(self, reasoning_engine: ReasoningEngine):
        await reasoning_engine.start()
        assert reasoning_engine.status == EngineStatus.RUNNING
        await reasoning_engine.stop()
        assert reasoning_engine.status == EngineStatus.STOPPED

    async def test_engine_execute(self, reasoning_engine: ReasoningEngine):
        result = await reasoning_engine.execute({"question": "Tell me about governance"})
        assert result["answer"]
        assert result["query_id"]
        assert result["decision"]
        assert result["trail"]

    async def test_reasoning_history(self, reasoning_engine: ReasoningEngine):
        await reasoning_engine.query("governance question")
        assert len(reasoning_engine.reasoning_history) == 1
