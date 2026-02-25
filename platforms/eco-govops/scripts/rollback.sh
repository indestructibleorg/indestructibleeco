#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# GovOps Platform — Rollback Script
# Rolls back the Helm release to the previous revision.
# =============================================================================

log_info()  { echo "[rollback] $(date -u +%FT%TZ) INFO  $*"; }
log_error() { echo "[rollback] $(date -u +%FT%TZ) ERROR $*" >&2; }
log_ok()    { echo "[rollback] $(date -u +%FT%TZ) OK    $*"; }

die() { log_error "$@"; exit 1; }

NAMESPACE="${GOVOPS_NAMESPACE:-govops}"
RELEASE_NAME="${GOVOPS_RELEASE:-govops}"
REVISION="${1:-}"
DRY_RUN="${GOVOPS_DRY_RUN:-false}"

command -v helm &>/dev/null   || die "helm is required"
command -v kubectl &>/dev/null || die "kubectl is required"

# ---------------------------------------------------------------------------
# Pre-rollback state
# ---------------------------------------------------------------------------
log_info "Current release status:"
helm status "${RELEASE_NAME}" -n "${NAMESPACE}" 2>/dev/null || die "Release '${RELEASE_NAME}' not found in namespace '${NAMESPACE}'"

log_info "Release history:"
helm history "${RELEASE_NAME}" -n "${NAMESPACE}" --max 5

# ---------------------------------------------------------------------------
# Rollback
# ---------------------------------------------------------------------------
ROLLBACK_ARGS=("${RELEASE_NAME}" -n "${NAMESPACE}" --wait --timeout 3m)

if [[ -n "${REVISION}" ]]; then
    log_info "Rolling back to revision ${REVISION}..."
    ROLLBACK_ARGS+=("${REVISION}")
else
    log_info "Rolling back to previous revision..."
fi

if [[ "${DRY_RUN}" == "true" ]]; then
    log_info "[DRY-RUN] helm rollback ${ROLLBACK_ARGS[*]}"
else
    helm rollback "${ROLLBACK_ARGS[@]}"
fi

# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------
log_info "Verifying rollback..."
kubectl -n "${NAMESPACE}" rollout status deployment/govops-engine --timeout=120s
log_ok "Rollback complete — deployment is healthy"

# Audit log entry
log_info "Audit: rollback executed by $(whoami)@$(hostname) at $(date -u +%FT%TZ)"
