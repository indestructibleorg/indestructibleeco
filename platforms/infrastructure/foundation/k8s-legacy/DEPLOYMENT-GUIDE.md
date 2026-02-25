<!-- @ECO-governed -->
<!-- @ECO-layer: GL90-99 -->
<!-- @ECO-semantic: governed-documentation -->
<!-- @ECO-audit-trail: engine/governance/GL_SEMANTIC_ANCHOR.json -->

# Enterprise Infrastructure Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the enterprise infrastructure components (Istio, Jaeger, Velero, Multi-AZ) to a testing environment.

## Prerequisites

### Required Tools
- **kubectl** v1.24+ - Kubernetes CLI
- **helm** v3.x - Package manager for Kubernetes
- **istioctl** v1.20+ - Istio CLI
- **Velero CLI** v1.12.0+ - Backup and restore tool

### Cluster Requirements
- Kubernetes cluster with 3+ nodes
- 3+ availability zones (for multi-AZ testing)
- S3-compatible storage (for Velero backups)
- Minimum resources:
  - 4 vCPUs per node
  - 8GB RAM per node
  - 50GB disk space per node

### Network Requirements
- Cluster must have network policies enabled
- Nodes must be able to communicate across zones
- Internet access for pulling images
- Access to S3 endpoint for backups

## Deployment Steps

### Step 1: Deploy Istio to Testing Environment

**Objective:** Deploy Istio Service Mesh with traffic management, security, and observability.

```bash
# Make script executable
chmod +x scripts/deploy-istio-testing.sh

# Run deployment
./scripts/deploy-istio-testing.sh
```

**What This Does:**
1. Creates namespace `machine-native-ops-testing`
2. Enables Istio sidecar injection
3. Deploys Istio gateway and virtual services
4. Applies security policies (mTLS, RBAC)
5. Deploys sample application for testing
6. Verifies Istio configuration

**Verification:**
```bash
# Check namespace
kubectl get namespace machine-native-ops-testing

# Check pods (should see Istio sidecars)
kubectl get pods -n machine-native-ops-testing

# Check Istio resources
kubectl get all -n machine-native-ops-testing

# Verify sidecar injection
kubectl describe pod