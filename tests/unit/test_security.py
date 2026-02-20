"""Unit tests for security hardening (Step 34)."""
import json
import os
import pytest
import yaml

TRIVY = os.path.join(os.path.dirname(__file__), "..", "..", ".trivy.yaml")
QYAML_POLICY = os.path.join(os.path.dirname(__file__), "..", "..", "policy", "qyaml_governance.rego")
DOCKERFILE_POLICY = os.path.join(os.path.dirname(__file__), "..", "..", "policy", "dockerfile.rego")
SBOM = os.path.join(os.path.dirname(__file__), "..", "..", "sbom.json")


class TestTrivyConfig:
    def test_file_exists(self):
        assert os.path.isfile(TRIVY)

    def test_valid_yaml(self):
        with open(TRIVY) as f:
            data = yaml.safe_load(f)
        assert "severity" in data

    def test_scans_critical_and_high(self):
        with open(TRIVY) as f:
            data = yaml.safe_load(f)
        assert "CRITICAL" in data["severity"]
        assert "HIGH" in data["severity"]


class TestOPAPolicies:
    def test_qyaml_policy_exists(self):
        assert os.path.isfile(QYAML_POLICY)

    def test_qyaml_policy_has_deny_rules(self):
        content = open(QYAML_POLICY).read()
        assert "deny[msg]" in content

    def test_qyaml_checks_governance_blocks(self):
        content = open(QYAML_POLICY).read()
        for block in ["document_metadata", "governance_info", "registry_binding", "vector_alignment_map"]:
            assert block in content

    def test_qyaml_checks_uri_format(self):
        content = open(QYAML_POLICY).read()
        assert "indestructibleeco://" in content

    def test_qyaml_checks_image_registry(self):
        content = open(QYAML_POLICY).read()
        assert "ghcr.io/indestructibleorg/" in content

    def test_dockerfile_policy_exists(self):
        assert os.path.isfile(DOCKERFILE_POLICY)


class TestSBOM:
    def test_file_exists(self):
        assert os.path.isfile(SBOM)

    def test_valid_json(self):
        with open(SBOM) as f:
            data = json.load(f)
        assert data["bomFormat"] == "CycloneDX"

    def test_has_components(self):
        with open(SBOM) as f:
            data = json.load(f)
        assert len(data["components"]) >= 10

    def test_components_have_purl(self):
        with open(SBOM) as f:
            data = json.load(f)
        for comp in data["components"]:
            assert "purl" in comp, f"Component {comp['name']} missing purl"
