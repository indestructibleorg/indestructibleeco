#!/usr/bin/env bash
# ============================================================================
# SuperAI Platform — Container Image Signing & Verification
# ============================================================================
# Usage:
#   Sign:   ./scripts/image-sign.sh sign <image:tag>
#   Verify: ./scripts/image-sign.sh verify <image:tag>
# Requires: cosign (https://github.com/sigstore/cosign)
# ============================================================================
set -euo pipefail

REGISTRY="${REGISTRY:-ghcr.io/indestructibleautoops}"
COSIGN_KEY="${COSIGN_KEY:-cosign.key}"
COSIGN_PUB="${COSIGN_PUB:-cosign.pub}"

log_info()  { echo "[image-sign] $(date -u +%FT%TZ) INFO  $*"; }
log_error() { echo "[image-sign] $(date -u +%FT%TZ) ERROR $*" >&2; }

# --- Pre-flight ---
check_cosign() {
    if ! command -v cosign &>/dev/null; then
        log_error "cosign not found. Install: https://docs.sigstore.dev/cosign/installation/"
        exit 1
    fi
    log_info "cosign version: $(cosign version 2>&1 | head -1)"
}

# --- Generate keypair (one-time setup) ---
cmd_generate_keys() {
    check_cosign
    if [ -f "${COSIGN_KEY}" ]; then
        log_error "Key already exists: ${COSIGN_KEY}. Remove it first to regenerate."
        exit 1
    fi
    log_info "Generating cosign keypair..."
    cosign generate-key-pair
    log_info "Keys generated: ${COSIGN_KEY}, ${COSIGN_PUB}"
    log_info "IMPORTANT: Store ${COSIGN_KEY} securely. Add ${COSIGN_PUB} to your repo."
}

# --- Sign image ---
cmd_sign() {
    local IMAGE="$1"
    check_cosign

    if [ ! -f "${COSIGN_KEY}" ]; then
        log_error "Signing key not found: ${COSIGN_KEY}"
        log_error "Run: $0 generate-keys"
        exit 1
    fi

    # Resolve full image reference
    if [[ "${IMAGE}" != *"/"* ]]; then
        IMAGE="${REGISTRY}/superai-platform:${IMAGE}"
    fi

    log_info "Signing image: ${IMAGE}"

    # Sign with key
    cosign sign \
        --key "${COSIGN_KEY}" \
        --annotations "repo=IndestructibleAutoOps/indestructibleautoops" \
        --annotations "build-date=$(date -u +%FT%TZ)" \
        --annotations "signed-by=superai-ci" \
        "${IMAGE}"

    log_info "Image signed successfully: ${IMAGE}"

    # Attach SBOM if syft is available
    if command -v syft &>/dev/null; then
        log_info "Generating and attaching SBOM..."
        syft "${IMAGE}" -o spdx-json > /tmp/sbom.spdx.json
        cosign attach sbom --sbom /tmp/sbom.spdx.json "${IMAGE}"
        rm -f /tmp/sbom.spdx.json
        log_info "SBOM attached."
    fi
}

# --- Verify image ---
cmd_verify() {
    local IMAGE="$1"
    check_cosign

    if [ ! -f "${COSIGN_PUB}" ]; then
        log_error "Public key not found: ${COSIGN_PUB}"
        exit 1
    fi

    if [[ "${IMAGE}" != *"/"* ]]; then
        IMAGE="${REGISTRY}/superai-platform:${IMAGE}"
    fi

    log_info "Verifying image signature: ${IMAGE}"

    cosign verify \
        --key "${COSIGN_PUB}" \
        "${IMAGE}" 2>&1

    VERIFY_EXIT=$?
    if [ ${VERIFY_EXIT} -eq 0 ]; then
        log_info "Signature verification PASSED: ${IMAGE}"
    else
        log_error "Signature verification FAILED: ${IMAGE}"
        exit 1
    fi

    # Verify SBOM if attached
    if cosign verify-attestation --key "${COSIGN_PUB}" "${IMAGE}" &>/dev/null; then
        log_info "SBOM attestation verified."
    fi
}

# --- Scan image for vulnerabilities ---
cmd_scan() {
    local IMAGE="$1"

    if [[ "${IMAGE}" != *"/"* ]]; then
        IMAGE="${REGISTRY}/superai-platform:${IMAGE}"
    fi

    if command -v trivy &>/dev/null; then
        log_info "Scanning image with Trivy: ${IMAGE}"
        trivy image \
            --severity HIGH,CRITICAL \
            --exit-code 1 \
            --no-progress \
            --format table \
            "${IMAGE}"
        log_info "Vulnerability scan completed."
    elif command -v grype &>/dev/null; then
        log_info "Scanning image with Grype: ${IMAGE}"
        grype "${IMAGE}" --fail-on high
        log_info "Vulnerability scan completed."
    else
        log_error "No scanner found. Install trivy or grype."
        exit 1
    fi
}

# --- Main ---
ACTION="${1:-help}"
shift || true

case "${ACTION}" in
    sign)
        [ $# -lt 1 ] && { log_error "Usage: $0 sign <image:tag>"; exit 1; }
        cmd_sign "$1"
        ;;
    verify)
        [ $# -lt 1 ] && { log_error "Usage: $0 verify <image:tag>"; exit 1; }
        cmd_verify "$1"
        ;;
    scan)
        [ $# -lt 1 ] && { log_error "Usage: $0 scan <image:tag>"; exit 1; }
        cmd_scan "$1"
        ;;
    generate-keys)
        cmd_generate_keys
        ;;
    *)
        echo "SuperAI Platform — Image Signing & Verification"
        echo ""
        echo "Usage: $0 <command> [args]"
        echo ""
        echo "Commands:"
        echo "  generate-keys          Generate cosign keypair"
        echo "  sign <image:tag>       Sign a container image"
        echo "  verify <image:tag>     Verify image signature"
        echo "  scan <image:tag>       Scan image for vulnerabilities"
        exit 0
        ;;
esac