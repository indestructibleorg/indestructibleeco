#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# SecCompOps Platform — Production Deployment Script
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

log_info()  { echo "[deploy] $(date -u +%FT%TZ) INFO  $*"; }
log_error() { echo "[deploy] $(date -u +%FT%TZ) ERROR $*" >&2; }
log_ok()    { echo "[deploy] $(date -u +%FT%TZ) OK    $*"; }
die() { log_error "$@"; exit 1; }

REGISTRY="${SECCOMPOPS_REGISTRY:-ghcr.io/indestructibleorg}"
IMAGE_NAME="${REGISTRY}/seccompops-platform"
VERSION="${SECCOMPOPS_VERSION:-$(date -u +%Y%m%d.%H%M%S)}"
IMAGE_TAG="${IMAGE_NAME}:${VERSION}"
NAMESPACE="${SECCOMPOPS_NAMESPACE:-seccompops}"
RELEASE_NAME="${SECCOMPOPS_RELEASE:-seccompops}"

log_info "Step 1/6: Pre-flight checks..."
for cmd in docker kubectl helm; do command -v "${cmd}" &>/dev/null || die "${cmd} required"; done
kubectl cluster-info &>/dev/null || die "Cannot connect to cluster"
log_ok "Pre-flight passed"

log_info "Step 2/6: Building container image..."
docker build -f "${PROJECT_ROOT}/Dockerfile.prod" -t "${IMAGE_TAG}" -t "${IMAGE_NAME}:latest" "${PROJECT_ROOT}"
log_ok "Image built: ${IMAGE_TAG}"

log_info "Step 3/6: Security scanning..."
if command -v trivy &>/dev/null; then
    trivy image --severity HIGH,CRITICAL --exit-code 1 "${IMAGE_TAG}" || die "Security scan failed"
    log_ok "Security scan passed"
fi

log_info "Step 4/6: Pushing image..."
docker push "${IMAGE_TAG}" && docker push "${IMAGE_NAME}:latest"
log_ok "Image pushed"

log_info "Step 5/6: Deploying via Helm..."
kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -
helm upgrade --install "${RELEASE_NAME}" "${PROJECT_ROOT}/helm/seccompops" \
    --namespace "${NAMESPACE}" --set image.repository="${IMAGE_NAME}" --set image.tag="${VERSION}" \
    --wait --timeout 5m
log_ok "Helm deployment complete"

log_info "Step 6/6: Smoke test..."
kubectl -n "${NAMESPACE}" rollout status deployment/seccompops-engine --timeout=120s
log_ok "Deployment complete — version ${VERSION}"
