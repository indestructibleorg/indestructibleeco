"""Test violation domain entity."""

from domain.entities.violation import (
    DetectionMethod,
    Violation,
    ViolationSeverity,
    ViolationStatus,
)


def test_violation_creation():
    v = Violation(
        violation_type="HASH_POLICY",
        severity=ViolationSeverity.CRITICAL,
        description="SHA3-512 hash mismatch detected",
        affected_system="evidence-collector",
        detection_method=DetectionMethod.STATIC,
        confidence_score=0.99,
    )
    assert v.status == ViolationStatus.DETECTED
    assert v.severity == ViolationSeverity.CRITICAL
    assert v.is_blocking is True


def test_violation_evidence_hash():
    v = Violation(
        violation_type="HASH_POLICY",
        severity=ViolationSeverity.LOW,
        description="Minor formatting issue",
        affected_system="formatter",
        detection_method=DetectionMethod.SEMANTIC,
        confidence_score=0.5,
    )
    assert len(v.evidence_hash) == 64  # SHA-256 hex digest
    assert v.is_blocking is False


def test_violation_non_blocking_medium():
    v = Violation(
        violation_type="NAMING",
        severity=ViolationSeverity.MEDIUM,
        description="Non-canonical naming",
        affected_system="scanner",
        detection_method=DetectionMethod.STATIC,
        confidence_score=0.8,
    )
    assert v.is_blocking is False
