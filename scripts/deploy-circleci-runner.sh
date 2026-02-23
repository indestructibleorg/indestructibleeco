#!/bin/bash

# CircleCI Self-Hosted Runner Deployment Script for GKE
# Project: IndestructibleEco

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
GCP_PROJECT="my-project-ops-1991"
GKE_REGION="asia-east1"
GKE_CLUSTER="eco-staging"
RUNNER_NAMESPACE="circleci-runner"

echo -e "${GREEN}=== CircleCI Self-Hosted Runner Deployment ===${NC}"
echo ""

# Check if CIRCLECI_RUNNER_TOKEN is set
if [ -z "$CIRCLECI_RUNNER_TOKEN" ]; then
    echo -e "${RED}Error: CIRCLECI_RUNNER_TOKEN environment variable is not set${NC}"
    echo "Please set it using: export CIRCLECI_RUNNER_TOKEN='your-token-here'"
    echo "Get your token from: https://app.circleci.com/settings/user/tokens"
    exit 1
fi

echo -e "${YELLOW}Step 1: Getting GKE credentials...${NC}"
gcloud container clusters get-credentials "$GKE_CLUSTER" --region="$GKE_REGION" --project="$GCP_PROJECT"
echo -e "${GREEN}✓ GKE credentials obtained${NC}"
echo ""

echo -e "${YELLOW}Step 2: Creating namespace...${NC}"
kubectl create namespace "$RUNNER_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
echo -e "${GREEN}✓ Namespace created${NC}"
echo ""

echo -e "${YELLOW}Step 3: Creating ConfigMap...${NC}"
kubectl apply -f k8s/circleci/configmap.yaml
echo -e "${GREEN}✓ ConfigMap created${NC}"
echo ""

echo -e "${YELLOW}Step 4: Creating Secret with runner token...${NC}"
kubectl create secret generic circleci-runner-secrets \
  --from-literal=CIRCLECI_RUNNER_TOKEN="$CIRCLECI_RUNNER_TOKEN" \
  --namespace="$RUNNER_NAMESPACE" \
  --dry-run=client -o yaml | kubectl apply -f -
echo -e "${GREEN}✓ Secret created${NC}"
echo ""

echo -e "${YELLOW}Step 5: Creating RBAC resources...${NC}"
kubectl apply -f k8s/circleci/rbac.yaml
echo -e "${GREEN}✓ RBAC resources created${NC}"
echo ""

echo -e "${YELLOW}Step 6: Deploying CircleCI agent...${NC}"
kubectl apply -f k8s/circleci/deployment.yaml
echo -e "${GREEN}✓ CircleCI agent deployed${NC}"
echo ""

echo -e "${YELLOW}Step 7: Waiting for deployment to be ready...${NC}"
kubectl rollout status deployment/circleci-agent -n "$RUNNER_NAMESPACE" --timeout=5m
echo -e "${GREEN}✓ Deployment is ready${NC}"
echo ""

echo -e "${GREEN}=== Deployment Complete ===${NC}"
echo ""
echo "CircleCI runner is now deployed to GKE cluster '$GKE_CLUSTER'"
echo ""
echo "To check the runner status:"
echo "  kubectl get pods -n $RUNNER_NAMESPACE"
echo ""
echo "To view agent logs:"
echo "  kubectl logs -f deployment/circleci-agent -n $RUNNER_NAMESPACE"
echo ""
echo "The runner will now be available in CircleCI with resource class 'eco/base'"