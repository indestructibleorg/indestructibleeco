#!/usr/bin/env bash
# ============================================================================
# SuperAI Platform — TLS Certificate Generation
# ============================================================================
# Usage: ./scripts/generate-certs.sh [--domain api.superai.example.com] [--output-dir ./certs]
# Generates self-signed CA + server certs for dev/staging, or creates
# cert-manager ClusterIssuer for production Let's Encrypt.
# ============================================================================
set -euo pipefail

DOMAIN="${DOMAIN:-api.superai.example.com}"
OUTPUT_DIR="${OUTPUT_DIR:-./certs}"
CERT_DAYS="${CERT_DAYS:-365}"
CA_DAYS="${CA_DAYS:-3650}"
KEY_SIZE="${KEY_SIZE:-4096}"
ENV="${APP_ENV:-development}"
NAMESPACE="${NAMESPACE:-superai}"

log_info()  { echo "[certs] $(date -u +%FT%TZ) INFO  $*"; }
log_error() { echo "[certs] $(date -u +%FT%TZ) ERROR $*" >&2; }

# --- Parse arguments ---
while [[ $# -gt 0 ]]; do
    case "$1" in
        --domain)     DOMAIN="$2"; shift 2 ;;
        --output-dir) OUTPUT_DIR="$2"; shift 2 ;;
        --days)       CERT_DAYS="$2"; shift 2 ;;
        --env)        ENV="$2"; shift 2 ;;
        --namespace)  NAMESPACE="$2"; shift 2 ;;
        *) log_error "Unknown argument: $1"; exit 1 ;;
    esac
done

mkdir -p "${OUTPUT_DIR}"

if [ "${ENV}" = "production" ]; then
    # --- Production: Generate cert-manager manifests ---
    log_info "Generating cert-manager manifests for production..."

    cat > "${OUTPUT_DIR}/cluster-issuer.yaml" << EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
  labels:
    app.kubernetes.io/name: superai-platform
    app.kubernetes.io/component: tls
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@superai.example.com
    privateKeySecretRef:
      name: letsencrypt-prod-account-key
    solvers:
      - http01:
          ingress:
            class: nginx
---
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-staging
spec:
  acme:
    server: https://acme-staging-v02.api.letsencrypt.org/directory
    email: admin@superai.example.com
    privateKeySecretRef:
      name: letsencrypt-staging-account-key
    solvers:
      - http01:
          ingress:
            class: nginx
EOF

    cat > "${OUTPUT_DIR}/certificate.yaml" << EOF
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: superai-tls
  namespace: ${NAMESPACE}
  labels:
    app.kubernetes.io/name: superai-platform
    app.kubernetes.io/component: tls
spec:
  secretName: superai-prod-tls
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
    - ${DOMAIN}
    - "*.${DOMAIN#*.}"
  duration: 2160h    # 90 days
  renewBefore: 720h  # 30 days before expiry
  privateKey:
    algorithm: ECDSA
    size: 256
EOF

    log_info "Generated: ${OUTPUT_DIR}/cluster-issuer.yaml"
    log_info "Generated: ${OUTPUT_DIR}/certificate.yaml"
    log_info "Apply with: kubectl apply -f ${OUTPUT_DIR}/"

else
    # --- Dev/Staging: Generate self-signed certificates ---
    if ! command -v openssl &>/dev/null; then
        log_error "openssl not found."
        exit 1
    fi

    log_info "Generating self-signed CA and server certificates..."
    log_info "Domain: ${DOMAIN}"

    # --- CA Key and Certificate ---
    openssl genrsa -out "${OUTPUT_DIR}/ca.key" "${KEY_SIZE}" 2>/dev/null
    openssl req -x509 -new -nodes \
        -key "${OUTPUT_DIR}/ca.key" \
        -sha256 \
        -days "${CA_DAYS}" \
        -out "${OUTPUT_DIR}/ca.crt" \
        -subj "/C=TW/ST=Taiwan/L=Taipei/O=SuperAI/OU=Platform/CN=SuperAI CA" \
        2>/dev/null

    log_info "CA certificate: ${OUTPUT_DIR}/ca.crt"

    # --- Server Key and CSR ---
    openssl genrsa -out "${OUTPUT_DIR}/server.key" "${KEY_SIZE}" 2>/dev/null

    cat > "${OUTPUT_DIR}/server.cnf" << EOF
[req]
default_bits = ${KEY_SIZE}
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = v3_req

[dn]
C = TW
ST = Taiwan
L = Taipei
O = SuperAI
OU = Platform
CN = ${DOMAIN}

[v3_req]
basicConstraints = CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = ${DOMAIN}
DNS.2 = *.${DOMAIN#*.}
DNS.3 = localhost
DNS.4 = superai-app.${NAMESPACE}.svc.cluster.local
IP.1 = 127.0.0.1
EOF

    openssl req -new \
        -key "${OUTPUT_DIR}/server.key" \
        -out "${OUTPUT_DIR}/server.csr" \
        -config "${OUTPUT_DIR}/server.cnf" \
        2>/dev/null

    # --- Sign server certificate with CA ---
    openssl x509 -req \
        -in "${OUTPUT_DIR}/server.csr" \
        -CA "${OUTPUT_DIR}/ca.crt" \
        -CAkey "${OUTPUT_DIR}/ca.key" \
        -CAcreateserial \
        -out "${OUTPUT_DIR}/server.crt" \
        -days "${CERT_DAYS}" \
        -sha256 \
        -extensions v3_req \
        -extfile "${OUTPUT_DIR}/server.cnf" \
        2>/dev/null

    # --- Create K8s TLS secret manifest ---
    cat > "${OUTPUT_DIR}/tls-secret.yaml" << EOF
apiVersion: v1
kind: Secret
metadata:
  name: superai-dev-tls
  namespace: ${NAMESPACE}
  labels:
    app.kubernetes.io/name: superai-platform
    app.kubernetes.io/component: tls
type: kubernetes.io/tls
data:
  tls.crt: $(base64 -w0 "${OUTPUT_DIR}/server.crt")
  tls.key: $(base64 -w0 "${OUTPUT_DIR}/server.key")
  ca.crt: $(base64 -w0 "${OUTPUT_DIR}/ca.crt")
EOF

    # --- Cleanup intermediate files ---
    rm -f "${OUTPUT_DIR}/server.csr" "${OUTPUT_DIR}/server.cnf" "${OUTPUT_DIR}/ca.srl"

    log_info "Server certificate: ${OUTPUT_DIR}/server.crt"
    log_info "Server key: ${OUTPUT_DIR}/server.key"
    log_info "K8s secret: ${OUTPUT_DIR}/tls-secret.yaml"

    # --- Verify ---
    openssl x509 -in "${OUTPUT_DIR}/server.crt" -noout -text 2>/dev/null | grep -E "Subject:|DNS:|Not After" | head -5
    log_info "Certificate generation completed."
fi