"""Test evidence domain entity."""

from domain.entities.evidence import Evidence


def test_evidence_creation():
    e = Evidence(
        violation_type="CRITICAL",
        violation_description="Hash chain broken",
        affected_system="hash-verifier",
        detection_method="STATIC",
        confidence_score=1.0,
        collected_by="COMP-BE-6",
    )
    assert e.collected_by == "COMP-BE-6"
    assert e.confidence_score == 1.0


def test_evidence_immutability():
    e = Evidence(
        violation_type="HIGH",
        violation_description="Narrative language detected",
        affected_system="scanner",
        detection_method="SEMANTIC",
        confidence_score=0.95,
        collected_by="COMP-BE-1",
    )
    # Evidence is frozen dataclass
    try:
        e.violation_type = "LOW"  # type: ignore
        assert False, "Should have raised FrozenInstanceError"
    except AttributeError:
        pass


def test_evidence_hash_deterministic():
    e = Evidence(
        id="test-id-123",
        violation_type="MEDIUM",
        violation_description="Test description",
        affected_system="test-system",
        detection_method="RUNTIME",
        confidence_score=0.75,
        collected_by="test-collector",
    )
    hash1 = e.evidence_hash
    hash2 = e.evidence_hash
    assert hash1 == hash2
    assert len(hash1) == 64
