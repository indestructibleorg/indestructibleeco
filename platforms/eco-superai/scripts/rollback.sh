#!/usr/bin/env bash
# ============================================================================
# SuperAI Platform - Rollback Script
# ============================================================================
# Rolls back the deployed application to a specified version/tag.
# Supports both Helm-based and Kustomize-based deployments.
# Creates backups before rollback and restores on failure.
#
# Usage:
#   ./scripts/rollback.sh <target-version> [options]
#
# Options:
#   --namespace <ns>     Kubernetes namespace (default: superai)
#   --release <name>     Helm release name (default: superai)
#   --method <method>    Deployment method: helm | kustomize (default: helm)
#   --overlay <name>     Kustomize overlay (default: prod)
#   --timeout <seconds>  Rollout timeout (default: 300)
#   --dry-run            Show what would be done without executing
#   --force              Skip confirmation prompt
#
# Exit codes:
#   0 - Rollback successful
#   1 - Rollback failed
#   2 - Rollback failed and restore was attempted
# ============================================================================
set -euo pipefail

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKUP_DIR="${PROJECT_ROOT}/backups/rollback"
AUDIT_LOG="${PROJECT_ROOT}/logs/rollback-audit.log"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"

# Defaults
NAMESPACE="superai"
RELEASE_NAME="superai"
METHOD="helm"
OVERLAY="prod"
TIMEOUT=300
DRY_RUN=false
FORCE=false
TARGET_VERSION=""

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <target-version> [--namespace <ns>] [--release <name>] [--method helm|kustomize] [--overlay <name>] [--timeout <s>] [--dry-run] [--force]"
    exit 1
fi

TARGET_VERSION="$1"; shift

while [[ $# -gt 0 ]]; do
    case "$1" in
        --namespace)  NAMESPACE="$2"; shift 2 ;;
        --release)    RELEASE_NAME="$2"; shift 2 ;;
        --method)     METHOD="$2"; shift 2 ;;
        --overlay)    OVERLAY="$2"; shift 2 ;;
        --timeout)    TIMEOUT="$2"; shift 2 ;;
        --dry-run)    DRY_RUN=true; shift ;;
        --force)      FORCE=true; shift ;;
        -h|--help)
            echo "Usage: $0 <target-version> [--namespace <ns>] [--release <name>] [--method helm|kustomize] [--overlay <name>] [--timeout <s>] [--dry-run] [--force]"
            exit 0
            ;;
        *) echo "ERROR: Unknown option: $1" >&2; exit 1 ;;
    esac
done

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
mkdir -p "$(dirname "${AUDIT_LOG}")" "${BACKUP_DIR}"

audit() {
    local ts
    ts="$(date '+%Y-%m-%d %H:%M:%S')"
    local msg="[${ts}] [ROLLBACK] $*"
    echo "${msg}" | tee -a "${AUDIT_LOG}"
}

info()    { audit "[INFO]    $*"; }
warn()    { audit "[WARN]    $*"; }
error()   { audit "[ERROR]   $*"; }
success() { audit "[SUCCESS] $*"; }

die() {
    error "$@"
    exit 1
}

# ---------------------------------------------------------------------------
# Validate prerequisites
# ---------------------------------------------------------------------------
validate_prerequisites() {
    info "Validating prerequisites..."

    case "${METHOD}" in
        helm)
            command -v helm &>/dev/null || die "helm is required for Helm rollback"
            command -v kubectl &>/dev/null || die "kubectl is required"
            ;;
        kustomize)
            command -v kubectl &>/dev/null || die "kubectl is required for Kustomize rollback"
            ;;
        *)
            die "Unknown method: ${METHOD}. Use 'helm' or 'kustomize'"
            ;;
    esac

    # Validate namespace exists
    if ! kubectl get namespace "${NAMESPACE}" &>/dev/null; then
        die "Namespace '${NAMESPACE}' does not exist"
    fi

    info "Prerequisites validated (method=${METHOD}, namespace=${NAMESPACE})"
}

# ---------------------------------------------------------------------------
# Backup current state
# ---------------------------------------------------------------------------
backup_current_state() {
    local backup_path="${BACKUP_DIR}/${TIMESTAMP}"
    mkdir -p "${backup_path}"

    info "Backing up current state to ${backup_path}..."

    # Backup all resources in the namespace
    local resource_types=("deployments" "services" "configmaps" "secrets" "ingresses" "hpa" "pdb")
    for rtype in "${resource_types[@]}"; do
        kubectl get "${rtype}" -n "${NAMESPACE}" -o yaml > "${backup_path}/${rtype}.yaml" 2>/dev/null || true
    done

    # Backup Helm state if using Helm
    if [[ "${METHOD}" == "helm" ]]; then
        helm get values "${RELEASE_NAME}" -n "${NAMESPACE}" > "${backup_path}/helm-values.yaml" 2>/dev/null || true
        helm get manifest "${RELEASE_NAME}" -n "${NAMESPACE}" > "${backup_path}/helm-manifest.yaml" 2>/dev/null || true

        local current_revision
        current_revision="$(helm history "${RELEASE_NAME}" -n "${NAMESPACE}" --max 1 -o json 2>/dev/null \
            | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0]['revision'] if d else 'unknown')" 2>/dev/null || echo "unknown")"
        echo "${current_revision}" > "${backup_path}/helm-revision.txt"
        info "Current Helm revision: ${current_revision}"
    fi

    # Record current image tags
    kubectl get deployments -n "${NAMESPACE}" -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.template.spec.containers[*].image}{"\n"}{end}' \
        > "${backup_path}/current-images.txt" 2>/dev/null || true

    # Save metadata
    cat > "${backup_path}/metadata.json" <<EOF
{
    "timestamp": "${TIMESTAMP}",
    "namespace": "${NAMESPACE}",
    "method": "${METHOD}",
    "release_name": "${RELEASE_NAME}",
    "target_version": "${TARGET_VERSION}",
    "operator": "$(whoami)",
    "hostname": "$(hostname)"
}
EOF

    info "Backup completed: ${backup_path}"
    echo "${backup_path}"
}

# ---------------------------------------------------------------------------
# Helm rollback
# ---------------------------------------------------------------------------
rollback_helm() {
    info "Executing Helm rollback to version ${TARGET_VERSION}..."

    # Check if target is a revision number or an image tag
    if [[ "${TARGET_VERSION}" =~ ^[0-9]+$ ]]; then
        # Numeric: treat as Helm revision number
        info "Rolling back to Helm revision ${TARGET_VERSION}"

        if [[ "${DRY_RUN}" == "true" ]]; then
            info "[DRY-RUN] Would execute: helm rollback ${RELEASE_NAME} ${TARGET_VERSION} -n ${NAMESPACE}"
            helm rollback "${RELEASE_NAME}" "${TARGET_VERSION}" -n "${NAMESPACE}" --dry-run 2>&1 || true
            return 0
        fi

        helm rollback "${RELEASE_NAME}" "${TARGET_VERSION}" \
            -n "${NAMESPACE}" \
            --wait \
            --timeout "${TIMEOUT}s" \
            2>&1
    else
        # Non-numeric: treat as image tag; upgrade with new tag
        info "Updating Helm release to image tag ${TARGET_VERSION}"

        if [[ "${DRY_RUN}" == "true" ]]; then
            info "[DRY-RUN] Would execute: helm upgrade ${RELEASE_NAME} ./helm --set image.tag=${TARGET_VERSION}"
            helm upgrade "${RELEASE_NAME}" "${PROJECT_ROOT}/helm" \
                -n "${NAMESPACE}" \
                --set "image.tag=${TARGET_VERSION}" \
                --dry-run \
                2>&1
            return 0
        fi

        helm upgrade "${RELEASE_NAME}" "${PROJECT_ROOT}/helm" \
            -n "${NAMESPACE}" \
            -f "${PROJECT_ROOT}/helm/values.yaml" \
            --set "image.tag=${TARGET_VERSION}" \
            --wait \
            --timeout "${TIMEOUT}s" \
            --atomic \
            2>&1
    fi
}

# ---------------------------------------------------------------------------
# Kustomize rollback
# ---------------------------------------------------------------------------
rollback_kustomize() {
    info "Executing Kustomize rollback to version ${TARGET_VERSION}..."

    local overlay_dir="${PROJECT_ROOT}/k8s/overlays/${OVERLAY}"
    if [[ ! -d "${overlay_dir}" ]]; then
        die "Kustomize overlay directory not found: ${overlay_dir}"
    fi

    # Update the image tag in the kustomization
    local kustomization_file="${overlay_dir}/kustomization.yaml"
    if [[ ! -f "${kustomization_file}" ]]; then
        die "kustomization.yaml not found in ${overlay_dir}"
    fi

    if [[ "${DRY_RUN}" == "true" ]]; then
        info "[DRY-RUN] Would update image tag to ${TARGET_VERSION} in ${kustomization_file}"
        info "[DRY-RUN] Would run: kubectl apply -k ${overlay_dir}"

        # Show diff
        cd "${PROJECT_ROOT}"
        kubectl diff -k "${overlay_dir}" 2>&1 || true
        return 0
    fi

    # Use kubectl set image on the live deployment
    info "Setting image tag to ${TARGET_VERSION} for deployments in ${NAMESPACE}..."

    local deployments
    deployments="$(kubectl get deployments -n "${NAMESPACE}" -o jsonpath='{.items[*].metadata.name}' 2>/dev/null)"

    for deploy in ${deployments}; do
        local current_image
        current_image="$(kubectl get deployment "${deploy}" -n "${NAMESPACE}" \
            -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null)"

        # Replace the tag portion of the image
        local image_base
        image_base="$(echo "${current_image}" | cut -d: -f1)"
        local new_image="${image_base}:${TARGET_VERSION}"

        info "  ${deploy}: ${current_image} -> ${new_image}"
        kubectl set image "deployment/${deploy}" \
            -n "${NAMESPACE}" \
            "$(kubectl get deployment "${deploy}" -n "${NAMESPACE}" -o jsonpath='{.spec.template.spec.containers[0].name}')=${new_image}" \
            2>&1
    done

    # Wait for rollout
    for deploy in ${deployments}; do
        info "  Waiting for rollout: ${deploy}..."
        kubectl rollout status "deployment/${deploy}" \
            -n "${NAMESPACE}" \
            --timeout="${TIMEOUT}s" \
            2>&1
    done
}

# ---------------------------------------------------------------------------
# Verify rollback
# ---------------------------------------------------------------------------
verify_rollback() {
    info "Verifying rollback..."
    local success=true

    # Check deployment status
    local deployments
    deployments="$(kubectl get deployments -n "${NAMESPACE}" -o jsonpath='{.items[*].metadata.name}' 2>/dev/null)"

    for deploy in ${deployments}; do
        local available
        available="$(kubectl get deployment "${deploy}" -n "${NAMESPACE}" \
            -o jsonpath='{.status.availableReplicas}' 2>/dev/null || echo "0")"
        local desired
        desired="$(kubectl get deployment "${deploy}" -n "${NAMESPACE}" \
            -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "0")"

        if [[ "${available}" == "${desired}" ]] && [[ "${available}" != "0" ]]; then
            info "  [OK] ${deploy}: ${available}/${desired} replicas available"
        else
            error "  [FAIL] ${deploy}: ${available}/${desired} replicas available"
            success=false
        fi
    done

    # Check pod status
    local not_ready
    not_ready="$(kubectl get pods -n "${NAMESPACE}" --field-selector=status.phase!=Running,status.phase!=Succeeded \
        -o name 2>/dev/null | wc -l)"
    if [[ "${not_ready}" -gt 0 ]]; then
        warn "  ${not_ready} pod(s) are not in Running/Succeeded state"
        kubectl get pods -n "${NAMESPACE}" --field-selector=status.phase!=Running,status.phase!=Succeeded 2>/dev/null || true
        success=false
    fi

    if [[ "${success}" == "true" ]]; then
        return 0
    else
        return 1
    fi
}

# ---------------------------------------------------------------------------
# Restore from backup
# ---------------------------------------------------------------------------
restore_from_backup() {
    local backup_path="$1"
    warn "Attempting to restore from backup: ${backup_path}"

    if [[ "${METHOD}" == "helm" ]]; then
        local prev_revision
        prev_revision="$(cat "${backup_path}/helm-revision.txt" 2>/dev/null || echo "")"
        if [[ -n "${prev_revision}" ]] && [[ "${prev_revision}" != "unknown" ]]; then
            info "Restoring Helm to revision ${prev_revision}..."
            helm rollback "${RELEASE_NAME}" "${prev_revision}" \
                -n "${NAMESPACE}" \
                --wait \
                --timeout "${TIMEOUT}s" \
                2>&1 || {
                error "Helm restore also failed. Manual intervention required."
                return 1
            }
        else
            warn "No previous Helm revision recorded; applying backup manifests..."
            kubectl apply -f "${backup_path}/deployments.yaml" -n "${NAMESPACE}" 2>/dev/null || true
            kubectl apply -f "${backup_path}/services.yaml" -n "${NAMESPACE}" 2>/dev/null || true
            kubectl apply -f "${backup_path}/configmaps.yaml" -n "${NAMESPACE}" 2>/dev/null || true
        fi
    else
        # Kustomize restore: re-apply backup manifests
        info "Restoring from backup manifests..."
        for manifest in "${backup_path}"/*.yaml; do
            [[ -f "${manifest}" ]] || continue
            kubectl apply -f "${manifest}" -n "${NAMESPACE}" 2>/dev/null || true
        done
    fi

    success "Restore from backup completed"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
    audit "========================================================================"
    audit "ROLLBACK INITIATED"
    audit "  Target Version: ${TARGET_VERSION}"
    audit "  Namespace:      ${NAMESPACE}"
    audit "  Method:         ${METHOD}"
    audit "  Release:        ${RELEASE_NAME}"
    audit "  Dry Run:        ${DRY_RUN}"
    audit "  Operator:       $(whoami)"
    audit "  Timestamp:      ${TIMESTAMP}"
    audit "========================================================================"

    # Confirmation prompt
    if [[ "${FORCE}" == "false" ]] && [[ "${DRY_RUN}" == "false" ]]; then
        echo ""
        echo "WARNING: You are about to rollback to version '${TARGET_VERSION}'"
        echo "  Namespace: ${NAMESPACE}"
        echo "  Method:    ${METHOD}"
        echo ""
        read -r -p "Continue? [y/N] " confirm
        if [[ "${confirm}" != "y" ]] && [[ "${confirm}" != "Y" ]]; then
            info "Rollback cancelled by operator"
            exit 0
        fi
    fi

    validate_prerequisites

    # Backup
    local backup_path
    backup_path="$(backup_current_state)"

    # Execute rollback
    local rollback_exit=0
    case "${METHOD}" in
        helm)      rollback_helm      || rollback_exit=$? ;;
        kustomize) rollback_kustomize || rollback_exit=$? ;;
    esac

    if [[ "${DRY_RUN}" == "true" ]]; then
        info "Dry run completed. No changes were applied."
        exit 0
    fi

    if [[ ${rollback_exit} -ne 0 ]]; then
        error "Rollback command failed (exit code: ${rollback_exit})"
        warn "Attempting automatic restore from backup..."
        restore_from_backup "${backup_path}"
        audit "ROLLBACK RESULT: FAILED - Restore attempted"
        exit 2
    fi

    # Verify
    if verify_rollback; then
        success "Rollback to '${TARGET_VERSION}' completed and verified"
        audit "ROLLBACK RESULT: SUCCESS"
        audit "  Backup retained at: ${backup_path}"
        exit 0
    else
        error "Rollback verification failed"
        warn "Attempting automatic restore from backup..."
        restore_from_backup "${backup_path}"
        audit "ROLLBACK RESULT: VERIFICATION FAILED - Restore attempted"
        exit 2
    fi
}

main "$@"
