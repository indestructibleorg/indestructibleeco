# @ECO-layer: GQS-L0
<!-- @ECO-governed -->
<!-- @ECO-layer: GL90-99 -->
<!-- @ECO-semantic: governed-documentation -->
<!-- @ECO-audit-trail: engine/governance/GL_SEMANTIC_ANCHOR.json -->

# Quantum Naming Governance Deployment

This directory contains Kubernetes deployment manifests for the MachineNativeOps Quantum-Enhanced Naming Governance system.

## Files

### quantum-deployment-manifest.yaml

Complete Kubernetes deployment manifest including:

- **Namespace**: `quantum-governance` with proper labels
- **ServiceAccount & RBAC**: Role-based access control configuration
- **ConfigMap**: Quantum configuration and naming policies
- **Secrets**: Secure storage for API tokens and cryptographic keys
- **Deployment**: 3-replica service with health probes and resource limits
- **Service**: LoadBalancer with HTTP, metrics, and Jaeger ports
- **HorizontalPodAutoscaler**: Auto-scaling based on CPU, memory, and quantum coherence
- **ServiceMonitor**: Prometheus integration for metrics collection
- **PrometheusRule**: Alert rules for quantum metrics
- **NetworkPolicy**: Security policies for ingress/egress traffic
- **PodDisruptionBudget**: High availability configuration
- **Certificate**: TLS certificate via cert-manager
- **Ingress**: NGINX ingress with TLS termination

## Quick Start

### Prerequisites

- Kubernetes 1.24+
- kubectl configured with cluster access
- cert-manager (for TLS certificates)
- Prometheus Operator (for monitoring)

### Deployment Steps

```bash
# Apply the deployment manifest
kubectl apply -f quantum-deployment-manifest.yaml

# Verify deployment
kubectl wait --for=condition=ready pod \
  -l app.kubernetes.io/name=quantum-governance \
  -n quantum-governance --timeout=300s

# Check service status
kubectl get pods -n quantum-governance
kubectl get svc -n quantum-governance
```

## Resource Requirements

| Resource | Request | Limit |
|----------|---------|-------|
| CPU | 2vQuantum | 4vQuantum |
| Memory | 4GiQuantum | 8GiQuantum |
| Storage | 10Gi | 20Gi |

## Service Endpoints

| Port | Service | Description |
|------|---------|-------------|
| 80 | HTTP | API endpoint |
| 9090 | Metrics | Prometheus metrics |
| 16686 | Jaeger | Distributed tracing |

## High Availability

- **Replicas**: 3 (minimum)
- **PDB**: minAvailable = 2
- **HPA**: Scales 3-10 pods based on load

## Related Documentation

- [Parent README](../README.md) - Main project documentation
- [Configuration](../config/README.md) - Governance configuration
- [Quick Install](../scripts/README.md) - Automated installation
