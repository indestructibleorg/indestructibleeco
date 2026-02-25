"""Test compliance status and severity value objects."""

import pytest

from domain.value_objects.compliance_status import ComplianceScore, ComplianceStatus
from domain.value_objects.severity import Severity, SeverityThreshold


# --- ComplianceStatus ---


def test_compliance_status_is_passing():
    assert ComplianceStatus.COMPLIANT.is_passing is True
    assert ComplianceStatus.EXEMPT.is_passing is True
    assert ComplianceStatus.NON_COMPLIANT.is_passing is False
    assert ComplianceStatus.PARTIALLY_COMPLIANT.is_passing is False
    assert ComplianceStatus.UNKNOWN.is_passing is False


def test_compliance_status_requires_action():
    assert ComplianceStatus.NON_COMPLIANT.requires_action is True
    assert ComplianceStatus.PARTIALLY_COMPLIANT.requires_action is True
    assert ComplianceStatus.COMPLIANT.requires_action is False
    assert ComplianceStatus.EXEMPT.requires_action is False
    assert ComplianceStatus.UNKNOWN.requires_action is False


def test_compliance_status_from_score():
    assert ComplianceStatus.from_score(95.0) == ComplianceStatus.COMPLIANT
    assert ComplianceStatus.from_score(90.0) == ComplianceStatus.COMPLIANT
    assert ComplianceStatus.from_score(75.0) == ComplianceStatus.PARTIALLY_COMPLIANT
    assert ComplianceStatus.from_score(60.0) == ComplianceStatus.PARTIALLY_COMPLIANT
    assert ComplianceStatus.from_score(59.9) == ComplianceStatus.NON_COMPLIANT
    assert ComplianceStatus.from_score(0.0) == ComplianceStatus.NON_COMPLIANT


# --- ComplianceScore ---


def test_compliance_score_auto_grade():
    assert ComplianceScore(score=95.0).grade == "A"
    assert ComplianceScore(score=85.0).grade == "B"
    assert ComplianceScore(score=75.0).grade == "C"
    assert ComplianceScore(score=65.0).grade == "D"
    assert ComplianceScore(score=50.0).grade == "F"


def test_compliance_score_explicit_grade():
    s = ComplianceScore(score=50.0, grade="X")
    assert s.grade == "X"


def test_compliance_score_invalid_bounds():
    with pytest.raises(ValueError, match="between 0 and 100"):
        ComplianceScore(score=-1.0)
    with pytest.raises(ValueError, match="between 0 and 100"):
        ComplianceScore(score=101.0)


def test_compliance_score_status():
    assert ComplianceScore(score=95.0).status == ComplianceStatus.COMPLIANT
    assert ComplianceScore(score=75.0).status == ComplianceStatus.PARTIALLY_COMPLIANT
    assert ComplianceScore(score=40.0).status == ComplianceStatus.NON_COMPLIANT


def test_compliance_score_is_passing():
    assert ComplianceScore(score=95.0).is_passing is True
    assert ComplianceScore(score=50.0).is_passing is False


def test_compliance_score_meets_threshold():
    s = ComplianceScore(score=80.0)
    assert s.meets_threshold(75.0) is True
    assert s.meets_threshold(80.0) is True
    assert s.meets_threshold(85.0) is False


def test_compliance_score_meets_threshold_invalid():
    s = ComplianceScore(score=50.0)
    with pytest.raises(ValueError, match="between 0 and 100"):
        s.meets_threshold(-1.0)


def test_compliance_score_delta():
    s1 = ComplianceScore(score=90.0)
    s2 = ComplianceScore(score=70.0)
    assert s1.delta(s2) == 20.0
    assert s2.delta(s1) == -20.0


def test_compliance_score_with_details():
    s = ComplianceScore(score=80.0, details={"rule_a": 90})
    s2 = s.with_details(rule_b=70)
    assert s2.details == {"rule_a": 90, "rule_b": 70}
    assert s2.score == 80.0


def test_compliance_score_to_dict():
    d = ComplianceScore(score=95.0).to_dict()
    assert d["score"] == 95.0
    assert d["grade"] == "A"
    assert d["is_passing"] is True


# --- Severity ---


def test_severity_ordering():
    assert Severity.CRITICAL > Severity.HIGH
    assert Severity.HIGH > Severity.MEDIUM
    assert Severity.MEDIUM > Severity.LOW
    assert Severity.LOW > Severity.INFO


def test_severity_is_actionable():
    assert Severity.CRITICAL.is_actionable is True
    assert Severity.HIGH.is_actionable is True
    assert Severity.MEDIUM.is_actionable is True
    assert Severity.LOW.is_actionable is False
    assert Severity.INFO.is_actionable is False


def test_severity_is_blocking():
    assert Severity.CRITICAL.is_blocking is True
    assert Severity.HIGH.is_blocking is True
    assert Severity.MEDIUM.is_blocking is False
    assert Severity.LOW.is_blocking is False


def test_severity_from_string():
    assert Severity.from_string("CRITICAL") == Severity.CRITICAL
    assert Severity.from_string("high") == Severity.HIGH
    assert Severity.from_string("  Medium  ") == Severity.MEDIUM


def test_severity_from_string_invalid():
    with pytest.raises(ValueError, match="Unknown severity"):
        Severity.from_string("FATAL")


# --- SeverityThreshold ---


def test_threshold_is_relevant():
    t = SeverityThreshold(minimum_severity=Severity.MEDIUM)
    assert t.is_relevant(Severity.CRITICAL) is True
    assert t.is_relevant(Severity.MEDIUM) is True
    assert t.is_relevant(Severity.LOW) is False
    assert t.is_relevant(Severity.INFO) is False


def test_threshold_exceeds():
    t = SeverityThreshold(
        minimum_severity=Severity.LOW,
        max_counts={Severity.CRITICAL: 0, Severity.HIGH: 2},
    )
    assert t.exceeds(Severity.CRITICAL, 1) is True
    assert t.exceeds(Severity.HIGH, 2) is False
    assert t.exceeds(Severity.HIGH, 3) is True
    assert t.exceeds(Severity.LOW, 100) is False  # no cap


def test_threshold_evaluate_counts():
    t = SeverityThreshold(
        minimum_severity=Severity.LOW,
        max_counts={Severity.CRITICAL: 0, Severity.HIGH: 5},
    )
    assert t.evaluate_counts({Severity.CRITICAL: 0, Severity.HIGH: 3}) is True
    assert t.evaluate_counts({Severity.CRITICAL: 1}) is False


def test_threshold_failing_severities():
    t = SeverityThreshold(
        minimum_severity=Severity.LOW,
        max_counts={Severity.CRITICAL: 0, Severity.HIGH: 1},
    )
    failing = t.failing_severities({Severity.CRITICAL: 1, Severity.HIGH: 5})
    assert Severity.CRITICAL in failing
    assert Severity.HIGH in failing


def test_threshold_with_max():
    t = SeverityThreshold(minimum_severity=Severity.LOW)
    t2 = t.with_max(Severity.CRITICAL, 0)
    assert t2.max_counts[Severity.CRITICAL] == 0
    assert t.max_counts == {}


def test_threshold_invalid_max_count():
    with pytest.raises(ValueError, match="non-negative"):
        SeverityThreshold(max_counts={Severity.HIGH: -1})


def test_threshold_to_dict():
    t = SeverityThreshold(
        minimum_severity=Severity.MEDIUM,
        max_counts={Severity.CRITICAL: 0},
    )
    d = t.to_dict()
    assert d["minimum_severity"] == "medium"
    assert d["max_counts"]["critical"] == 0
