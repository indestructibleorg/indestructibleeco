"""Test evidence record domain entity."""

from domain.entities.evidence_record import EvidenceRecord, EvidenceState


def test_evidence_record_creation():
    r = EvidenceRecord(
        source="evidence-collector",
        payload={"key": "value", "count": 42},
    )
    assert r.state == EvidenceState.INGESTED
    assert r.source == "evidence-collector"
    assert r.payload == {"key": "value", "count": 42}
    assert r.chain_parent_hash is None
    assert r.sealed_at is None


def test_evidence_hash_deterministic():
    r = EvidenceRecord(
        id="test-id-001",
        source="collector",
        payload={"msg": "deterministic"},
    )
    hash1 = r.evidence_hash
    hash2 = r.evidence_hash
    assert hash1 == hash2
    assert len(hash1) == 128  # SHA3-512 hex digest


def test_evidence_hash_differs_by_id():
    r1 = EvidenceRecord(id="id-a", source="s", payload={"x": 1})
    r2 = EvidenceRecord(id="id-b", source="s", payload={"x": 1})
    assert r1.evidence_hash != r2.evidence_hash


def test_evidence_is_sealed():
    r = EvidenceRecord(source="s", payload={})
    assert r.is_sealed is False
    r.state = EvidenceState.SEALED
    assert r.is_sealed is True


def test_evidence_is_terminal():
    r = EvidenceRecord(source="s", payload={})
    assert r.is_terminal is False

    for state in (EvidenceState.SEALED, EvidenceState.ARCHIVED, EvidenceState.REJECTED):
        r.state = state
        assert r.is_terminal is True

    for state in (EvidenceState.INGESTED, EvidenceState.VALIDATING, EvidenceState.VERIFIED):
        r.state = state
        assert r.is_terminal is False


def test_evidence_state_enum_values():
    assert EvidenceState.INGESTED.value == "INGESTED"
    assert EvidenceState.VALIDATING.value == "VALIDATING"
    assert EvidenceState.VERIFIED.value == "VERIFIED"
    assert EvidenceState.SEALED.value == "SEALED"
    assert EvidenceState.ARCHIVED.value == "ARCHIVED"
    assert EvidenceState.REJECTED.value == "REJECTED"
