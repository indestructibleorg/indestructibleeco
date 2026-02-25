#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# SecCompOps Platform — Rollback Script
# =============================================================================

log_info()  { echo "[rollback] $(date -u +%FT%TZ) INFO  $*"; }
log_error() { echo "[rollback] $(date -u +%FT%TZ) ERROR $*" >&2; }
log_ok()    { echo "[rollback] $(date -u +%FT%TZ) OK    $*"; }
die() { log_error "$@"; exit 1; }

NAMESPACE="${SECCOMPOPS_NAMESPACE:-seccompops}"
RELEASE_NAME="${SECCOMPOPS_RELEASE:-seccompops}"
REVISION="${1:-}"

command -v helm &>/dev/null   || die "helm is required"
command -v kubectl &>/dev/null || die "kubectl is required"

log_info "Current release status:"
helm status "${RELEASE_NAME}" -n "${NAMESPACE}" || die "Release not found"
helm history "${RELEASE_NAME}" -n "${NAMESPACE}" --max 5

ARGS=("${RELEASE_NAME}" -n "${NAMESPACE}" --wait --timeout 3m)
[[ -n "${REVISION}" ]] && ARGS+=("${REVISION}")

log_info "Rolling back..."
helm rollback "${ARGS[@]}"

kubectl -n "${NAMESPACE}" rollout status deployment/seccompops-engine --timeout=120s
log_ok "Rollback complete"
log_info "Audit: rollback by $(whoami)@$(hostname) at $(date -u +%FT%TZ)"
