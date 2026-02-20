# IndestructibleEco Deployment Guide

URI: indestructibleeco://docs/DEPLOYMENT

## Prerequisites

- Kubernetes 1.28+
- Helm 3.14+
- Argo CD 2.10+
- Docker 24+
- kubectl configured for target cluster

## Local Development

```bash
# Start all services
docker compose up -d

# Verify health
curl http://localhost:8001/health  # AI service
curl http://localhost:3000/health  # API service
open http://localhost:5173         # Web frontend
open http://localhost:9090         # Prometheus
open http://localhost:3001         # Grafana
```

## Kubernetes Deployment

### 1. Create Namespace

```bash
kubectl apply -f k8s/base/namespace.qyaml
```

### 2. Deploy with Helm

```bash
helm install eco helm/ \
  --namespace indestructibleeco \
  --values helm/values.yaml \
  --set global.imageRegistry=ghcr.io/indestructibleorg
```

### 3. Staging Deployment

```bash
helm install eco-staging helm/ \
  --namespace indestructibleeco-staging \
  --values helm/values-staging.yaml
```

## Argo CD GitOps

### Install ApplicationSet

```bash
kubectl apply -f k8s/argocd/applicationset.yaml -n argocd
```

This creates two Argo CD Applications:
- `eco-staging` - tracks `develop` branch
- `eco-production` - tracks `main` branch (manual sync)

### Verify Sync

```bash
argocd app list
argocd app get eco-staging
argocd app get eco-production
```

## CI/CD Pipeline

5-gate pipeline (`.github/workflows/ci.yaml`):

1. **validate** - CI Validator Engine (8 validators)
2. **lint** - Python compile + JS syntax + YAML governance
3. **test** - Core tests + skill tests
4. **build** - Docker build + structure verification
5. **auto-fix** - Diagnostic mode on failure

## Monitoring

- **Prometheus**: `http://localhost:9090` - metrics collection
- **Grafana**: `http://localhost:3001` - AI service dashboard
- **Alert Rules**: `ecosystem/monitoring/alertmanager/alert-rules.yaml`

## Security

- **Trivy**: `.trivy.yaml` - vulnerability scanning
- **OPA**: `policy/` - governance policy enforcement
- **SBOM**: `sbom.json` - CycloneDX software bill of materials
