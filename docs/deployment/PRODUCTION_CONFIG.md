# Production Configuration Guide

## Overview
This document provides the complete configuration required for deploying the Ecosystem v1.0 to production.

## Prerequisites

### Kubernetes Cluster Requirements
- **Version**: Kubernetes 1.27+
- **Nodes**: Minimum 3 nodes
- **Resources per node**: 4 CPU, 8GB RAM
- **Storage**: 100GB persistent storage
- **Network**: VPC with proper networking configuration

### Required Secrets
The following GitHub Secrets must be configured:

```
SUPABASE_URL=https://yrfxijooswpvdpdseswy.supabase.co
SUPABASE_ANON_KEY=sb_publishable_rhTyBa4IqqV14nV_B87S7g_zKzDSYTd
SUPABASE_SERVICE_ROLE_KEY=sbp_7ece928e1564d8d4fe481ca4d85b6dbc5b3d022d
ANTHROPIC_API_KEY=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
GROQ_API_KEY=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
CLOUDFLARE_API_TOKEN=wpKocLGuX5W-YmV8Z_qrhSneX48xf93uxYdSKc-D
CLOUDFLARE_API_TOKEN_READ=Vl2I3FAEsuH8uj1X_viZYKnK3bHn3Oa47FGt4gNi
```

### Additional Required Secrets
These must be added to the Kubernetes cluster:

```
KUBE_CONFIG_STAGING: Base64-encoded kubeconfig for staging cluster
KUBE_CONFIG_PRODUCTION: Base64-encoded kubeconfig for production cluster
KUBE_CONFIG_DEV: Base64-encoded kubeconfig for development cluster
DATABASE_URL: PostgreSQL connection string
JWT_SECRET: Random secret for JWT signing
ARGOCD_SERVER: ArgoCD server URL
ARGOCD_PASSWORD: ArgoCD admin password
SLACK_WEBHOOK: Slack webhook for notifications
```

## Deployment Architecture

### Namespaces
- `ecosystem-staging`: Staging environment
- `ecosystem-production`: Production environment

### Services

#### Client (Frontend)
- **Image**: `ghcr.io/machops/ecosystem/client:latest`
- **Replicas**: 2 (staging), 3 (production)
- **Port**: 3000
- **Resources**:
  - Requests: 100m CPU, 128Mi memory
  - Limits: 500m CPU, 512Mi memory

#### Server (Backend)
- **Image**: `ghcr.io/machops/ecosystem/server:latest`
- **Replicas**: 2 (staging), 3 (production)
- **Port**: 8080
- **Resources**:
  - Requests: 200m CPU, 256Mi memory
  - Limits: 1000m CPU, 1Gi memory

## Deployment Steps

### 1. Configure Kubernetes Secrets

```bash
# Create namespace
kubectl create namespace ecosystem-production

# Create secrets
kubectl create secret generic ecosystem-secrets \
  --from-literal=supabase-url=https://yrfxijooswpvdpdseswy.supabase.co \
  --from-literal=supabase-anon-key=sb_publishable_rhTyBa4IqqV14nV_B87S7g_zKzDSYTd \
  --from-literal=supabase-service-role-key=sbp_7ece928e1564d8d4fe481ca4d85b6dbc5b3d022d \
  --from-literal=anthropic-api-key=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 \
  --from-literal=groq-api-key=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 \
  --from-literal=cloudflare-api-token=wpKocLGuX5W-YmV8Z_qrhSneX48xf93uxYdSKc-D \
  --from-literal=jwt-secret=<generate-random-secret> \
  --from-literal=database-url=<postgresql-connection-string> \
  -n ecosystem-production
```

### 2. Deploy to Staging

The CD pipeline will automatically deploy to staging when code is pushed to the main branch and passes CI checks.

### 3. Deploy to Production

Production deployment requires manual approval in the GitHub Actions workflow.

## Monitoring and Observability

### Health Checks
- **Client**: HTTP GET on `/` port 3000
- **Server**: HTTP GET on `/health` port 8080

### Logs
```bash
# View client logs
kubectl logs -f deployment/client -n ecosystem-production

# View server logs
kubectl logs -f deployment/server -n ecosystem-production
```

### Metrics
Configure Prometheus to scrape metrics from:
- Client service: `http://client.ecosystem-production.svc.cluster.local:80/metrics`
- Server service: `http://server.ecosystem-production.svc.cluster.local:80/metrics`

## Rollback Procedure

```bash
# Rollback to previous deployment
kubectl rollout undo deployment/client -n ecosystem-production
kubectl rollout undo deployment/server -n ecosystem-production

# View rollout history
kubectl rollout history deployment/client -n ecosystem-production
kubectl rollout history deployment/server -n ecosystem-production
```

## Troubleshooting

### Pods not starting
```bash
kubectl describe pod <pod-name> -n ecosystem-production
kubectl logs <pod-name> -n ecosystem-production
```

### Service not accessible
```bash
kubectl get endpoints -n ecosystem-production
kubectl describe service <service-name> -n ecosystem-production
```

### Image pull errors
Ensure the GitHub token has proper permissions to pull from GHCR.

## Security Considerations

1. **Network Policies**: Implement network policies to restrict traffic
2. **Pod Security Standards**: Apply pod security policies
3. **RBAC**: Configure proper role-based access control
4. **Secrets Management**: Use external secret management (e.g., Sealed Secrets, External Secrets Operator)
5. **Image Scanning**: Enable vulnerability scanning in CI/CD

## Performance Tuning

### Horizontal Pod Autoscaling
Configure HPA based on CPU/memory metrics:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: server-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: server
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Resource Limits
Adjust resource limits based on actual usage patterns.

## Backup and Recovery

### Database Backups
Configure regular backups of Supabase database.

### Configuration Backups
Backup Kubernetes manifests and configurations:

```bash
kubectl get all -n ecosystem-production -o yaml > backup-$(date +%Y%m%d).yaml
```

## Support and Maintenance

For issues or questions:
- Check logs: `kubectl logs -f <pod-name> -n ecosystem-production`
- Review deployment status: `kubectl get deployments -n ecosystem-production`
- Monitor metrics in Grafana
- Check GitHub Actions workflow runs