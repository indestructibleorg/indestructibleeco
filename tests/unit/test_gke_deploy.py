"""Tests for GKE deployment artifacts (staging + production)."""
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
        assert "ghcr.io/indestructibleorg/gateway" in content
        assert "readinessProbe" in content
        assert "livenessProbe" in content

    def test_ai_service_image(self):
        content = _read("k8s/staging/ai-service.qyaml")
        assert "ghcr.io/indestructibleorg/ai" in content
        assert "8001" in content

    def test_api_service_image(self):
        content = _read("k8s/staging/api-service.qyaml")
        assert "ghcr.io/indestructibleorg/api" in content
        assert "3000" in content

    def test_web_frontend_image(self):
        content = _read("k8s/staging/web-frontend.qyaml")
        assert "ghcr.io/indestructibleorg/web" in content
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

    def test_ingress_staging_domain(self):
        content = _read("k8s/staging/ingress.qyaml")
        assert "staging.autoecoops.io" in content
        assert "api-staging.autoecoops.io" in content

    def test_all_have_governance_blocks(self):
        for f in self.STAGING_FILES:
            content = _read(f)
            assert "schema_version: v8" in content, f"Missing governance in {f}"
            assert "yaml-toolkit-v8" in content, f"Missing toolkit ref in {f}"

    def test_all_have_eco_staging_namespace(self):
        for f in self.STAGING_FILES:
            content = _read(f)
            assert "eco-staging" in content, f"Missing eco-staging namespace in {f}"


# ── K8s production manifests ────────────────────────────────
class TestProductionManifests:
    PRODUCTION_FILES = [
        "k8s/production/namespace.qyaml",
        "k8s/production/configmap.qyaml",
        "k8s/production/api-gateway.qyaml",
        "k8s/production/ai-service.qyaml",
        "k8s/production/api-service.qyaml",
        "k8s/production/web-frontend.qyaml",
        "k8s/production/redis.qyaml",
        "k8s/production/postgres.qyaml",
        "k8s/production/ingress.qyaml",
    ]

    def test_all_production_files_exist(self):
        for f in self.PRODUCTION_FILES:
            assert _exists(f), f"Missing: {f}"

    def test_namespace_eco_production(self):
        content = _read("k8s/production/namespace.qyaml")
        assert "eco-production" in content
        assert "ServiceAccount" in content
        assert "eco-sa" in content

    def test_configmap_production_vars(self):
        content = _read("k8s/production/configmap.qyaml")
        assert "ECO_ENVIRONMENT" in content
        assert "production" in content
        assert "ECO_LOG_LEVEL" in content

    def test_configmap_no_hardcoded_secrets(self):
        content = _read("k8s/production/configmap.qyaml")
        assert "INJECT_FROM_K8S_SECRET" in content

    def test_api_gateway_production(self):
        content = _read("k8s/production/api-gateway.qyaml")
        assert "asia-east1-docker.pkg.dev/my-project-ops-1991/indestructibleeco/gateway" in content
        assert "eco-production" in content
        assert "replicas:" in content
        assert "readinessProbe" in content
        assert "livenessProbe" in content

    def test_ai_service_production(self):
        content = _read("k8s/production/ai-service.qyaml")
        assert "asia-east1-docker.pkg.dev/my-project-ops-1991/indestructibleeco/ai" in content
        assert "eco-production" in content
        assert "8001" in content

    def test_api_service_production(self):
        content = _read("k8s/production/api-service.qyaml")
        assert "asia-east1-docker.pkg.dev/my-project-ops-1991/indestructibleeco/api" in content
        assert "eco-production" in content
        assert "replicas:" in content

    def test_web_frontend_production(self):
        content = _read("k8s/production/web-frontend.qyaml")
        assert "asia-east1-docker.pkg.dev/my-project-ops-1991/indestructibleeco/web" in content
        assert "eco-production" in content
        assert "replicas:" in content

    def test_redis_production(self):
        content = _read("k8s/production/redis.qyaml")
        assert "eco-production" in content
        assert "redis:" in content

    def test_postgres_production(self):
        content = _read("k8s/production/postgres.qyaml")
        assert "eco-production" in content
        assert "postgres:16-alpine" in content
        assert "eco_production" in content

    def test_ingress_production_domain(self):
        content = _read("k8s/production/ingress.qyaml")
        assert "autoecoops.io" in content
        assert "api.autoecoops.io" in content

    def test_ingress_production_routing(self):
        content = _read("k8s/production/ingress.qyaml")
        assert "eco-web-svc" in content
        assert "eco-api-svc" in content
        assert "api.autoecoops.io" in content

    def test_production_security_context(self):
        # All services should use non-root user for security
        non_root_files = ["k8s/production/api-gateway.qyaml",
                          "k8s/production/ai-service.qyaml",
                          "k8s/production/api-service.qyaml",
                          "k8s/production/web-frontend.qyaml"]
        for f in non_root_files:
            content = _read(f)
            assert "runAsNonRoot: true" in content, f"Missing securityContext in {f}"
            assert "runAsUser:" in content, f"Missing runAsUser in {f}"

    def test_all_have_governance_blocks(self):
        for f in self.PRODUCTION_FILES:
            content = _read(f)
            assert "schema_version: v8" in content, f"Missing governance in {f}"
            assert "yaml-toolkit-v8" in content, f"Missing toolkit ref in {f}"

    def test_all_have_eco_production_namespace(self):
        for f in self.PRODUCTION_FILES:
            content = _read(f)
            assert "eco-production" in content, f"Missing eco-production namespace in {f}"


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

    def test_eco_production_app_exists(self):
        assert _exists("k8s/argocd/argo-app-eco-production.yaml")

    def test_eco_production_app_content(self):
        content = _read("k8s/argocd/argo-app-eco-production.yaml")
        assert "eco-production" in content
        assert "k8s/production" in content
        assert "selfHeal: true" in content
        assert "prune: true" in content
        assert "*.qyaml" in content

    def test_eco_production_targets_correct_namespace(self):
        content = _read("k8s/argocd/argo-app-eco-production.yaml")
        assert "namespace: eco-production" in content


# ── Deploy workflows ────────────────────────────────────────
class TestDeployWorkflow:
    def test_deploy_gke_workflow_exists(self):
        assert _exists(".github/workflows/deploy-gke.yaml")

    def test_deploy_gke_content(self):
        content = _read(".github/workflows/deploy-gke.yaml")
        assert "vars.GCP_PROJECT_ID" in content
        assert "vars.GKE_CLUSTER_STAGING" in content or "eco-staging" in content
        assert "GCP_SA_KEY" in content

    def test_deploy_gke_builds_all_images(self):
        content = _read(".github/workflows/deploy-gke.yaml")
        assert "gateway" in content
        assert "/ai:" in content or "eco-ai" in content
        assert "/api:" in content or "eco-api" in content
        assert "/web:" in content or "eco-web" in content

    def test_deploy_production_workflow_exists(self):
        assert _exists(".github/workflows/deploy-gke-production.yaml")

    def test_deploy_production_content(self):
        content = _read(".github/workflows/deploy-gke-production.yaml")
        assert "vars.GCP_PROJECT_ID" in content
        assert "vars.GKE_CLUSTER_PRODUCTION" in content or "eco-production" in content
        assert "GCP_SA_KEY" in content
        assert "deploy-production" in content

    def test_deploy_production_requires_confirmation(self):
        content = _read(".github/workflows/deploy-gke-production.yaml")
        assert "workflow_dispatch" in content
        assert "confirm" in content


# ── Deploy script ───────────────────────────────────────────
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


# ── Domain configuration ────────────────────────────────────
class TestDomainConfig:
    def test_staging_ingress_uses_autoecoops(self):
        content = _read("k8s/staging/ingress.qyaml")
        assert "autoecoops.io" in content
        assert "eco-base.io" not in content

    def test_production_ingress_uses_autoecoops(self):
        content = _read("k8s/production/ingress.qyaml")
        assert "autoecoops.io" in content
        assert "eco-base.io" not in content

    def test_base_ingress_uses_autoecoops(self):
        content = _read("k8s/ingress/ingress.qyaml")
        assert "autoecoops.io" in content
        assert "eco-base.io" not in content

    def test_wrangler_uses_autoecoops(self):
        content = _read("backend/cloudflare/wrangler.toml")
        assert "autoecoops.io" in content
        assert "eco-base.io" not in content

    def test_wrangler_sets_api_url(self):
        content = _read("backend/cloudflare/wrangler.toml")
        assert 'ECO_API_URL = "https://api.autoecoops.io"' in content

    def test_helm_values_uses_autoecoops(self):
        content = _read("helm/values.yaml")
        assert "autoecoops.io" in content
        assert "eco-base.io" not in content
