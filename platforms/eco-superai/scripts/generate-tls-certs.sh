#!/bin/bash
# TLS Certificate Infrastructure Setup Script
# P0 Critical: Automated TLS certificate generation for K8s

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

# Default configuration
CERTS_DIR="${CERTS_DIR:-./certs}"
ENVIRONMENT="${ENVIRONMENT:-prod}"
DOMAIN="${DOMAIN:-superai.platform}"
VALIDITY_DAYS="${VALIDITY_DAYS:-365}"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    log_warn "This script should be run as root for certificate installation"
    log_warn "Certificates will be generated in current directory"
fi

log_info "Starting TLS Certificate Generation..."
log_info "Environment: $ENVIRONMENT"
log_info "Domain: $DOMAIN"
log_info "Output directory: $CERTS_DIR"

# Create certificates directory
mkdir -p "$CERTS_DIR"
cd "$CERTS_DIR"

# Step 1: Generate Root CA Certificate
log_step "Generating Root CA Certificate..."
cat > ca.conf << EOF
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_ca
prompt = no

[req_distinguished_name]
C = US
ST = California
L = San Francisco
O = SuperAI Platform
OU = Certificate Authority
CN = SuperAI Root CA

[v3_ca]
basicConstraints = critical,CA:TRUE,pathlen:1
keyUsage = critical, digitalSignature, cRLSign, keyCertSign
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer
EOF

openssl genrsa -out root-ca.key 4096
openssl req -new -x509 -days ${VALIDITY_DAYS} -key root-ca.key -out root-ca.crt -config ca.conf

log_info "Root CA certificate generated"
log_info "  Private key: root-ca.key"
log_info "  Certificate: root-ca.crt"

# Step 2: Generate Intermediate CA Certificate
log_step "Generating Intermediate CA Certificate..."
cat > intermediate.conf << EOF
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_intermediate_ca
prompt = no

[req_distinguished_name]
C = US
ST = California
L = San Francisco
O = SuperAI Platform
OU = Certificate Authority
CN = SuperAI Intermediate CA

[v3_intermediate_ca]
basicConstraints = critical,CA:TRUE,pathlen:0
keyUsage = critical, digitalSignature, cRLSign, keyCertSign
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer
EOF

openssl genrsa -out intermediate-ca.key 4096
openssl req -new -key intermediate-ca.key -out intermediate-ca.csr -config intermediate.conf
openssl x509 -req -days ${VALIDITY_DAYS} -in intermediate-ca.csr -CA root-ca.crt -CAkey root-ca.key -CAcreateserial -out intermediate-ca.crt -extfile intermediate.conf -extensions v3_intermediate_ca

log_info "Intermediate CA certificate generated"
log_info "  Private key: intermediate-ca.key"
log_info "  Certificate: intermediate-ca.crt"

# Step 3: Generate Server Certificate
log_step "Generating Server Certificate for $DOMAIN..."

# Generate SAN list
cat > server.conf << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = California
L = San Francisco
O = SuperAI Platform
OU = $ENVIRONMENT Environment
CN = $DOMAIN

[v3_req]
basicConstraints = critical,CA:FALSE
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth, clientAuth
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer

[alt_names]
DNS.1 = $DOMAIN
DNS.2 = *.$DOMAIN
DNS.3 = localhost
DNS.4 = api.$DOMAIN
DNS.5 = app.$DOMAIN
DNS.6 = grafana.$DOMAIN
DNS.7 = prometheus.$DOMAIN
IP.1 = 127.0.0.1
IP.2 = ::1
EOF

# Add alt_names section to v3_req
sed -i '/\[v3_req\]/a subjectAltName=@alt_names' server.conf

openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr -config server.conf
openssl x509 -req -days $((VALIDITY_DAYS / 2)) -in server.csr -CA intermediate-ca.crt -CAkey intermediate-ca.key -CAcreateserial -out server.crt -extfile server.conf -extensions v3_req

log_info "Server certificate generated"
log_info "  Private key: server.key"
log_info "  Certificate: server.crt"

# Step 4: Generate Client Certificate (for mTLS)
log_step "Generating Client Certificate for mTLS..."
cat > client.conf << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = California
L = San Francisco
O = SuperAI Platform
OU = Client Authentication
CN = SuperAI Client

[v3_req]
basicConstraints = critical,CA:FALSE
keyUsage = critical, digitalSignature
extendedKeyUsage = clientAuth
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer
EOF

openssl genrsa -out client.key 2048
openssl req -new -key client.key -out client.csr -config client.conf
openssl x509 -req -days $((VALIDITY_DAYS / 2)) -in client.csr -CA intermediate-ca.crt -CAkey intermediate-ca.key -CAcreateserial -out client.crt -extfile client.conf -extensions v3_req

log_info "Client certificate generated"
log_info "  Private key: client.key"
log_info "  Certificate: client.crt"

# Step 5: Generate PKCS#12 bundle for client (optional)
log_step "Generating PKCS#12 bundle..."
openssl pkcs12 -export -out client.p12 -inkey client.key -in client.crt -certfile intermediate-ca.crt -passout pass:changeit

log_info "PKCS#12 bundle generated: client.p12"

# Step 6: Generate Certificate Chain
log_step "Generating certificate chain..."
cat server.crt intermediate-ca.crt > server-chain.crt

log_info "Certificate chain generated: server-chain.crt"

# Step 7: Generate Trust Store (Java format)
log_step "Generating Java trust store..."
if command -v keytool &> /dev/null; then
    keytool -importcert -alias superai-root-ca -file root-ca.crt -keystore truststore.jks -storepass changeit -noprompt 2>/dev/null || log_warn "keytool not available, skipping Java trust store"
    keytool -importcert -alias superai-intermediate-ca -file intermediate-ca.crt -keystore truststore.jks -storepass changeit -noprompt 2>/dev/null || true
    log_info "Java trust store generated: truststore.jks"
else
    log_warn "keytool not available, skipping Java trust store"
fi

# Step 8: Set appropriate permissions
log_step "Setting file permissions..."
chmod 600 *.key
chmod 644 *.crt *.p12 *.jks

# Step 9: Generate certificate info
log_step "Certificate information:"
echo ""
echo "=== Root CA ==="
openssl x509 -in root-ca.crt -text -noout | grep -A 2 "Subject:"
openssl x509 -in root-ca.crt -text -noout | grep -A 2 "Validity"
echo ""
echo "=== Server Certificate ==="
openssl x509 -in server.crt -text -noout | grep -A 2 "Subject:"
openssl x509 -in server.crt -text -noout | grep -A 2 "Validity"
echo ""

# Step 10: Generate k8s secret manifest (if kubectl available)
log_step "Generating Kubernetes secrets..."
if command -v kubectl &> /dev/null; then
    cat > k8s-tls-secrets.yaml << EOF
apiVersion: v1
kind: Secret
metadata:
  name: superai-tls
  namespace: default
type: kubernetes.io/tls
data:
  tls.crt: $(cat server.crt | base64 -w 0)
  tls.key: $(cat server.key | base64 -w 0)
---
apiVersion: v1
kind: Secret
metadata:
  name: superai-ca
  namespace: default
type: Opaque
data:
  ca.crt: $(cat root-ca.crt | base64 -w 0)
---
apiVersion: v1
kind: Secret
metadata:
  name: superai-client-tls
  namespace: default
type: kubernetes.io/tls
data:
  tls.crt: $(cat client.crt | base64 -w 0)
  tls.key: $(cat client.key | base64 -w 0)
EOF
    log_info "K8s secrets manifest generated: k8s-tls-secrets.yaml"
else
    log_warn "kubectl not available, skipping K8s secrets generation"
fi

# Step 11: Generate verification script
log_step "Generating certificate verification script..."
cat > verify-certs.sh << 'VERIFY_EOF'
#!/bin/bash
echo "Verifying certificates..."

echo "Verifying server certificate..."
if openssl verify -CAfile intermediate-ca.crt -untrusted root-ca.crt server.crt; then
    echo "Server certificate: VALID"
else
    echo "Server certificate: INVALID"
    exit 1
fi

echo "Verifying client certificate..."
if openssl verify -CAfile intermediate-ca.crt -untrusted root-ca.crt client.crt; then
    echo "Client certificate: VALID"
else
    echo "Client certificate: INVALID"
    exit 1
fi

echo "Verifying certificate chain..."
if openssl verify -CAfile root-ca.crt server-chain.crt; then
    echo "Certificate chain: VALID"
else
    echo "Certificate chain: INVALID"
    exit 1
fi

echo "All certificates verified successfully!"
VERIFY_EOF

chmod +x verify-certs.sh
log_info "Verification script generated: verify-certs.sh"

# Final summary
log_info "TLS Certificate Infrastructure Setup Complete!"
echo ""
echo "Generated files:"
echo "  - root-ca.key, root-ca.crt (Root CA)"
echo "  - intermediate-ca.key, intermediate-ca.crt (Intermediate CA)"
echo "  - server.key, server.crt, server-chain.crt (Server)"
echo "  - client.key, client.crt, client.p12 (Client for mTLS)"
echo "  - truststore.jks (Java trust store)"
echo "  - k8s-tls-secrets.yaml (K8s secrets)"
echo "  - verify-certs.sh (Verification script)"
echo ""
log_info "Next steps:"
echo "  1. Review and securely store CA private keys"
echo "  2. Install root-ca.crt on all systems that trust this CA"
echo "  3. Apply k8s-tls-secrets.yaml to your Kubernetes cluster"
echo "  4. Run ./verify-certs.sh to verify all certificates"
echo ""
log_warn "SECURITY REMINDER: Keep private keys secure and never commit them to version control!"