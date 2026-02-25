"""Test governance evidence domain entity."""

from domain.entities.evidence import Evidence, EvidenceType


def test_evidence_creation_via_factory():
    e = Evidence.create(
        cycle_id="cycle-001",
        module_id="mod-auth",
        evidence_type=EvidenceType.SCAN_RESULT,
        payload={"rule": "naming", "passed": True},
    )
    assert e.cycle_id == "cycle-001"
    assert e.module_id == "mod-auth"
    assert e.evidence_type == EvidenceType.SCAN_RESULT
    assert e.chain_previous_hash is None
    assert len(e.content_hash) == 64


def test_evidence_immutability():
    e = Evidence.create(
        cycle_id="cycle-002",
        module_id="mod-api",
        evidence_type=EvidenceType.COMPLIANCE_CHECK,
        payload={"score": 95},
    )
    try:
        e.cycle_id = "tampered"  # type: ignore
        assert False, "Should have raised ValidationError"
    except Exception:
        pass


def test_evidence_content_hash_deterministic():
    payload = {"key": "value", "nested": {"a": 1}}
    e1 = Evidence.create(
        cycle_id="c1", module_id="m1",
        evidence_type=EvidenceType.GATE_DECISION,
        payload=payload,
    )
    e2 = Evidence.create(
        cycle_id="c1", module_id="m1",
        evidence_type=EvidenceType.GATE_DECISION,
        payload=payload,
    )
    assert e1.content_hash == e2.content_hash


def test_evidence_integrity_verification():
    e = Evidence.create(
        cycle_id="c1", module_id="m1",
        evidence_type=EvidenceType.REMEDIATION_ACTION,
        payload={"action": "fix-naming"},
    )
    assert e.verify_integrity() is True


def test_evidence_chain_entry():
    e = Evidence.create(
        cycle_id="c1", module_id="m1",
        evidence_type=EvidenceType.POLICY_CHANGE,
        payload={"policy": "v2"},
    )
    entry = e.to_chain_entry()
    assert "chain_hash" in entry
    assert entry["evidence_type"] == "policy_change"
    assert entry["cycle_id"] == "c1"


def test_evidence_chain_sequence_valid():
    e1 = Evidence.create(
        cycle_id="c1", module_id="m1",
        evidence_type=EvidenceType.SCAN_RESULT,
        payload={"step": 1},
        previous_hash=None,
    )
    e2 = Evidence.create(
        cycle_id="c1", module_id="m1",
        evidence_type=EvidenceType.COMPLIANCE_CHECK,
        payload={"step": 2},
        previous_hash=e1.content_hash,
    )
    assert Evidence.verify_chain_sequence([e1, e2]) is True


def test_evidence_chain_sequence_broken():
    e1 = Evidence.create(
        cycle_id="c1", module_id="m1",
        evidence_type=EvidenceType.SCAN_RESULT,
        payload={"step": 1},
    )
    e2 = Evidence.create(
        cycle_id="c1", module_id="m1",
        evidence_type=EvidenceType.COMPLIANCE_CHECK,
        payload={"step": 2},
        previous_hash="0000000000000000000000000000000000000000000000000000000000000000",
    )
    assert Evidence.verify_chain_sequence([e1, e2]) is False


def test_evidence_chain_sequence_empty():
    assert Evidence.verify_chain_sequence([]) is True


def test_evidence_summary():
    e = Evidence.create(
        cycle_id="c1", module_id="m1",
        evidence_type=EvidenceType.DRIFT_DETECTION,
        payload={"drift": True},
    )
    s = e.summary()
    assert s["cycle_id"] == "c1"
    assert s["type"] == "drift_detection"
    assert "evidence_id" in s


def test_evidence_type_values():
    assert EvidenceType.SCAN_RESULT.value == "scan_result"
    assert EvidenceType.COMPLIANCE_CHECK.value == "compliance_check"
    assert EvidenceType.REMEDIATION_ACTION.value == "remediation_action"
    assert EvidenceType.GATE_DECISION.value == "gate_decision"
    assert EvidenceType.POLICY_CHANGE.value == "policy_change"
    assert EvidenceType.DRIFT_DETECTION.value == "drift_detection"
    assert EvidenceType.MANUAL_ATTESTATION.value == "manual_attestation"
    assert EvidenceType.APPROVAL_RECORD.value == "approval_record"
    assert EvidenceType.CONFIGURATION_SNAPSHOT.value == "configuration_snapshot"
