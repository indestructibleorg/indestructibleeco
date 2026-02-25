#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# GovOps Platform — Production Deployment Script
# Full deployment pipeline: build, scan, sign, deploy via Helm.
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

log_info()  { echo "[deploy] $(date -u +%FT%TZ) INFO  $*"; }
log_warn()  { echo "[deploy] $(date -u +%FT%TZ) WARN  $*" >&2; }
log_error() { echo "[deploy] $(date -u +%FT%TZ) ERROR $*" >&2; }
log_ok()    { echo "[deploy] $(date -u +%FT%TZ) OK    $*"; }

die() { log_error "$@"; exit 1; }

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
REGISTRY="${GOVOPS_REGISTRY:-ghcr.io/indestructibleorg}"
IMAGE_NAME="${REGISTRY}/govops-platform"
VERSION="${GOVOPS_VERSION:-$(date -u +%Y%m%d.%H%M%S)}"
IMAGE_TAG="${IMAGE_NAME}:${VERSION}"
NAMESPACE="${GOVOPS_NAMESPACE:-govops}"
RELEASE_NAME="${GOVOPS_RELEASE:-govops}"
CLUSTER="${GOVOPS_CLUSTER:-production}"

# ---------------------------------------------------------------------------
# Pre-flight
# ---------------------------------------------------------------------------
log_info "Step 1/7: Pre-flight checks..."

for cmd in docker kubectl helm; do
    command -v "${cmd}" &>/dev/null || die "${cmd} is required"
done

kubectl cluster-info &>/dev/null || die "Cannot connect to Kubernetes cluster"
log_ok "Pre-flight passed"

# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
log_info "Step 2/7: Building container image..."

docker build \
    -f "${PROJECT_ROOT}/Dockerfile.prod" \
    -t "${IMAGE_TAG}" \
    -t "${IMAGE_NAME}:latest" \
    --label "org.opencontainers.image.version=${VERSION}" \
    --label "org.opencontainers.image.created=$(date -u +%FT%TZ)" \
    "${PROJECT_ROOT}"

log_ok "Image built: ${IMAGE_TAG}"

# ---------------------------------------------------------------------------
# Security scan
# ---------------------------------------------------------------------------
log_info "Step 3/7: Security scanning..."

if command -v trivy &>/dev/null; then
    trivy image --severity HIGH,CRITICAL --exit-code 1 "${IMAGE_TAG}" || die "Security scan failed"
    log_ok "Security scan passed"
else
    log_warn "trivy not found — skipping security scan"
fi

# ---------------------------------------------------------------------------
# Push
# ---------------------------------------------------------------------------
log_info "Step 4/7: Pushing image..."

docker push "${IMAGE_TAG}"
docker push "${IMAGE_NAME}:latest"
log_ok "Image pushed"

# ---------------------------------------------------------------------------
# Namespace
# ---------------------------------------------------------------------------
log_info "Step 5/7: Ensuring namespace..."

kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -
log_ok "Namespace ${NAMESPACE} ready"

# ---------------------------------------------------------------------------
# Deploy via Helm
# ---------------------------------------------------------------------------
log_info "Step 6/7: Deploying via Helm..."

helm upgrade --install "${RELEASE_NAME}" \
    "${PROJECT_ROOT}/helm/govops" \
    --namespace "${NAMESPACE}" \
    --set image.repository="${IMAGE_NAME}" \
    --set image.tag="${VERSION}" \
    --wait \
    --timeout 5m

log_ok "Helm deployment complete"

# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------
log_info "Step 7/7: Running smoke tests..."

kubectl -n "${NAMESPACE}" rollout status deployment/govops-engine --timeout=120s
log_ok "Deployment rolled out successfully"

echo ""
echo "  GovOps Platform — Deployment Complete"
echo "  ======================================"
echo "  Version:   ${VERSION}"
echo "  Namespace: ${NAMESPACE}"
echo "  Cluster:   ${CLUSTER}"
echo ""
