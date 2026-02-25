"""Test fixtures for governance platform tests."""

from __future__ import annotations

import pytest

from governance_platform.domain.entities import (
    GateCheck,
    Policy,
    PolicyRule,
    QualityGate,
)
from governance_platform.domain.value_objects import PolicySeverity
from governance_platform.engines.policy_engine import PolicyEngine
from governance_platform.engines.quality_gate_engine import QualityGateEngine
from governance_platform.engines.reasoning_engine import ReasoningEngine


# -- Policy Engine fixtures ----------------------------------------------------


@pytest.fixture
def policy_engine() -> PolicyEngine:
    return PolicyEngine()


@pytest.fixture
def sample_policy() -> Policy:
    """A policy that requires environment=production and version >= 2.0."""
    return Policy(
        id="pol-test-001",
        name="Production Readiness",
        rules=[
            PolicyRule(field="environment", operator="eq", value="production"),
            PolicyRule(field="version", operator="gt", value="1.0"),
        ],
        severity=PolicySeverity.HIGH,
    )


@pytest.fixture
def strict_security_policy() -> Policy:
    """Policy checking security fields."""
    return Policy(
        id="pol-sec-001",
        name="Security Compliance",
        rules=[
            PolicyRule(field="encryption", operator="eq", value=True),
            PolicyRule(field="auth_method", operator="ne", value="none"),
            PolicyRule(field="allowed_ips", operator="contains", value="10.0.0.0/8"),
        ],
        severity=PolicySeverity.CRITICAL,
    )


# -- Quality Gate fixtures -----------------------------------------------------


@pytest.fixture
def gate_engine() -> QualityGateEngine:
    return QualityGateEngine()


@pytest.fixture
def sample_gate() -> QualityGate:
    """A quality gate with coverage and test checks."""
    return QualityGate(
        id="gate-test-001",
        name="Release Quality Gate",
        checks=[
            GateCheck(name="coverage", field="coverage_pct", operator="gte", expected=80.0),
            GateCheck(name="tests_passed", field="tests_passed", operator="eq", expected=True),
            GateCheck(name="no_criticals", field="critical_issues", operator="eq", expected=0),
        ],
        threshold=1.0,
    )


@pytest.fixture
def lenient_gate() -> QualityGate:
    """A gate that only requires 2/3 checks to pass (threshold=0.66)."""
    return QualityGate(
        id="gate-test-002",
        name="Lenient Gate",
        checks=[
            GateCheck(name="has_readme", field="readme", operator="not_empty", expected=None),
            GateCheck(name="has_tests", field="test_count", operator="gt", expected=0),
            GateCheck(name="lint_clean", field="lint_errors", operator="eq", expected=0),
        ],
        threshold=0.66,
    )


# -- Reasoning Engine fixtures -------------------------------------------------


@pytest.fixture
def reasoning_engine() -> ReasoningEngine:
    return ReasoningEngine()
