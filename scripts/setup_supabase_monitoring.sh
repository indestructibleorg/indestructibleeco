#!/bin/bash
# Supabase Monitoring Setup Script for IndestructibleEco
# This script deploys Prometheus and Grafana for Supabase Pro monitoring

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="monitoring"
SUPABASE_PROJECT_REF="yrfxijooswpvdpdseswy"
GRAFANA_PASSWORD="${GRAFANA_PASSWORD:-admin123}"

echo -e "${GREEN}=== Supabase Monitoring Setup ===${NC}"
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

# Prompt for Supabase secret key
echo -e "${YELLOW}Please provide your Supabase Secret API key${NC}"
echo "You can find it in Project Settings → API Keys"
read -sp "Enter Supabase Secret API key (sb_secret_...): " SUPABASE_SECRET_KEY
echo ""

if [[ ! $SUPABASE_SECRET_KEY =~ ^sb_secret_ ]]; then
    echo -e "${RED}Error: Invalid Supabase Secret API key format${NC}"
    echo "Secret API key should start with 'sb_secret_'"
    exit 1
fi

# Create namespace
echo -e "${GREEN}Creating monitoring namespace...${NC}"
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Deploy Node Exporter
echo -e "${GREEN}Deploying Node Exporter...${NC}"
kubectl apply -f monitoring/k8s/node-exporter-daemonset.yaml

# Deploy Prometheus
echo -e "${GREEN}Deploying Prometheus...${NC}"
kubectl apply -f monitoring/k8s/prometheus-deployment.yaml

# Update Prometheus secret with Supabase key
echo -e "${GREEN}Configuring Prometheus with Supabase credentials...${NC}"
kubectl create secret generic prometheus-secrets \
  --from-literal=SUPABASE_SECRET_KEY="$SUPABASE_SECRET_KEY" \
  --namespace=$NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart Prometheus to pick up new secret
kubectl rollout restart deployment/prometheus -n $NAMESPACE

# Deploy Grafana
echo -e "${GREEN}Deploying Grafana...${NC}"
kubectl apply -f monitoring/k8s/grafana-deployment.yaml

# Update Grafana admin password
echo -e "${GREEN}Configuring Grafana admin credentials...${NC}"
kubectl create secret generic grafana-secrets \
  --from-literal=admin-user="admin" \
  --from-literal=admin-password="$GRAFANA_PASSWORD" \
  --namespace=$NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart Grafana to pick up new secret
kubectl rollout restart deployment/grafana -n $NAMESPACE

# Wait for deployments to be ready
echo -e "${GREEN}Waiting for deployments to be ready...${NC}"
kubectl wait --for=condition=available --timeout=300s \
  deployment/prometheus -n $NAMESPACE
kubectl wait --for=condition=available --timeout=300s \
  deployment/grafana -n $NAMESPACE

# Get service URLs
echo ""
echo -e "${GREEN}=== Setup Complete ===${NC}"
echo ""
echo "Monitoring stack deployed successfully!"
echo ""
echo "Access URLs:"
echo "  Prometheus: https://prometheus._cf-custom-hostname.autoecoops.io"
echo "  Grafana:    https://grafana._cf-custom-hostname.autoecoops.io"
echo ""
echo "Grafana Credentials:"
echo "  Username: admin"
echo "  Password: $GRAFANA_PASSWORD"
echo ""
echo "Supabase Project: $SUPABASE_PROJECT_REF"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Access Grafana at http://grafana.indestructibleeco.io"
echo "2. Login with the credentials above"
echo "3. Navigate to Dashboards → Supabase → Supabase Overview"
echo "4. Verify metrics are being collected"
echo ""
echo -e "${YELLOW}Testing Supabase Metrics API:${NC}"
echo "Run the following command to test the metrics endpoint:"
echo ""
echo "curl https://$SUPABASE_PROJECT_REF.supabase.co/customer/v1/privileged/metrics \&quot;
echo "  --user 'service_role:$SUPABASE_SECRET_KEY'"
echo ""