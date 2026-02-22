#!/bin/bash
# Cloudflare Certificate Setup Script for IndestructibleEco
# This script helps you create Kubernetes secrets from Cloudflare certificates

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Cloudflare Certificate Setup ===${NC}"
echo ""

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl is not installed${NC}"
    exit 1
fi

# Check if base64 is available
if ! command -v base64 &> /dev/null; then
    echo -e "${RED}Error: base64 is not available${NC}"
    exit 1
fi

# Prompt for certificate file
echo -e "${YELLOW}Please provide the Cloudflare Origin Certificate${NC}"
echo "You can find it in Cloudflare Dashboard → SSL/TLS → Origin Server"
read -p "Enter path to certificate file (e.g., cloudflare-origin-cert.pem): " CERT_FILE

if [ ! -f "$CERT_FILE" ]; then
    echo -e "${RED}Error: Certificate file not found: $CERT_FILE${NC}"
    exit 1
fi

# Prompt for private key file
echo ""
echo -e "${YELLOW}Please provide the Cloudflare Origin Private Key${NC}"
echo "You can find it in Cloudflare Dashboard → SSL/TLS → Origin Server"
read -p "Enter path to private key file (e.g., cloudflare-origin-key.key): " KEY_FILE

if [ ! -f "$KEY_FILE" ]; then
    echo -e "${RED}Error: Private key file not found: $KEY_FILE${NC}"
    exit 1
fi

# Encode files to base64
echo ""
echo -e "${GREEN}Encoding certificates to base64...${NC}"
CERT_BASE64=$(cat "$CERT_FILE" | base64 -w 0)
KEY_BASE64=$(cat "$KEY_FILE" | base64 -w 0)

# Create secret
echo -e "${GREEN}Creating Kubernetes secret...${NC}"
kubectl create secret tls cloudflare-origin-cert \
  --cert="$CERT_FILE" \
  --key="$KEY_FILE" \
  --namespace=monitoring \
  --dry-run=client -o yaml | kubectl apply -f -

# Update Ingress resources to use Cloudflare certificate
echo ""
echo -e "${GREEN}Updating Ingress resources to use Cloudflare certificate...${NC}"

# Update Prometheus Ingress
kubectl patch ingress prometheus-ingress -n monitoring -p '{
  "spec": {
    "tls": [{
      "hosts": ["prometheus._cf-custom-hostname.autoecoops.io"],
      "secretName": "cloudflare-origin-cert"
    }]
  }
}' --type=merge

# Update Grafana Ingress
kubectl patch ingress grafana-ingress -n monitoring -p '{
  "spec": {
    "tls": [{
      "hosts": ["grafana._cf-custom-hostname.autoecoops.io"],
      "secretName": "cloudflare-origin-cert"
    }]
  }
}' --type=merge

echo ""
echo -e "${GREEN}=== Setup Complete ===${NC}"
echo ""
echo "Cloudflare certificates have been configured successfully!"
echo ""
echo "Access URLs:"
echo "  Prometheus: https://prometheus._cf-custom-hostname.autoecoops.io"
echo "  Grafana:    https://grafana._cf-custom-hostname.autoecoops.io"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Verify the certificates are working by accessing the URLs above"
echo "2. Check that the SSL certificate is valid (issued by Cloudflare)"
echo "3. Update Cloudflare DNS to point to your Kubernetes ingress IP"
echo ""
echo -e "${YELLOW}Note:${NC}"
echo "Make sure your Cloudflare DNS records point to your Kubernetes ingress IP:"
echo "  prometheus._cf-custom-hostname.autoecoops.io → <INGRESS_IP>"
echo "  grafana._cf-custom-hostname.autoecoops.io → <INGRESS_IP>"
echo ""