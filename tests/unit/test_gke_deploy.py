"""Tests for GKE eco-staging deployment artifacts."""
import os
import sys

# ── Path setup ──────────────────────────────────────────────
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def _read(path):
    with open(os.path.join(ROOT, path)) as f:
        return f.read()

def _exists(path):
    return os.path.isfile(os.path.join(ROOT, path))


# ── Dockerfile tests ────────────────────────────────────────
class TestDockerfiles:
    def test_web_dockerfile_exists(self):
        assert _exists("platforms/web/Dockerfile")

    def test_web_dockerfile_nginx(self):
        content = _read("platforms/web/Dockerfile")
        assert "nginx" in content
        assert "HEALTHCHECK" in content
        assert "/health" in content

    def test_ai_dockerfile_exists(self):
        assert _exists("backend/ai/Dockerfile")

    def test_api_dockerfile_exists(self):
        assert _exists("backend/api/Dockerfile")

    def test_gateway_dockerfile_exists(self):
        assert _exists("docker/Dockerfile")


# ── K8s staging manifests ───────────────────────────────────
class TestStagingManifests:
    STAGING_FILES = [
        "k8s/staging/namespace.qyaml",
        "k8s/staging/configmap.qyaml",
        "k8s/staging/api-gateway.qyaml",
        "k8s/staging/ai-service.qyaml",
        "k8s/staging/api-service.qyaml",
        "k8s/staging/web-frontend.qyaml",
        "k8s/staging/redis.qyaml",
        "k8s/staging/postgres.qyaml",
        "k8s/staging/ingress.qyaml",
    ]

    def test_all_staging_files_exist(self):
        for f in self.STAGING_FILES:
            assert _exists(f), f"Missing: {f}"

    def test_namespace_eco_staging(self):
        content = _read("k8s/staging/namespace.qyaml")
        assert "eco-staging" in content
        assert "ServiceAccount" in content
        assert "eco-sa" in content

    def test_configmap_eco_vars(self):
        content = _read("k8s/staging/configmap.qyaml")
        assert "ECO_ENVIRONMENT" in content
        assert "staging" in content
        assert "ECO_DEFAULT_ENGINE" in content

    def test_configmap_secrets(self):
        content = _read("k8s/staging/configmap.qyaml")
        assert "eco-secrets" in content
        assert "ECO_POSTGRES_USER" in content
        assert "DATABASE_URL" in content

    def test_api_gateway_image(self):
        content = _read("k8s/staging/api-gateway.qyaml")
        assert "asia-east1-docker.pkg.dev/my-project-ops-1991/eco-images/eco-gateway" in content
        assert "readinessProbe" in content
        assert "livenessProbe" in content

    def test_ai_service_image(self):
        content = _read("k8s/staging/ai-service.qyaml")
        assert "asia-east1-docker.pkg.dev/my-project-ops-1991/eco-images/eco-ai" in content
        assert "8001" in content

    def test_api_service_image(self):
        content = _read("k8s/staging/api-service.qyaml")
        assert "asia-east1-docker.pkg.dev/my-project-ops-1991/eco-images/eco-api" in content
        assert "3000" in content

    def test_web_frontend_image(self):
        content = _read("k8s/staging/web-frontend.qyaml")
        assert "asia-east1-docker.pkg.dev/my-project-ops-1991/eco-images/eco-web" in content
        assert "80" in content

    def test_redis_staging(self):
        content = _read("k8s/staging/redis.qyaml")
        assert "eco-staging" in content
        assert "redis:7-alpine" in content
        assert "512mb" in content

    def test_postgres_staging(self):
        content = _read("k8s/staging/postgres.qyaml")
        assert "eco-staging" in content
        assert "postgres:16-alpine" in content

    def test_ingress_gke(self):
        content = _read("k8s/staging/ingress.qyaml")
        assert "eco-staging" in content
        assert "/api" in content
        assert "/v1" in content
        assert "eco-web-svc" in content

    def test_all_have_governance_blocks(self):
        for f in self.STAGING_FILES:
            content = _read(f)
            assert "schema_version: v8" in content, f"Missing governance in {f}"
            assert "yaml-toolkit-v8" in content, f"Missing toolkit ref in {f}"

    def test_all_have_eco_staging_namespace(self):
        for f in self.STAGING_FILES:
            content = _read(f)
            assert "eco-staging" in content, f"Missing eco-staging namespace in {f}"


# ── Argo CD ─────────────────────────────────────────────────
class TestArgoCD:
    def test_eco_staging_app_exists(self):
        assert _exists("k8s/argocd/argo-app-eco-staging.yaml")

    def test_eco_staging_app_content(self):
        content = _read("k8s/argocd/argo-app-eco-staging.yaml")
        assert "eco-staging" in content
        assert "k8s/staging" in content
        assert "selfHeal: true" in content
        assert "prune: true" in content
        assert "*.qyaml" in content

    def test_eco_staging_targets_correct_namespace(self):
        content = _read("k8s/argocd/argo-app-eco-staging.yaml")
        assert "namespace: eco-staging" in content


# ── Deploy workflow ──────────────────────────────────────────
class TestDeployWorkflow:
    def test_deploy_gke_workflow_exists(self):
        assert _exists(".github/workflows/deploy-gke.yaml")

    def test_deploy_gke_content(self):
        content = _read(".github/workflows/deploy-gke.yaml")
        assert "my-project-ops-1991" in content
        assert "eco-staging" in content
        assert "asia-east1" in content
        assert "eco-images" in content
        assert "KUBE_CONFIG_STAGING" in content

    def test_deploy_gke_builds_all_images(self):
        content = _read(".github/workflows/deploy-gke.yaml")
        assert "eco-gateway" in content
        assert "eco-ai" in content
        assert "eco-api" in content
        assert "eco-web" in content


# ── Deploy script ────────────────────────────────────────────
class TestDeployScript:
    def test_deploy_script_exists(self):
        assert _exists("deploy.sh")

    def test_deploy_script_executable_content(self):
        content = _read("deploy.sh")
        assert "my-project-ops-1991" in content
        assert "eco-staging" in content
        assert "asia-east1" in content
        assert "eco-images" in content
        assert "gcloud" in content
        assert "kubectl" in content
        assert "docker" in content
