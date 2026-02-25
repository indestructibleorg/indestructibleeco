"""Test governance module domain entity."""

import pytest

from domain.entities.governance_module import GovernanceModule
from domain.value_objects.compliance_status import ComplianceScore, ComplianceStatus


def test_module_creation():
    m = GovernanceModule(
        name="auth-service",
        path="/platforms/auth",
        gl_layer="GL30-49",
        ng_era="Era-2",
    )
    assert m.name == "auth-service"
    assert m.gl_layer == "GL30-49"
    assert m.ng_era == "Era-2"
    assert m.compliance_status == ComplianceStatus.UNKNOWN
    assert m.bindings == []


def test_module_is_compliant():
    m = GovernanceModule(
        name="core-lib",
        path="/libs/core",
        gl_layer="GL10-29",
        ng_era="Era-1",
        compliance_status=ComplianceStatus.COMPLIANT,
    )
    assert m.is_compliant() is True


def test_module_exempt_is_compliant():
    m = GovernanceModule(
        name="legacy",
        path="/libs/legacy",
        gl_layer="GL00-09",
        ng_era="Era-1",
        compliance_status=ComplianceStatus.EXEMPT,
    )
    assert m.is_compliant() is True


def test_module_non_compliant():
    m = GovernanceModule(
        name="api-gw",
        path="/services/api",
        gl_layer="GL30-49",
        ng_era="Era-2",
        compliance_status=ComplianceStatus.NON_COMPLIANT,
    )
    assert m.is_compliant() is False
    assert m.needs_remediation() is True


def test_module_partially_compliant_needs_remediation():
    m = GovernanceModule(
        name="worker",
        path="/services/worker",
        gl_layer="GL30-49",
        ng_era="Era-2",
        compliance_status=ComplianceStatus.PARTIALLY_COMPLIANT,
    )
    assert m.is_compliant() is False
    assert m.needs_remediation() is True


def test_module_update_hash_valid():
    m = GovernanceModule(
        name="svc",
        path="/svc",
        gl_layer="GL10-29",
        ng_era="Era-1",
    )
    valid_hash = "a" * 64
    m.update_hash(valid_hash)
    assert m.hash_signature == valid_hash


def test_module_update_hash_invalid_length():
    m = GovernanceModule(
        name="svc",
        path="/svc",
        gl_layer="GL10-29",
        ng_era="Era-1",
    )
    with pytest.raises(ValueError, match="Invalid SHA-256 hash"):
        m.update_hash("short")


def test_module_update_hash_invalid_chars():
    m = GovernanceModule(
        name="svc",
        path="/svc",
        gl_layer="GL10-29",
        ng_era="Era-1",
    )
    with pytest.raises(ValueError, match="Invalid SHA-256 hash"):
        m.update_hash("g" * 64)


def test_module_compute_hash():
    m = GovernanceModule(
        name="svc",
        path="/svc",
        gl_layer="GL10-29",
        ng_era="Era-1",
    )
    digest = m.compute_hash(b"hello world")
    assert len(digest) == 64
    assert m.hash_signature == digest


def test_module_mark_scanned():
    m = GovernanceModule(
        name="svc",
        path="/svc",
        gl_layer="GL10-29",
        ng_era="Era-1",
    )
    score = ComplianceScore(score=95.0)
    m.mark_scanned(ComplianceStatus.COMPLIANT, score=score)
    assert m.compliance_status == ComplianceStatus.COMPLIANT
    assert m.last_scan_at is not None
    assert m.metadata["last_score"]["score"] == 95.0


def test_module_bindings():
    m = GovernanceModule(
        name="svc",
        path="/svc",
        gl_layer="GL10-29",
        ng_era="Era-1",
    )
    m.add_binding("policy-001")
    m.add_binding("policy-002")
    m.add_binding("policy-001")  # idempotent
    assert len(m.bindings) == 2

    removed = m.remove_binding("policy-001")
    assert removed is True
    assert len(m.bindings) == 1

    removed = m.remove_binding("nonexistent")
    assert removed is False


def test_module_summary():
    m = GovernanceModule(
        name="svc",
        path="/svc",
        gl_layer="GL10-29",
        ng_era="Era-1",
    )
    s = m.summary()
    assert s["name"] == "svc"
    assert s["gl_layer"] == "GL10-29"
    assert s["compliance"] == "unknown"
    assert s["binding_count"] == 0
