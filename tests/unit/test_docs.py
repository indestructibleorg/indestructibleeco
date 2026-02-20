"""Unit tests for documentation completeness and cross-references."""
import os
import pytest

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
DOCS = os.path.join(ROOT, "docs")


class TestDocumentationFiles:
    """Verify all documentation files exist and meet minimum size."""

    REQUIRED_DOCS = {
        "docs/API.md": 800,
        "docs/ARCHITECTURE.md": 250,
        "docs/DEPLOYMENT.md": 350,
        "docs/DEVELOPER_GUIDE.md": 200,
        "docs/ENV_REFERENCE.md": 120,
        "docs/QYAML_GOVERNANCE.md": 200,
        "docs/argocd-gitops-guide.md": 100,
        "docs/auto-repair-architecture.md": 100,
    }

    REQUIRED_ROOT = {
        "README.md": 100,
        "CONTRIBUTING.md": 100,
        "SECURITY.md": 30,
        "LICENSE": 10,
        ".env.example": 30,
    }

    @pytest.mark.parametrize("path,min_lines", list(REQUIRED_DOCS.items()))
    def test_doc_exists_and_size(self, path, min_lines):
        full = os.path.join(ROOT, path)
        assert os.path.isfile(full), f"Missing: {path}"
        lines = len(open(full, encoding="utf-8").readlines())
        assert lines >= min_lines, f"{path} has {lines} lines, expected >= {min_lines}"

    @pytest.mark.parametrize("path,min_lines", list(REQUIRED_ROOT.items()))
    def test_root_doc_exists_and_size(self, path, min_lines):
        full = os.path.join(ROOT, path)
        assert os.path.isfile(full), f"Missing: {path}"
        lines = len(open(full, encoding="utf-8").readlines())
        assert lines >= min_lines, f"{path} has {lines} lines, expected >= {min_lines}"


class TestAPIDocContent:
    """Verify API.md covers all endpoint groups."""

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = open(os.path.join(DOCS, "API.md"), encoding="utf-8").read()

    def test_health_endpoints(self):
        for ep in ["/health", "/ready", "/metrics", "/health/worker",
                    "/health/grpc", "/health/embedding", "/health/registry",
                    "/health/monitor"]:
            assert ep in self.content, f"Missing endpoint: {ep}"

    def test_auth_endpoints(self):
        for ep in ["/auth/signup", "/auth/login", "/auth/refresh",
                    "/auth/logout", "/auth/me"]:
            assert ep in self.content, f"Missing endpoint: {ep}"

    def test_openai_endpoints(self):
        for ep in ["/v1/chat/completions", "/v1/completions",
                    "/v1/embeddings", "/v1/models"]:
            assert ep in self.content, f"Missing endpoint: {ep}"

    def test_legacy_endpoints(self):
        for ep in ["/generate", "/vector/align", "/embeddings/similarity"]:
            assert ep in self.content, f"Missing endpoint: {ep}"

    def test_job_endpoints(self):
        assert "/jobs" in self.content
        assert "DELETE" in self.content

    def test_platform_endpoints(self):
        assert "/api/v1/platforms" in self.content

    def test_yaml_endpoints(self):
        assert "/api/v1/yaml/generate" in self.content
        assert "/api/v1/yaml/validate" in self.content

    def test_error_format(self):
        assert "error_code" in self.content or "Error Response" in self.content

    def test_authentication_section(self):
        assert "Bearer" in self.content
        assert "API Key" in self.content or "API key" in self.content

    def test_websocket_section(self):
        assert "WebSocket" in self.content or "Socket.IO" in self.content

    def test_grpc_section(self):
        assert "gRPC" in self.content

    def test_sdk_section(self):
        assert "EcoClient" in self.content or "api-client" in self.content


class TestArchitectureDocContent:
    """Verify ARCHITECTURE.md covers all system components."""

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = open(os.path.join(DOCS, "ARCHITECTURE.md"), encoding="utf-8").read()

    def test_layers(self):
        for layer in ["Layer 0", "Layer 1", "Layer 2", "Layer 3", "Layer 4", "Layer 5"]:
            assert layer in self.content, f"Missing: {layer}"

    def test_engines(self):
        for engine in ["vLLM", "TGI", "Ollama", "SGLang", "TensorRT", "DeepSpeed", "LMDeploy"]:
            assert engine in self.content, f"Missing engine: {engine}"

    def test_resilience_patterns(self):
        for pattern in ["Circuit Breaker", "Connection Pool", "Retry", "Health Monitor", "WAL"]:
            assert pattern in self.content, f"Missing pattern: {pattern}"

    def test_governance_section(self):
        assert "document_metadata" in self.content
        assert "governance_info" in self.content
        assert "registry_binding" in self.content
        assert "vector_alignment_map" in self.content

    def test_data_flow(self):
        assert "Data Flow" in self.content or "data flow" in self.content

    def test_security_section(self):
        assert "Security" in self.content
        assert "mTLS" in self.content

    def test_cicd_section(self):
        assert "CI/CD" in self.content or "Pipeline" in self.content


class TestDeploymentDocContent:
    """Verify DEPLOYMENT.md covers all deployment methods."""

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = open(os.path.join(DOCS, "DEPLOYMENT.md"), encoding="utf-8").read()

    def test_local_development(self):
        assert "docker compose" in self.content.lower() or "Docker Compose" in self.content

    def test_kubernetes(self):
        assert "helm install" in self.content
        assert "kubectl" in self.content

    def test_argocd(self):
        assert "Argo CD" in self.content
        assert "applicationset" in self.content.lower()

    def test_monitoring(self):
        assert "Prometheus" in self.content
        assert "Grafana" in self.content

    def test_troubleshooting(self):
        assert "Troubleshooting" in self.content or "troubleshoot" in self.content.lower()


class TestQYAMLDocContent:
    """Verify QYAML_GOVERNANCE.md covers the full spec."""

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = open(os.path.join(DOCS, "QYAML_GOVERNANCE.md"), encoding="utf-8").read()

    def test_four_blocks(self):
        for block in ["document_metadata", "governance_info",
                       "registry_binding", "vector_alignment_map"]:
            assert block in self.content, f"Missing block: {block}"

    def test_uuid_v1(self):
        assert "UUID v1" in self.content or "uuid v1" in self.content.lower()

    def test_validation_phases(self):
        assert "YAML" in self.content and "parse" in self.content.lower()

    def test_audit_trail(self):
        assert "audit" in self.content.lower()

    def test_complete_example(self):
        assert "apiVersion" in self.content


class TestEnvReferenceContent:
    """Verify ENV_REFERENCE.md covers all ECO_* variables."""

    @pytest.fixture(autouse=True)
    def load(self):
        self.content = open(os.path.join(DOCS, "ENV_REFERENCE.md"), encoding="utf-8").read()

    def test_core_vars(self):
        for var in ["ECO_ENVIRONMENT", "ECO_LOG_LEVEL", "ECO_AI_HTTP_PORT",
                     "ECO_API_PORT", "ECO_JWT_SECRET", "ECO_REDIS_URL"]:
            assert var in self.content, f"Missing var: {var}"

    def test_engine_vars(self):
        for var in ["ECO_VLLM_URL", "ECO_TGI_URL", "ECO_OLLAMA_URL", "ECO_SGLANG_URL"]:
            assert var in self.content, f"Missing var: {var}"

    def test_index_vars(self):
        for var in ["ECO_FAISS_ENABLED", "ECO_ES_ENABLED", "ECO_NEO4J_ENABLED"]:
            assert var in self.content, f"Missing var: {var}"

    def test_production_checklist(self):
        assert "Production Checklist" in self.content or "production" in self.content.lower()


class TestCrossReferences:
    """Verify documentation cross-references are consistent."""

    def _read(self, path):
        full = os.path.join(ROOT, path)
        return open(full, encoding="utf-8").read()

    def test_readme_links_to_docs(self):
        content = self._read("README.md")
        for doc in ["docs/API.md", "docs/ARCHITECTURE.md", "docs/DEPLOYMENT.md"]:
            assert doc in content, f"README missing link to {doc}"

    def test_contributing_links_to_docs(self):
        content = self._read("CONTRIBUTING.md")
        assert "DEVELOPER_GUIDE" in content or "Developer Guide" in content

    def test_api_links_to_architecture(self):
        content = self._read("docs/API.md")
        assert "ARCHITECTURE" in content

    def test_architecture_links_to_api(self):
        content = self._read("docs/ARCHITECTURE.md")
        assert "API" in content

    def test_deployment_links_to_architecture(self):
        content = self._read("docs/DEPLOYMENT.md")
        assert "ARCHITECTURE" in content or "Architecture" in content
