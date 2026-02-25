# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: documentation
# @ECO-audit-trail: ../../engine/governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated
# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: documentation
# @ECO-audit-trail: ../../engine/governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated
# MachineNativeOps Enterprise Deployment Guide

This guide provides comprehensive instructions for deploying MachineNativeOps in enterprise environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Deployment Methods](#deployment-methods)
3. [Kubernetes Deployment](#kubernetes-deployment)
4. [Docker Compose Deployment](#docker-compose-deployment)
5. [Terraform Infrastructure](#terraform-infrastructure)
6. [CI/CD Pipeline](#cicd-pipeline)
7. [Monitoring and Logging](#monitoring-and-logging)
8. [Backup and Recovery](#backup-and-recovery)
9. [Security Configuration](#security-configuration)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools

- **Kubernetes**: v1.24+
- **Docker**: v20.10+
- **Helm**: v3.10+
- **Terraform**: v1.5+
- **kubectl**: v1.24+
- **Git**: v2.30+

### Required Accounts

- Cloud provider account (AWS/GCP/Azure)
- Container registry access (GHCR, ECR, GCR, or ACR)
- Monitoring and alerting accounts (optional)

## Deployment Methods

MachineNativeOps supports multiple deployment methods:

1. **Kubernetes with Helm** (Recommended for production)
2. **Docker Compose** (For development and testing)
3. **Terraform** (For infrastructure provisioning)
4. **CI/CD Pipeline** (For automated deployments)

## Kubernetes Deployment

### Prerequisites

```bash
# Install kubectl
curl -LO "[EXTERNAL_URL_REMOVED] -L -s [EXTERNAL_URL_REMOVED])/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Install Helm
curl [EXTERNAL_URL_REMOVED] | bash
```

### Quick Start

```bash
# Clone the repository
git clone [EXTERNAL_URL_REMOVED]
cd machine-native-ops

# Create namespace
kubectl create namespace machine-native-ops

# Deploy with Helm
helm install machine-native-ops ./deployment/helm/machine-native-ops \
  --namespace machine-native-ops \
  --create-namespace \
  --values deployment/helm/machine-native-ops/values.yaml \
  --wait
```

### Custom Deployment

```bash
# Create custom values file
cat > custom-values.yaml << EOF
global:
  environment: production

image:
  repository: ghcr.io/machinenativeops/machine-native-ops-core
  tag: "1.0.0"

resources:
  limits:
    cpu: 4000m
    memory: 8Gi
  requests:
    cpu: 1000m
    memory: 2Gi

monitoring:
  prometheus:
    enabled: true
  grafana:
    enabled: true
EOF

# Deploy with custom values
helm upgrade --install machine-native-ops ./deployment/helm/machine-native-ops \
  --namespace machine-native-ops \
  --values custom-values.yaml \
  --wait
```

### Verify Deployment

```bash
# Check pod status
kubectl get pods -n machine-native-ops

# Check services
kubectl get services -n machine-native-ops

# Check deployment status
kubectl rollout status deployment/machine-native-ops -n machine-native-ops

# View logs
kubectl logs -f deployment/machine-native-ops -n machine-native-ops
```

## Docker Compose Deployment

### Prerequisites

```bash
# Install Docker Compose
sudo curl -L "[EXTERNAL_URL_REMOVED] -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Quick Start

```bash
# Clone the repository
git clone [EXTERNAL_URL_REMOVED]
cd machine-native-ops/deployment/docker-compose

# Copy environment file
cp .env.example .env

# Edit environment variables
nano .env

# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### Service URLs

- **MachineNativeOps**: [EXTERNAL_URL_REMOVED]
- **Grafana**: [EXTERNAL_URL_REMOVED] (admin/admin)
- **Prometheus**: [EXTERNAL_URL_REMOVED]
- **Kibana**: [EXTERNAL_URL_REMOVED]
- **Jaeger**: [EXTERNAL_URL_REMOVED]

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Terraform Infrastructure

### Prerequisites

```bash
# Install Terraform
wget -O- [EXTERNAL_URL_REMOVED] | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] [EXTERNAL_URL_REMOVED] $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform
```

### AWS Deployment

```bash
cd deployment/terraform

# Configure AWS credentials
aws configure

# Initialize Terraform
terraform init

# Plan deployment
terraform plan -out=tfplan

# Apply deployment
terraform apply tfplan

# Get cluster credentials
aws eks update-kubeconfig --name machine-native-ops-prod --region us-east-1

# Deploy applications with Helm
helm install machine-native-ops ./deployment/helm/machine-native-ops \
  --namespace machine-native-ops \
  --create-namespace
```

## CI/CD Pipeline

### GitHub Actions Setup

1. **Configure Secrets in GitHub Repository**:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `GITHUB_TOKEN` (auto-provided)
   - `SLACK_WEBHOOK_URL`
   - `SNYK_TOKEN`

2. **Push Code to Trigger Pipeline**:
   ```bash
   git add .
   git commit -m "feat: new feature"
   git push origin main
   ```

3. **Monitor Pipeline**:
   - Go to GitHub Actions tab
   - View workflow runs
   - Check logs for each job

## Monitoring and Logging

### Prometheus and Grafana

**Access Grafana**:
```bash
# Port forward to local machine
kubectl port-forward -n machine-native-ops svc/grafana 3000:3000

# Open browser
open [EXTERNAL_URL_REMOVED]
```

### Elasticsearch and Kibana

**Access Kibana**:
```bash
# Port forward to local machine
kubectl port-forward -n machine-native-ops svc/kibana 5601:5601

# Open browser
open [EXTERNAL_URL_REMOVED]
```

## Security Configuration

### Update Secrets

```bash
# Generate strong passwords
openssl rand -base64 32

# Update secrets
kubectl create secret generic machine-native-ops-secrets \
  --from-literal=database-password=$(openssl rand -base64 32) \
  --from-literal=encryption-key=$(openssl rand -base64 32) \
  --from-literal=api-secret-key=$(openssl rand -base64 32) \
  --dry-run=client -o yaml | kubectl apply -f -
```

## Troubleshooting

### Common Issues

**Pods not starting**:
```bash
# Check pod status
kubectl describe pod <pod-name> -n machine-native-ops

# Check logs
kubectl logs <pod-name> -n machine-native-ops

# Check events
kubectl get events -n machine-native-ops --sort-by='.lastTimestamp'
```

**Service not accessible**:
```bash
# Check service endpoints
kubectl get endpoints -n machine-native-ops

# Check network policies
kubectl get networkpolicies -n machine-native-ops
```

## Support

For issues and questions:
- GitHub Issues: [EXTERNAL_URL_REMOVED]
- Documentation: [EXTERNAL_URL_REMOVED]
- Email: support@machinenativeops.com