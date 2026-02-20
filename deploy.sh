#!/usr/bin/env bash
# IndestructibleEco v1.0 — Manual GKE Deployment Script
# Target: GKE eco-staging cluster (asia-east1)
# Project: my-project-ops-1991
#
# Usage:
#   chmod +x deploy.sh
#   ./deploy.sh              # Deploy all services
#   ./deploy.sh --build-only # Build and push images only
#   ./deploy.sh --apply-only # Apply k8s manifests only
set -euo pipefail

# ── Configuration ──────────────────────────────────────────
GCP_PROJECT="my-project-ops-1991"
GKE_CLUSTER="eco-staging"
GKE_ZONE="asia-east1"
GAR_LOCATION="asia-east1"
GAR_REPOSITORY="eco-images"
REGISTRY="${GAR_LOCATION}-docker.pkg.dev/${GCP_PROJECT}/${GAR_REPOSITORY}"
NAMESPACE="eco-staging"
TAG="${IMAGE_TAG:-latest}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log()  { echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} $*"; }
ok()   { echo -e "${GREEN}[OK]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()  { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# ── Pre-flight checks ─────────────────────────────────────
preflight() {
    log "Pre-flight checks..."
    for cmd in gcloud docker kubectl; do
        if ! command -v "$cmd" &>/dev/null; then
            err "$cmd not found. Install it first."
            exit 1
        fi
    done
    ok "All tools available"
}

# ── Authenticate ───────────────────────────────────────────
authenticate() {
    log "Authenticating to GCP project: ${GCP_PROJECT}"
    gcloud config set project "${GCP_PROJECT}" 2>/dev/null
    gcloud auth configure-docker "${GAR_LOCATION}-docker.pkg.dev" --quiet 2>/dev/null
    ok "Docker configured for Artifact Registry"

    log "Connecting to GKE cluster: ${GKE_CLUSTER}"
    gcloud container clusters get-credentials "${GKE_CLUSTER}" \
        --zone "${GKE_ZONE}" \
        --project "${GCP_PROJECT}"
    ok "Connected to ${GKE_CLUSTER}"
}

# ── Create Artifact Registry (if needed) ───────────────────
ensure_registry() {
    log "Ensuring Artifact Registry exists..."
    if ! gcloud artifacts repositories describe "${GAR_REPOSITORY}" \
        --location="${GAR_LOCATION}" --project="${GCP_PROJECT}" &>/dev/null; then
        log "Creating Artifact Registry: ${GAR_REPOSITORY}"
        gcloud artifacts repositories create "${GAR_REPOSITORY}" \
            --repository-format=docker \
            --location="${GAR_LOCATION}" \
            --project="${GCP_PROJECT}" \
            --description="IndestructibleEco container images"
        ok "Registry created"
    else
        ok "Registry already exists"
    fi
}

# ── Build & Push ───────────────────────────────────────────
build_and_push() {
    log "Building Docker images (tag: ${TAG})..."

    log "  [1/4] eco-gateway (root gateway)"
    docker build -t "${REGISTRY}/eco-gateway:${TAG}" -f docker/Dockerfile . 2>&1 | tail -5
    docker push "${REGISTRY}/eco-gateway:${TAG}"
    ok "  eco-gateway pushed"

    log "  [2/4] eco-ai (AI service)"
    docker build -t "${REGISTRY}/eco-ai:${TAG}" -f backend/ai/Dockerfile backend/ai/ 2>&1 | tail -5
    docker push "${REGISTRY}/eco-ai:${TAG}"
    ok "  eco-ai pushed"

    log "  [3/4] eco-api (API service)"
    docker build -t "${REGISTRY}/eco-api:${TAG}" backend/api/ 2>&1 | tail -5
    docker push "${REGISTRY}/eco-api:${TAG}"
    ok "  eco-api pushed"

    log "  [4/4] eco-web (Web frontend)"
    docker build -t "${REGISTRY}/eco-web:${TAG}" platforms/web/ 2>&1 | tail -5
    docker push "${REGISTRY}/eco-web:${TAG}"
    ok "  eco-web pushed"

    ok "All images built and pushed"
}

# ── Convert .qyaml & Apply ─────────────────────────────────
apply_manifests() {
    log "Converting .qyaml to standard YAML..."
    TMPDIR=$(mktemp -d)
    if command -v node &>/dev/null && [ -f tools/yaml-toolkit/bin/cli.js ]; then
        node tools/yaml-toolkit/bin/cli.js convert k8s/staging/ --output "${TMPDIR}/" 2>/dev/null || true
    fi
    # Fallback: copy .qyaml as .yaml
    for f in k8s/staging/*.qyaml; do
        [ -f "$f" ] || continue
        base=$(basename "${f%.qyaml}.yaml")
        [ -f "${TMPDIR}/${base}" ] || cp "$f" "${TMPDIR}/${base}"
    done
    ok "Converted $(ls "${TMPDIR}"/*.yaml 2>/dev/null | wc -l) manifests"

    log "Applying namespace..."
    kubectl apply -f "${TMPDIR}/namespace.yaml" 2>/dev/null || true

    log "Applying all manifests to ${NAMESPACE}..."
    kubectl apply -f "${TMPDIR}/" --namespace="${NAMESPACE}"
    ok "Manifests applied"

    # Update image tags if not :latest
    if [ "${TAG}" != "latest" ]; then
        log "Updating image tags to ${TAG}..."
        kubectl set image deployment/eco-api-gateway eco-gateway="${REGISTRY}/eco-gateway:${TAG}" -n "${NAMESPACE}" 2>/dev/null || true
        kubectl set image deployment/eco-ai-service eco-ai="${REGISTRY}/eco-ai:${TAG}" -n "${NAMESPACE}" 2>/dev/null || true
        kubectl set image deployment/eco-api-service eco-api="${REGISTRY}/eco-api:${TAG}" -n "${NAMESPACE}" 2>/dev/null || true
        kubectl set image deployment/eco-web-frontend eco-web="${REGISTRY}/eco-web:${TAG}" -n "${NAMESPACE}" 2>/dev/null || true
    fi

    rm -rf "${TMPDIR}"
}

# ── Wait & Verify ──────────────────────────────────────────
verify() {
    log "Waiting for rollouts..."
    for deploy in eco-api-gateway eco-ai-service eco-api-service eco-web-frontend; do
        kubectl rollout status "deployment/${deploy}" -n "${NAMESPACE}" --timeout=300s 2>/dev/null ||             warn "${deploy} rollout not complete (may still be starting)"
    done

    echo ""
    log "=== Deployment Status ==="
    echo ""
    kubectl get pods -n "${NAMESPACE}" -o wide
    echo ""
    kubectl get svc -n "${NAMESPACE}"
    echo ""
    kubectl get ingress -n "${NAMESPACE}" 2>/dev/null || true
    echo ""

    # Health check
    log "Running health checks..."
    GATEWAY_POD=$(kubectl get pods -n "${NAMESPACE}" -l app.kubernetes.io/name=eco-api-gateway -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)
    if [ -n "${GATEWAY_POD}" ]; then
        kubectl exec -n "${NAMESPACE}" "${GATEWAY_POD}" -- wget -qO- http://localhost:8000/health 2>/dev/null && ok "Gateway health OK" || warn "Gateway health check failed"
    fi

    ok "Deployment complete!"
    echo ""
    log "Quick access:"
    echo "  kubectl port-forward svc/eco-web-svc 8080:80 -n ${NAMESPACE}"
    echo "  kubectl port-forward svc/eco-gateway-svc 8000:8000 -n ${NAMESPACE}"
    echo "  kubectl port-forward svc/eco-api-svc 3000:3000 -n ${NAMESPACE}"
    echo "  Then open: http://localhost:8080"
}

# ── Main ───────────────────────────────────────────────────
main() {
    preflight

    case "${1:-}" in
        --build-only)
            authenticate
            ensure_registry
            build_and_push
            ;;
        --apply-only)
            authenticate
            apply_manifests
            verify
            ;;
        *)
            authenticate
            ensure_registry
            build_and_push
            apply_manifests
            verify
            ;;
    esac
}

main "$@"
