"""Unit tests for yaml-toolkit CLI (generate, validate, lint, convert)."""
import os
import json
import subprocess
import tempfile
import pytest

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
CLI = os.path.join(REPO_ROOT, "tools", "yaml-toolkit", "bin", "cli.js")


def run_cli(*args, check=True):
    result = subprocess.run(
        ["node", CLI, *args],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=15,
    )
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode, result.args, result.stdout, result.stderr
        )
    return result


class TestYAMLToolkitHelp:
    def test_help_output(self):
        r = run_cli()
        assert "YAML Toolkit" in r.stdout
        assert "gen" in r.stdout
        assert "validate" in r.stdout
        assert "lint" in r.stdout
        assert "convert" in r.stdout


class TestYAMLToolkitGenerate:
    def test_generate_deployment(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "module.json")
            with open(input_path, "w") as f:
                json.dump({
                    "name": "eco-pytest-svc",
                    "kind": "Deployment",
                    "namespace": "indestructibleeco",
                    "image": "ghcr.io/indestructibleorg/test:1.0.0",
                    "ports": [8080],
                    "depends_on": ["redis"],
                    "health_check": "/health",
                }, f)
            out_dir = os.path.join(tmpdir, "out")
            r = run_cli("gen", f"--input={input_path}", f"--output={out_dir}")
            assert "valid=true" in r.stdout
            qyaml_path = os.path.join(out_dir, "eco-pytest-svc.qyaml")
            assert os.path.isfile(qyaml_path)
            content = open(qyaml_path).read()
            assert "document_metadata:" in content
            assert "governance_info:" in content
            assert "registry_binding:" in content
            assert "vector_alignment_map:" in content
            assert "schema_version: v8" in content
            assert "yaml-toolkit-v8" in content

    def test_generate_fails_without_input(self):
        r = run_cli("gen", check=False)
        assert r.returncode != 0


class TestYAMLToolkitValidate:
    def test_validate_existing_qyaml(self):
        qyaml = os.path.join(REPO_ROOT, "k8s", "base", "api-gateway.qyaml")
        if os.path.isfile(qyaml):
            r = run_cli("validate", qyaml)
            assert "valid=true" in r.stdout

    def test_validate_all_base_qyaml(self):
        base_dir = os.path.join(REPO_ROOT, "k8s", "base")
        for f in os.listdir(base_dir):
            if f.endswith(".qyaml"):
                r = run_cli("validate", os.path.join(base_dir, f))
                assert "valid=true" in r.stdout, f"{f} should be valid"


class TestYAMLToolkitLint:
    def test_lint_k8s_base(self):
        r = run_cli("lint", os.path.join(REPO_ROOT, "k8s", "base"))
        assert "Linted" in r.stdout
        assert "PASS" in r.stdout

    def test_lint_backend_k8s(self):
        r = run_cli("lint", os.path.join(REPO_ROOT, "backend", "k8s"))
        assert "Linted" in r.stdout


class TestYAMLToolkitConvert:
    def test_convert_strips_governance(self):
        qyaml = os.path.join(REPO_ROOT, "k8s", "base", "namespace.qyaml")
        if not os.path.isfile(qyaml):
            pytest.skip("namespace.qyaml not found")
        with tempfile.TemporaryDirectory() as tmpdir:
            r = run_cli("convert", qyaml, f"--output={tmpdir}")
            assert "Converted:" in r.stdout
            yaml_path = os.path.join(tmpdir, "namespace.yaml")
            assert os.path.isfile(yaml_path)
            content = open(yaml_path).read()
            assert "document_metadata:" not in content
            assert "governance_info:" not in content
            assert "registry_binding:" not in content
            assert "vector_alignment_map:" not in content
            # Should still have K8s content
            assert "apiVersion:" in content or "kind:" in content

    def test_convert_api_gateway(self):
        qyaml = os.path.join(REPO_ROOT, "k8s", "base", "api-gateway.qyaml")
        if not os.path.isfile(qyaml):
            pytest.skip("api-gateway.qyaml not found")
        with tempfile.TemporaryDirectory() as tmpdir:
            r = run_cli("convert", qyaml, f"--output={tmpdir}")
            assert "Converted:" in r.stdout
            yaml_path = os.path.join(tmpdir, "api-gateway.yaml")
            content = open(yaml_path).read()
            assert "Deployment" in content
            assert "document_metadata:" not in content
