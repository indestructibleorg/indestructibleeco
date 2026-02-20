"""Unit tests for Governance Engine — YAML parsing + persistent audit."""
import json
import os
import sys
import tempfile
import uuid

import pytest
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.ai.src.governance import GovernanceEngine, AuditPersistence, _deep_values


@pytest.fixture
def tmp_audit_dir(tmp_path):
    return str(tmp_path / "audit")


@pytest.fixture
def engine(tmp_audit_dir):
    e = GovernanceEngine(audit_dir=tmp_audit_dir, persist=True)
    yield e
    e.close()


@pytest.fixture
def engine_no_persist():
    e = GovernanceEngine(persist=False)
    yield e


def _make_valid_qyaml():
    """Generate a fully compliant .qyaml string."""
    uid = uuid.uuid1()
    doc = {
        "document_metadata": {
            "unique_id": str(uid),
            "uri": f"indestructibleeco://test/unit/{uid}",
            "urn": f"urn:indestructibleeco:test:unit:{uid}",
            "target_system": "gke-production",
            "schema_version": "v1",
            "generated_by": "yaml-toolkit-v1",
            "created_at": "2025-01-01T00:00:00Z",
        },
        "governance_info": {
            "owner": "platform-team",
            "compliance_tags": ["zero-trust"],
            "lifecycle_policy": "active",
        },
        "registry_binding": {
            "service_endpoint": "http://test.indestructibleeco.svc.cluster.local",
            "health_check_path": "/health",
        },
        "vector_alignment_map": {
            "alignment_model": "quantum-bert-xxl-v1",
            "coherence_vector_dim": 1024,
        },
    }
    return yaml.dump(doc, default_flow_style=False)


class TestValidateQyaml:
    def test_valid_document(self, engine):
        content = _make_valid_qyaml()
        result = engine.validate_qyaml(content)
        assert result["valid"] is True
        assert len([e for e in result["errors"] if e["severity"] == "error"]) == 0

    def test_missing_block(self, engine):
        doc = {
            "document_metadata": {
                "unique_id": str(uuid.uuid1()),
                "uri": "indestructibleeco://test",
                "urn": "urn:indestructibleeco:test",
                "target_system": "gke",
                "schema_version": "v1",
                "generated_by": "test",
                "created_at": "2025-01-01T00:00:00Z",
            },
            # missing governance_info, registry_binding, vector_alignment_map
        }
        result = engine.validate_qyaml(yaml.dump(doc))
        assert result["valid"] is False
        block_errors = [e for e in result["errors"] if "Missing mandatory" in e["message"]]
        assert len(block_errors) == 3

    def test_missing_metadata_fields(self, engine):
        doc = {
            "document_metadata": {"unique_id": str(uuid.uuid1())},
            "governance_info": {"owner": "t", "compliance_tags": [], "lifecycle_policy": "active"},
            "registry_binding": {"service_endpoint": "http://x", "health_check_path": "/h"},
            "vector_alignment_map": {"alignment_model": "m", "coherence_vector_dim": 128},
        }
        result = engine.validate_qyaml(yaml.dump(doc))
        assert result["valid"] is False
        field_errors = [e for e in result["errors"] if "Missing required field" in e["message"]]
        assert len(field_errors) >= 5  # uri, urn, target_system, schema_version, generated_by, created_at

    def test_invalid_uri_format(self, engine):
        doc = {
            "document_metadata": {
                "unique_id": str(uuid.uuid1()),
                "uri": "http://wrong-prefix",
                "urn": "urn:indestructibleeco:test",
                "target_system": "gke",
                "schema_version": "v1",
                "generated_by": "test",
                "created_at": "2025-01-01T00:00:00Z",
            },
            "governance_info": {"owner": "t", "compliance_tags": [], "lifecycle_policy": "active"},
            "registry_binding": {"service_endpoint": "http://x", "health_check_path": "/h"},
            "vector_alignment_map": {"alignment_model": "m", "coherence_vector_dim": 128},
        }
        result = engine.validate_qyaml(yaml.dump(doc))
        uri_errors = [e for e in result["errors"] if "URI must start with" in e["message"]]
        assert len(uri_errors) == 1

    def test_invalid_urn_format(self, engine):
        doc = {
            "document_metadata": {
                "unique_id": str(uuid.uuid1()),
                "uri": "indestructibleeco://test",
                "urn": "wrong:prefix:test",
                "target_system": "gke",
                "schema_version": "v1",
                "generated_by": "test",
                "created_at": "2025-01-01T00:00:00Z",
            },
            "governance_info": {"owner": "t", "compliance_tags": [], "lifecycle_policy": "active"},
            "registry_binding": {"service_endpoint": "http://x", "health_check_path": "/h"},
            "vector_alignment_map": {"alignment_model": "m", "coherence_vector_dim": 128},
        }
        result = engine.validate_qyaml(yaml.dump(doc))
        urn_errors = [e for e in result["errors"] if "URN must start with" in e["message"]]
        assert len(urn_errors) == 1

    def test_invalid_uuid(self, engine):
        doc = {
            "document_metadata": {
                "unique_id": "not-a-uuid",
                "uri": "indestructibleeco://test",
                "urn": "urn:indestructibleeco:test",
                "target_system": "gke",
                "schema_version": "v1",
                "generated_by": "test",
                "created_at": "2025-01-01T00:00:00Z",
            },
            "governance_info": {"owner": "t", "compliance_tags": [], "lifecycle_policy": "active"},
            "registry_binding": {"service_endpoint": "http://x", "health_check_path": "/h"},
            "vector_alignment_map": {"alignment_model": "m", "coherence_vector_dim": 128},
        }
        result = engine.validate_qyaml(yaml.dump(doc))
        uuid_errors = [e for e in result["errors"] if "not a valid UUID" in e["message"]]
        assert len(uuid_errors) == 1

    def test_uuid_v4_warning(self, engine):
        doc = {
            "document_metadata": {
                "unique_id": str(uuid.uuid4()),
                "uri": "indestructibleeco://test",
                "urn": "urn:indestructibleeco:test",
                "target_system": "gke",
                "schema_version": "v1",
                "generated_by": "test",
                "created_at": "2025-01-01T00:00:00Z",
            },
            "governance_info": {"owner": "t", "compliance_tags": [], "lifecycle_policy": "active"},
            "registry_binding": {"service_endpoint": "http://x", "health_check_path": "/h"},
            "vector_alignment_map": {"alignment_model": "m", "coherence_vector_dim": 128},
        }
        result = engine.validate_qyaml(yaml.dump(doc))
        v4_warnings = [e for e in result["errors"] if "UUID v1" in e["message"]]
        assert len(v4_warnings) == 1
        assert v4_warnings[0]["severity"] == "warning"

    def test_yaml_parse_error(self, engine):
        result = engine.validate_qyaml("{{invalid yaml: [")
        assert result["valid"] is False
        parse_errors = [e for e in result["errors"] if "YAML parse error" in e["message"]]
        assert len(parse_errors) >= 1

    def test_empty_document(self, engine):
        result = engine.validate_qyaml("")
        assert result["valid"] is False

    def test_gke_yaml_directive(self, engine):
        content = "%YAML 1.2\n---\nfoo: bar"
        result = engine.validate_qyaml(content)
        gke_errors = [e for e in result["errors"] if "GKE incompatible" in e["message"]]
        assert len(gke_errors) >= 1

    def test_governance_info_missing_fields(self, engine):
        doc = {
            "document_metadata": {
                "unique_id": str(uuid.uuid1()),
                "uri": "indestructibleeco://test",
                "urn": "urn:indestructibleeco:test",
                "target_system": "gke",
                "schema_version": "v1",
                "generated_by": "test",
                "created_at": "2025-01-01T00:00:00Z",
            },
            "governance_info": {},
            "registry_binding": {"service_endpoint": "http://x", "health_check_path": "/h"},
            "vector_alignment_map": {"alignment_model": "m", "coherence_vector_dim": 128},
        }
        result = engine.validate_qyaml(yaml.dump(doc))
        gov_errors = [e for e in result["errors"] if "governance_info" in e["path"]]
        assert len(gov_errors) >= 3


class TestStampGovernance:
    def test_stamp_has_all_blocks(self, engine):
        stamp = engine.stamp_governance("test-svc", "indestructibleeco", "Deployment")
        assert "document_metadata" in stamp
        assert "governance_info" in stamp
        assert "registry_binding" in stamp
        assert "vector_alignment_map" in stamp

    def test_stamp_uuid_v1(self, engine):
        stamp = engine.stamp_governance("test-svc")
        uid = uuid.UUID(stamp["document_metadata"]["unique_id"])
        assert uid.version == 1

    def test_stamp_uri_format(self, engine):
        stamp = engine.stamp_governance("test-svc", "ns1", "Service")
        assert stamp["document_metadata"]["uri"] == "indestructibleeco://k8s/ns1/service/test-svc"

    def test_stamp_urn_format(self, engine):
        stamp = engine.stamp_governance("test-svc", "ns1", "Service")
        assert stamp["document_metadata"]["urn"].startswith("urn:indestructibleeco:k8s:ns1:service:test-svc:")

    def test_stamp_roundtrip_validate(self, engine):
        stamp = engine.stamp_governance("roundtrip-svc")
        content = yaml.dump(stamp, default_flow_style=False)
        result = engine.validate_qyaml(content)
        assert result["valid"] is True


class TestResolveEngine:
    def test_resolve_vllm(self, engine):
        assert engine.resolve_engine("vllm-default") == "vllm_adapter"

    def test_resolve_ollama(self, engine):
        assert engine.resolve_engine("ollama-chat") == "ollama_adapter"

    def test_resolve_tgi(self, engine):
        assert engine.resolve_engine("tgi-large") == "tgi_adapter"

    def test_resolve_unknown_fallback(self, engine):
        result = engine.resolve_engine("unknown-model")
        assert result.endswith("_adapter")


class TestAuditLog:
    def test_audit_entries_created(self, engine):
        engine.resolve_engine("vllm-test")
        log = engine.get_audit_log()
        assert len(log) >= 1
        assert log[-1]["action"] == "engine_resolve"

    def test_audit_has_uuid_v1(self, engine):
        engine.resolve_engine("test")
        log = engine.get_audit_log()
        uid = uuid.UUID(log[-1]["id"])
        assert uid.version == 1

    def test_audit_has_uri(self, engine):
        engine.resolve_engine("test")
        log = engine.get_audit_log()
        assert log[-1]["uri"].startswith("indestructibleeco://governance/audit/")


class TestAuditPersistence:
    def test_persistence_creates_file(self, tmp_audit_dir):
        engine = GovernanceEngine(audit_dir=tmp_audit_dir, persist=True)
        engine.resolve_engine("test")
        engine.close()
        files = list(os.listdir(tmp_audit_dir))
        assert len(files) >= 1
        assert files[0].endswith(".jsonl")

    def test_persistence_writes_json_lines(self, tmp_audit_dir):
        engine = GovernanceEngine(audit_dir=tmp_audit_dir, persist=True)
        engine.resolve_engine("vllm-test")
        engine.validate_qyaml(_make_valid_qyaml())
        engine.close()
        files = list(os.listdir(tmp_audit_dir))
        fpath = os.path.join(tmp_audit_dir, files[0])
        with open(fpath, "r") as f:
            lines = f.readlines()
        assert len(lines) >= 2
        for line in lines:
            parsed = json.loads(line)
            assert "action" in parsed
            assert "timestamp" in parsed

    def test_no_persist_mode(self):
        engine = GovernanceEngine(persist=False)
        engine.resolve_engine("test")
        log = engine.get_audit_log()
        assert len(log) >= 1  # in-memory still works


class TestDeepValues:
    def test_flat_dict(self):
        assert set(_deep_values({"a": 1, "b": 2})) == {1, 2}

    def test_nested_dict(self):
        vals = _deep_values({"a": {"b": {"c": "deep"}}})
        assert "deep" in vals

    def test_list_in_dict(self):
        vals = _deep_values({"a": [1, 2, 3]})
        assert 1 in vals and 2 in vals and 3 in vals

    def test_empty(self):
        assert _deep_values({}) == []
