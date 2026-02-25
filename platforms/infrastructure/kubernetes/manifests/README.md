# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: documentation
# @ECO-audit-trail: ../../engine/governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated
# @ECO-governed
# @ECO-layer: infrastructure
# @ECO-semantic: kubernetes-manifests-readme
# @ECO-audit-trail: ../../engine/governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated
# Kubernetes Manifests Documentation

## Overview

This directory contains the complete Kubernetes manifests for the MachineNativeOps infrastructure following best practices for cloud-native deployments.

## Directory Structure

```
infrastructure/kubernetes/manifests/
├── base/                      # Base manifests (common across environments)
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── serviceaccount.yaml
│   ├── networkpolicy.yaml
│   ├── limitrange.yaml
│   ├── resourcequota.yaml
│   ├── ingress.yaml
│   ├── hpa.yaml
│   ├── poddisruptionbudget.yaml
│   └── kustomization.yaml
├── systems/                   # System-specific deployments
│   ├── engine/
│   ├── file-organizer-system/
│   ├── instant/
│   ├── elasticsearch-search-system/
│   └── esync-platform/
└── overlays/                  # Environment-specific overlays
    ├── dev/
    ├── staging/
    └── production/
```

## Best Practices Implemented

### 1. GL Governance Integration
- All manifests include GL governance markers
- Semantic annotations for audit trails
- Governance labels for tracking compliance

### 2. Resource Management
- **Resource Quotas**: Namespace-level resource limits
- **Limit Ranges**: Default resource requests/limits for containers
- **HPA**: Horizontal Pod Autoscaling for scalability
- **PDB**: PodDisruptionBudget for high availability

### 3. Security
- **Network Policies**: Restrict pod-to-pod communication
- **Service Accounts**: Dedicated service accounts with minimal permissions
- **Secrets Management**: External secret management integration
- **RBAC**: Role-based access control

### 4. Observability
- **Probes**: Liveness and readiness probes for health checks
- **Metrics**: Prometheus metrics endpoints exposed
- **Labels**: Consistent labeling for monitoring and tracing

### 5. Configuration Management
- **ConfigMaps**: Non-sensitive configuration
- **Secrets**: Sensitive data (managed externally)
- **Kustomize**: Environment-specific overlays

## Deployment

### Prerequisites
- Kubernetes cluster (v1.24+)
- kubectl configured
- kustomize installed
- External secret management (e.g., Sealed Secrets, External Secrets Operator)

### Deploy to Development
```bash
kubectl apply -k infrastructure/kubernetes/manifests/overlays/dev
```

### Deploy to Staging
```bash
kubectl apply -k infrastructure/kubernetes/manifests/overlays/staging
```

### Deploy to Production
```bash
kubectl apply -k infrastructure/kubernetes/manifests/overlays/production
```

## Verification

### Check Deployment Status
```bash
kubectl get pods -n machine-native-ops
kubectl get services -n machine-native-ops
kubectl get ingress -n machine-native-ops
```

### Check Governance Compliance
```bash
kubectl get pods -n machine-native-ops -L governance.machinenativeops.io/layer
kubectl get pods -n machine-native-ops -L governance.machinenativeops.io/charter-version
```

## System-Specific Endpoints

| System | Internal Service | External Endpoint |
|--------|-----------------|-------------------|
| AEP Engine | aep-engine-service:80 | [EXTERNAL_URL_REMOVED] |
| File Organizer | file-organizer-service:80 | [EXTERNAL_URL_REMOVED] |
| Instant System | instant-service:80 | [EXTERNAL_URL_REMOVED] |
| Elasticsearch | elasticsearch-search-service:80 | [EXTERNAL_URL_REMOVED] |
| ESync Platform | esync-platform-service:80 | [EXTERNAL_URL_REMOVED] |

## Maintenance

### Updating Images
Modify the `images` section in the appropriate overlay kustomization.yaml

### Scaling
Adjust replica counts in the overlay kustomization.yaml

### Adding New Systems
1. Create directory in `systems/<system-name>/`
2. Add deployment.yaml and service.yaml
3. Include GL governance markers
4. Add to overlay kustomization.yaml resources

## GL Compliance

All manifests comply with GL Unified Architecture Governance Framework v2.0.0
