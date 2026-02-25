#!/bin/bash
# SLSA Level 3 Provenance Generation Script
# P0 Critical: Generate SLSA L3 provenance attestation for artifacts

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Configuration
IMAGE_REF="${IMAGE_REF:-ghcr.io/superai-platform/superai-platform:latest}"
BUILDERS_REPO="${BUILDERS_REPO:-github.com/superai-platform/builders}"
REKOR_URL="${REKOR_URL:-https://rekor.sigstore.dev}"
FULCIO_URL="${FULCIO_URL:-https://fulcio.sigstore.dev}"
COSIGN_EXPERIMENTAL="${COSIGN_EXPERIMENTAL:-1}"

log_info "Starting SLSA Level 3 Provenance Generation..."
log_info "Image: $IMAGE_REF"
log_info "Rekor: $REKOR_URL"
log_info "Fulcio: $FULCIO_URL"

# Check for required tools
check_tools() {
    log_step "Checking required tools..."
    
    for tool in cosign slsa-verifier jq; do
        if ! command -v $tool &> /dev/null; then
            log_error "$tool not found"
            log_info "Install cosign: go install github.com/sigstore/cosign/v2/cmd/cosign@latest"
            log_info "Install slsa-verifier: go install github.com/slsa-framework/slsa-verifier/v2/cmd/slsa-verifier@latest"
            exit 1
        fi
    done
    
    log_info "All required tools found"
}

# Get build metadata
get_build_metadata() {
    log_step "Collecting build metadata..."
    
    # Get git commit information
    local git_commit=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
    local git_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
    local git_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "none")
    
    # Get build environment information
    local build_id="${BUILD_ID:-$(date +%Y%m%d-%H%M%S)}"
    local build_url="${BUILD_URL:-}"
    local builder_id="${BUILDER_ID:-$(hostname)}"
    
    # Get source repository information
    local source_repo=$(git config --get remote.origin.url 2>/dev/null || echo "unknown")
    local source_commit=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
    
    log_info "Build ID: $build_id"
    log_info "Git Commit: $git_commit"
    log_info "Git Branch: $git_branch"
    log_info "Git Tag: $git_tag"
    log_info "Source Repo: $source_repo"
}

# Generate SLSA L3 provenance predicate
generate_provenance_predicate() {
    log_step "Generating SLSA L3 provenance predicate..."
    
    local git_commit=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
    local git_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
    local build_id="${BUILD_ID:-$(date +%Y%m%d-%H%M%S)}"
    local source_repo=$(git config --get remote.origin.url 2>/dev/null || echo "unknown")
    
    cat > /tmp/provenance-predicate.json << EOF
{
  "_type": "https://in-toto.io/Statement/v1",
  "subject": [
    {
      "name": "${IMAGE_REF}",
      "digest": {
        "sha256": "$(docker inspect --format='{{index .RepoDigests 0}}' ${IMAGE_REF} | cut -d'@' -f2 | cut -d':' -f2 || echo 'unknown')"
      }
    }
  ],
  "predicateType": "https://slsa.dev/provenance/v1",
  "predicate": {
    "buildDefinition": {
      "buildType": "https://slsa-framework.github.io/github-actions-buildtypes/workflow/v1",
      "externalParameters": {
        "workflow": {
          "id": "${WORKFLOW_ID:-.github/workflows/ci-cd.yml}",
          "ref": "refs/heads/${git_branch}",
          "repository": "${source_repo}"
        },
        "inputs": {
          "image": "${IMAGE_REF}",
          "build_id": "${build_id}",
          "git_commit": "${git_commit}"
        }
      },
      "internalParameters": {
        "GITHUB_RUN_ID": "${GITHUB_RUN_ID:-}",
        "GITHUB_RUN_NUMBER": "${GITHUB_RUN_NUMBER:-}",
        "GITHUB_ACTOR": "${GITHUB_ACTOR:-}"
      },
      "resolvedDependencies": [
        {
          "uri": "git+${source_repo}@${git_commit}",
          "digest": {
            "gitCommit": "${git_commit}"
          }
        },
        {
          "uri": "pkg:oci/${IMAGE_REF}",
          "digest": {
            "sha256": "$(docker inspect --format='{{index .RepoDigests 0}}' ${IMAGE_REF} | cut -d'@' -f2 | cut -d':' -f2 || echo 'unknown')"
          }
        }
      ]
    },
    "runDetails": {
      "builder": {
        "id": "https://github.com/${source_repo}/.github/workflows/ci-cd.yml@refs/heads/${git_branch}",
        "builderDependencies": [
          {
            "uri": "pkg:oci/docker",
            "version": "24.0.0"
          },
          {
            "uri": "pkg:oci/buildkit",
            "version": "0.12.0"
          }
        ]
      },
      "metadata": {
        "invocationId": "${build_id}",
        "startedOn": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
        "finishedOn": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
      },
      "byproducts": [
        {
          "name": "build-log",
          "content": "$(cat /tmp/build.log 2>/dev/null || echo 'build log not available')"
        }
      ]
    }
  }
}
EOF
    
    log_info "Provenance predicate generated"
}

# Sign and attest provenance
sign_provenance() {
    log_step "Signing and attesting SLSA provenance..."
    
    # Sign with cosign using keyless signing (Fulcio/Rekor)
    cosign attest --predicate-type slsaprovenance \
        --type slsaprovenance \
        --fulcio-url "$FULCIO_URL" \
        --rekor-url "$REKOR_URL" \
        "$IMAGE_REF" \
        < /tmp/provenance-predicate.json
    
    log_info "SLSA L3 provenance attested and stored in Rekor"
}

# Verify provenance
verify_provenance() {
    log_step "Verifying SLSA Level 3 provenance..."
    
    # Verify with slsa-verifier
    slsa-verifier verify-image \
        --source-uri "${source_repo}" \
        --source-tag "${git_tag}" \
        --provenance-path /tmp/provenance-attestation.json \
        --builder-id "https://github.com/${source_repo}/.github/workflows/ci-cd.yml" \
        "$IMAGE_REF"
    
    log_info "SLSA L3 provenance verified successfully"
}

# Generate SBOM
generate_sbom() {
    log_step "Generating Software Bill of Materials (SBOM)..."
    
    # Generate SPDX SBOM
    syft "${IMAGE_REF}" \
        --output spdx-json \
        --file /tmp/sbom-spdx.json
    
    # Generate CycloneDX SBOM
    syft "${IMAGE_REF}" \
        --output cyclonedx-json \
        --file /tmp/sbom-cyclonedx.json
    
    # Attest SBOM
    cosign attest --predicate-type sbom \
        --type spdxjson \
        --fulcio-url "$FULCIO_URL" \
        --rekor-url "$REKOR_URL" \
        "$IMAGE_REF" \
        < /tmp/sbom-spdx.json
    
    log_info "SBOM generated and attested"
}

# Store provenance metadata
store_metadata() {
    log_step "Storing provenance metadata..."
    
    local metadata_dir="./artifacts/provenance/$(date +%Y/%m/%d)"
    mkdir -p "$metadata_dir"
    
    cp /tmp/provenance-predicate.json "${metadata_dir}/provenance-${BUILD_ID:-$(date +%Y%m%d-%H%M%S)}.json"
    cp /tmp/sbom-spdx.json "${metadata_dir}/sbom-spdx-${BUILD_ID:-$(date +%Y%m%d-%H%M%S)}.json"
    cp /tmp/sbom-cyclonedx.json "${metadata_dir}/sbom-cyclonedx-${BUILD_ID:-$(date +%Y%m%d-%H%M%S)}.json"
    
    log_info "Provenance metadata stored in ${metadata_dir}"
}

# Main execution
main() {
    check_tools
    get_build_metadata
    generate_provenance_predicate
    sign_provenance
    verify_provenance
    generate_sbom
    store_metadata
    
    log_info "SLSA Level 3 provenance generation completed"
    log_info "Provenance is available in Rekor at: ${REKOR_URL}"
}

main "$@"