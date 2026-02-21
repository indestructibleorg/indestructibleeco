#!/bin/bash
# Complete Secrets Configuration Script for IndestructibleEco
# This script configures all GCP, Supabase, and Cloudflare secrets

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== IndestructibleEco Complete Secrets Configuration ===${NC}"
echo ""

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl is not installed${NC}"
    exit 1
fi

# Check if user is logged in to kubectl
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}Error: Not connected to Kubernetes cluster${NC}"
    exit 1
fi

# Configuration
NAMESPACE="indestructibleeco"
MONITORING_NAMESPACE="monitoring"

echo -e "${GREEN}Step 1: Configuring GCP Service Account Secret${NC}"
kubectl create secret generic gcp-sa-key \
  --from-file=.gcp/eco-deployer-key.json \
  --namespace=$NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -
echo -e "${GREEN}✓ GCP Service Account secret configured${NC}"
echo ""

echo -e "${GREEN}Step 2: Configuring Supabase Secrets${NC}"
# Required environment variables (no defaults to prevent accidental deployment with placeholder values):
# SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_DB_URL, SUPABASE_JWT_SECRET
for var in SUPABASE_ANON_KEY SUPABASE_SERVICE_ROLE_KEY SUPABASE_DB_URL SUPABASE_JWT_SECRET; do
  if [[ -z "${!var}" ]]; then
    echo -e "${RED}Error: Required environment variable $var is not set${NC}"
    exit 1
  fi
done
kubectl create secret generic supabase-secrets \
  --from-literal=SUPABASE_URL="https://yrfxijooswpvdpdseswy.supabase.co" \
  --from-literal=SUPABASE_ANON_KEY="${SUPABASE_ANON_KEY}" \
  --from-literal=SUPABASE_SERVICE_ROLE_KEY="${SUPABASE_SERVICE_ROLE_KEY}" \
  --from-literal=SUPABASE_DB_URL="${SUPABASE_DB_URL}" \
  --from-literal=SUPABASE_JWT_SECRET="${SUPABASE_JWT_SECRET}" \
  --from-literal=SUPABASE_PROJECT_REF="yrfxijooswpvdpdseswy" \
  --namespace=$NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -
echo -e "${GREEN}✓ Supabase secrets configured${NC}"
echo ""

echo -e "${GREEN}Step 3: Configuring Cloudflare Origin Certificate${NC}"
kubectl create secret tls cloudflare-origin-cert \
  --cert=.cloudflare/cloudflare-origin-cert.pem \
  --key=.cloudflare/cloudflare-origin-key.key \
  --namespace=$MONITORING_NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -
echo -e "${GREEN}✓ Cloudflare origin certificate configured${NC}"
echo ""

echo -e "${GREEN}Step 4: Configuring Prometheus Secrets${NC}"
kubectl create secret generic prometheus-secrets \
  --from-literal=SUPABASE_SECRET_KEY="${SUPABASE_SERVICE_ROLE_KEY:-sb_secret_31vU-HAOwfR81zlaDWa_hQ_EHmtoqS8}" \
  --namespace=$MONITORING_NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -
echo -e "${GREEN}✓ Prometheus secrets configured${NC}"
echo ""

echo -e "${GREEN}Step 5: Configuring Grafana Secrets${NC}"
GRAFANA_PASSWORD="${GRAFANA_PASSWORD:-IndestructibleEco2026!}"
kubectl create secret generic grafana-secrets \
  --from-literal=admin-user="admin" \
  --from-literal=admin-password="$GRAFANA_PASSWORD" \
  --namespace=$MONITORING_NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -
echo -e "${GREEN}✓ Grafana secrets configured${NC}"
echo ""

echo -e "${GREEN}Step 6: Verifying Secrets${NC}"
echo ""
echo "GCP Service Account Secret:"
kubectl get secret gcp-sa-key -n $NAMESPACE
echo ""
echo "Supabase Secrets:"
kubectl get secret supabase-secrets -n $NAMESPACE
echo ""
echo "Cloudflare Certificate:"
kubectl get secret cloudflare-origin-cert -n $MONITORING_NAMESPACE
echo ""
echo "Prometheus Secrets:"
kubectl get secret prometheus-secrets -n $MONITORING_NAMESPACE
echo ""
echo "Grafana Secrets:"
kubectl get secret grafana-secrets -n $MONITORING_NAMESPACE
echo ""

echo -e "${GREEN}=== Configuration Complete ===${NC}"
echo ""
echo -e "${YELLOW}All secrets have been configured successfully!${NC}"
echo ""
echo -e "${BLUE}Grafana Credentials:${NC}"
echo "  Username: admin"
echo "  Password: $GRAFANA_PASSWORD"
echo ""
echo -e "${BLUE}Access URLs:${NC}"
echo "  Prometheus: https://prometheus._cf-custom-hostname.autoecoops.io"
echo "  Grafana:    https://grafana._cf-custom-hostname.autoecoops.io"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Deploy monitoring stack: ./scripts/setup_supabase_monitoring.sh"
echo "2. Configure Cloudflare DNS records"
echo "3. Verify SSL certificates"
echo ""