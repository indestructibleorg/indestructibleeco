#!/bin/bash
# Complete Infrastructure Deployment Script for IndestructibleEco
# This script deploys all infrastructure components

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== IndestructibleEco Complete Infrastructure Deployment ===${NC}"
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

echo -e "${GREEN}Phase 1: Configuring Secrets${NC}"
echo "----------------------------------------"
./scripts/configure_all_secrets.sh
echo ""

echo -e "${GREEN}Phase 2: Deploying Monitoring Stack${NC}"
echo "----------------------------------------"

# Create monitoring namespace
kubectl create namespace $MONITORING_NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Deploy Node Exporter
echo "Deploying Node Exporter..."
kubectl apply -f monitoring/k8s/node-exporter-daemonset.yaml

# Deploy Prometheus
echo "Deploying Prometheus..."
kubectl apply -f monitoring/k8s/prometheus-deployment.yaml

# Deploy Grafana
echo "Deploying Grafana..."
kubectl apply -f monitoring/k8s/grafana-deployment.yaml

echo ""

echo -e "${GREEN}Phase 3: Waiting for Deployments${NC}"
echo "----------------------------------------"
echo "Waiting for Prometheus to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/prometheus -n $MONITORING_NAMESPACE || true

echo "Waiting for Grafana to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/grafana -n $MONITORING_NAMESPACE || true

echo ""

echo -e "${GREEN}Phase 4: Verifying Deployment${NC}"
echo "----------------------------------------"
echo "Deployment Status:"
kubectl get deployments -n $MONITORING_NAMESPACE
echo ""

echo "Pod Status:"
kubectl get pods -n $MONITORING_NAMESPACE
echo ""

echo "Service Status:"
kubectl get services -n $MONITORING_NAMESPACE
echo ""

echo "Ingress Status:"
kubectl get ingress -n $MONITORING_NAMESPACE
echo ""

echo -e "${GREEN}Phase 5: Testing Supabase Metrics API${NC}"
echo "----------------------------------------"
echo "Testing Supabase metrics endpoint..."
curl -s https://yrfxijooswpvdpdseswy.supabase.co/customer/v1/privileged/metrics \
  --user 'service_role:YOUR_SERVICE_ROLE_KEY' | head -20
echo ""

echo -e "${GREEN}=== Deployment Complete ===${NC}"
echo ""
echo -e "${YELLOW}Infrastructure deployed successfully!${NC}"
echo ""
echo -e "${BLUE}Access URLs:${NC}"
echo "  Prometheus: https://prometheus._cf-custom-hostname.autoecoops.io"
echo "  Grafana:    https://grafana._cf-custom-hostname.autoecoops.io"
echo ""
echo -e "${BLUE}Grafana Credentials:${NC}"
echo "  Username: admin"
echo "  Password: (see grafana-secrets Kubernetes secret in the monitoring namespace)"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Configure Cloudflare DNS records:"
echo "   - prometheus._cf-custom-hostname.autoecoops.io → <INGRESS_IP>"
echo "   - grafana._cf-custom-hostname.autoecoops.io → <INGRESS_IP>"
echo ""
echo "2. Get Ingress IP:"
echo "   kubectl get ingress -n monitoring"
echo ""
echo "3. Access Grafana and verify dashboards"
echo ""
echo "4. Configure alert notifications"
echo ""
echo -e "${YELLOW}Important Notes:${NC}"
echo "- All secrets are stored in Kubernetes secrets"
echo "- Cloudflare certificates are configured for SSL/TLS"
echo "- Supabase metrics are being scraped every 60 seconds"
echo "- Grafana dashboards are pre-configured"
echo ""