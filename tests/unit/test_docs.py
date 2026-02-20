"""Unit tests for documentation (Step 35)."""
import os
import pytest

DOCS = os.path.join(os.path.dirname(__file__), "..", "..", "docs")


class TestDocumentation:
    def test_api_doc_exists(self):
        assert os.path.isfile(os.path.join(DOCS, "API.md"))

    def test_architecture_doc_exists(self):
        assert os.path.isfile(os.path.join(DOCS, "ARCHITECTURE.md"))

    def test_deployment_doc_exists(self):
        assert os.path.isfile(os.path.join(DOCS, "DEPLOYMENT.md"))

    def test_api_has_endpoints(self):
        content = open(os.path.join(DOCS, "API.md")).read()
        assert "/v1/chat/completions" in content
        assert "/v1/models" in content
        assert "/health" in content

    def test_architecture_has_layers(self):
        content = open(os.path.join(DOCS, "ARCHITECTURE.md")).read()
        assert "Layer 0" in content
        assert "Layer 5" in content

    def test_architecture_has_engines(self):
        content = open(os.path.join(DOCS, "ARCHITECTURE.md")).read()
        for engine in ["vLLM", "TGI", "Ollama", "SGLang"]:
            assert engine in content

    def test_deployment_has_helm(self):
        content = open(os.path.join(DOCS, "DEPLOYMENT.md")).read()
        assert "helm install" in content

    def test_deployment_has_argocd(self):
        content = open(os.path.join(DOCS, "DEPLOYMENT.md")).read()
        assert "Argo CD" in content
        assert "applicationset" in content.lower()
