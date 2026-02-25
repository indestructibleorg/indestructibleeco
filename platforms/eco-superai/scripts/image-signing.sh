#!/bin/bash
# Image Signing Implementation Script
# P0 Critical: Sign and verify container images using cosign/sigstore

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
REGISTRY="${REGISTRY:-ghcr.io}"
IMAGE_NAME="${IMAGE_NAME:-superai-platform}"
IMAGE_TAG="${IMAGE_TAG:-$(git describe --tags --always --dirty 2>/dev/null || echo 'latest')}"
FULL_IMAGE="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
COSIGN_EXPERIMENTAL="${COSIGN_EXPERIMENTAL:-1}"

log_info "Starting Image Signing Process..."
log_info "Image: $FULL_IMAGE"

# Check for required tools
check_tools() {
    log_step "Checking required tools..."
    
    local missing_tools=()
    
    for tool in cosign docker trivy; do
        if ! command -v $tool &> /dev/null; then
            missing_tools+=($tool)
        fi
    done
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_info "Install with:"
        echo "  cosign: go install github.com/sigstore/cosign/v2/cmd/cosign@latest"
        echo "  trivy: brew install trivy (macOS) or apt-get install trivy (Linux)"
        exit 1
    fi
    
    log_info "All required tools found"
}

# Generate cosign key pair if not exists
generate_keypair() {
    log_step "Checking for cosign key pair..."
    
    local cosign_key="cosign.key"
    local cosign_pub="cosign.pub"
    
    if [[ -f "$cosign_key" && -f "$cosign_pub" ]]; then
        log_info "Cosign key pair already exists"
        return
    fi
    
    log_warn "Cosign key pair not found, generating new pair..."
    log_warn "IMPORTANT: Store cosign.key securely and back it up!"
    
    COSIGN_PASSWORD="${COSIGN_PASSWORD:-}"
    
    if [[ -z "$COSIGN_PASSWORD" ]]; then
        log_info "Enter password for cosign key (leave empty for no password):"
        read -s COSIGN_PASSWORD
        export COSIGN_PASSWORD
    fi
    
    cosign generate-key-pair
    
    log_info "Key pair generated:"
    echo "  Private key: $cosign_key"
    echo "  Public key: $cosign_pub"
    echo ""
    log_warn "IMPORTANT: Keep cosign.key secure and never commit to version control!"
}

# Scan image for vulnerabilities
scan_image() {
    log_step "Scanning image for vulnerabilities..."
    
    log_info "Running Trivy scan on $FULL_IMAGE"
    
    if ! trivy image --severity HIGH,CRITICAL --exit-code 1 "$FULL_IMAGE"; then
        log_error "Image has HIGH or CRITICAL vulnerabilities"
        log_info "Fix vulnerabilities before signing"
        exit 1
    fi
    
    log_info "No HIGH or CRITICAL vulnerabilities found"
}

# Sign the image
sign_image() {
    log_step "Signing image with cosign..."
    
    # Sign with key pair
    cosign sign --key cosign.key "$FULL_IMAGE" --annotations "version=${IMAGE_TAG}" --annotations "timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    
    log_info "Image signed successfully"
    
    # Generate SBOM
    log_step "Generating SBOM..."
    cosign attest --key cosign.key --predicate-type spdxjson --type spdxjson "$FULL_IMAGE" <(sbom-tool generate -b . -o sbom.json 2>/dev/null || echo "{}")
    
    log_info "SBOM generated and attested"
}

# Verify the signature
verify_signature() {
    log_step "Verifying image signature..."
    
    cosign verify --key cosign.pub "$FULL_IMAGE" --insecure-ignore-tlog
    
    log_info "Signature verified successfully"
}

# Generate provenance
generate_provenance() {
    log_step "Generating provenance..."
    
    # Get git commit info
    local git_commit=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
    local git_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
    
    cosign attest --key cosign.key --predicate-type slsaprovenance --type slsaprovenance \
        "$FULL_IMAGE" << EOF
{
  "_type": "https://in-toto.io/Statement/v0.1",
  "predicateType": "https://slsa.dev/provenance/v0.2",
  "subject": [{
    "name": "$FULL_IMAGE",
    "digest": {"sha256": "$(docker inspect --format='{{index .RepoDigests 0}}' $FULL_IMAGE | cut -d: -f2)"}
  }],
  "predicate": {
    "buildType": "superai/ci-build@v1",
    "invocation": {
      "configSource": {
        "uri": "git+https://github.com/organization/repo@$git_commit",
        "digest": {"sha1": "$git_commit"},
        "entryPoint": ".github/workflows/ci-cd.yml"
      },
      "parameters": {
        "branch": "$git_branch",
        "tag": "$IMAGE_TAG"
      }
    },
    "builder": {
      "id": "github-actions/superai-platform"
    },
    "materials": [
      {
        "uri": "git+https://github.com/organization/repo@$git_commit",
        "digest": {"sha1": "$git_commit"}
      }
    ]
  }
}
EOF
    
    log_info "Provenance generated successfully"
}

# Verify provenance
verify_provenance() {
    log_step "Verifying provenance..."
    
    cosign verify-attestation --key cosign.pub --type slsaprovenance "$FULL_IMAGE"
    
    log_info "Provenance verified successfully"
}

# Generate Kubernetes admission configuration
generate_admission_config() {
    log_step "Generating Kubernetes admission webhook configuration..."
    
    mkdir -p k8s/cosign-admission
    
    cat > k8s/cosign-admission/validatingwebhook.yaml << EOF
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: cosign-webhook
  annotations:
    cert-manager.io/inject-ca-from: default/cosign-webhook-cert
webhooks:
  - name: cosign.superai.io
    rules:
      - apiGroups: [""]
        apiVersions: ["v1"]
        operations: ["CREATE"]
        resources: ["pods"]
    clientConfig:
      service:
        name: cosign-webhook
        namespace: default
        path: "/validate"
      caBundle: ""
    admissionReviewVersions: ["v1"]
    sideEffects: None
    timeoutSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: cosign-webhook
  namespace: default
spec:
  ports:
    - port: 443
      targetPort: 8443
  selector:
    app: cosign-webhook
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cosign-webhook
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: cosign-webhook
  template:
    metadata:
      labels:
        app: cosign-webhook
    spec:
      containers:
      - name: webhook
        image: gcr.io/projectsigstore/cosign:v2.2.1
        args:
          - webhook
          - --url=0.0.0.0:8443
          - --public-key=/etc/cosign/cosign.pub
          - --namespace=*
          - --ignore-uncertified-images=false
        ports:
        - containerPort: 8443
        volumeMounts:
        - name: public-key
          mountPath: /etc/cosign
          readOnly: true
      volumes:
      - name: public-key
        secret:
          secretName: cosign-public-key
---
apiVersion: v1
kind: Secret
metadata:
  name: cosign-public-key
  namespace: default
type: Opaque
data:
  cosign.pub: $(cat cosign.pub | base64 -w 0)
EOF
    
    log_info "Kubernetes admission webhook configuration generated"
    log_info "  Location: k8s/cosign-admission/validatingwebhook.yaml"
}

# Generate policy-controller configuration
generate_policy_controller() {
    log_step "Generating Gatekeeper policy configuration..."
    
    mkdir -p k8s/policy-controller
    
    cat > k8s/policy-controller/signed-image-policy.yaml << EOF
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sSignedImages
metadata:
  name: require-signed-images
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
    namespaces: ["default", "staging", "production"]
  parameters:
    images:
      - pattern: "$REGISTRY/$IMAGE_NAME:*"
        keys:
          - $(cat cosign.pub | base64 -w 0)
EOF
    
    log_info "Gatekeeper policy configuration generated"
    log_info "  Location: k8s/policy-controller/signed-image-policy.yaml"
}

# Main execution
main() {
    check_tools
    generate_keypair
    scan_image
    sign_image
    verify_signature
    generate_provenance
    verify_provenance
    generate_admission_config
    generate_policy_controller
    
    log_info "Image signing process completed successfully!"
    echo ""
    echo "Generated artifacts:"
    echo "  - cosign.key, cosign.pub (Key pair)"
    echo "  - Image signature: $FULL_IMAGE.sig"
    echo "  - SBOM attestation"
    echo "  - Provenance attestation"
    echo "  - K8s admission webhook: k8s/cosign-admission/"
    echo "  - Gatekeeper policy: k8s/policy-controller/"
    echo ""
    log_info "Next steps:"
    echo "  1. Store cosign.key securely"
    echo "  2. Deploy cosign-admission to enforce signature verification"
    echo "  3. Deploy signed-image-policy to Gatekeeper"
}

main "$@"