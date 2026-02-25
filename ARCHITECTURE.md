# ECO Base — Architecture & Deployment Status

> **Last Updated**: 2026-02-26 | **Cluster**: eco-production | **Region**: asia-east1

---

## System Overview

ECO Base (IndestructibleAutoOps) is an enterprise-grade Kubernetes-native platform ecosystem built on GKE, implementing a full DevSecOps lifecycle with GitOps automation, supply chain security, and multi-layer observability.

---

## Infrastructure

| Component | Value |
|-----------|-------|
| **Cloud Provider** | GCP (my-project-ops-1991) |
| **Cluster** | eco-production (GKE v1.34.3-gke.1245000) |
| **Region** | asia-east1 |
| **Node Pool** | default-pool: n2-standard-4, 6 nodes (auto-scale 3–10) |
| **Network** | eco-vpc / eco-production-subnet |
| **NAT** | eco-nat-router + eco-nat (Private Nodes egress) |
| **Registry** | Harbor 2.14.2 (harbor namespace) |
| **Container Registry** | ghcr.io/indestructibleorg |

---

## Platform Namespaces

| Namespace | Purpose | Status |
|-----------|---------|--------|
| `infra` | Shared infrastructure services | Active |
| `platform-01` | IndestructibleAutoOps (govops, seccompops) | Active |
| `platform-02` | IAOps (dataops, superai) | Active |
| `platform-03` | MachineNativeOps (observops) | Active |
| `eco-production` | Production workloads | Active |

---

## 7-Layer Toolstack (All Deployed)

### Layer 1 — Event Streaming
| Tool | Version | Namespace | Status |
|------|---------|-----------|--------|
| Argo Events | v1.9.6 | argo-events | Running (4 pods) |
| NATS EventBus | — | argo-events | Running (3 replicas) |

### Layer 2 — CI/CD Pipeline
| Tool | Version | Namespace | Status |
|------|---------|-----------|--------|
| Tekton Pipelines | latest | tekton-pipelines | Running (3 pods) |
| Tekton Dashboard | latest | tekton-pipelines | Running |
| Tekton Resolvers | latest | tekton-pipelines-resolvers | Running |

### Layer 3 — Container Registry & GitOps
| Tool | Version | Namespace | Status |
|------|---------|-----------|--------|
| Harbor | 2.14.2 | harbor | Running (9 pods) |
| Argo CD | v3.3.2 | argocd | Running (7 pods) |

### Layer 4 — Policy & Admission Control
| Tool | Version | Namespace | Status |
|------|---------|-----------|--------|
| Kyverno | v1.17.1 | kyverno | Running (4 pods, 20 CRDs) |
| OPA Gatekeeper | v3.21.1 | gatekeeper-system | Running (2 pods, 17 CRDs) |

### Layer 5 — Observability
| Tool | Version | Namespace | Status |
|------|---------|-----------|--------|
| Prometheus | v0.89.0 | monitoring | Running (2/2) |
| Grafana | — | monitoring | Running (3/3) |
| AlertManager | — | monitoring | Running (2/2) |
| Loki | 3.6.5 | monitoring | Running (SingleBinary) |
| Promtail | 3.5.1 | monitoring | Running (DaemonSet, 6 nodes) |

### Layer 6 — Autoscaling
| Tool | Version | Namespace | Status |
|------|---------|-----------|--------|
| KEDA | 2.19.0 | keda | Running (3 pods, 6 CRDs) |

### Layer 7 — Progressive Delivery
| Tool | Version | Namespace | Status |
|------|---------|-----------|--------|
| Flagger | 1.42.0 | flagger-system | Running (1 pod, 3 CRDs) |

---

## ECO Platform Modules

| Module | Path | Namespace | Description |
|--------|------|-----------|-------------|
| eco-core | platforms/eco-core | infra | Shared kernel (auth, memory-hub, event-bus) |
| eco-govops | platforms/eco-govops | platform-01 | Governance & compliance operations |
| eco-seccompops | platforms/eco-seccompops | platform-01 | Security & compliance operations |
| eco-dataops | platforms/eco-dataops | platform-02 | Data pipeline operations |
| eco-superai | platforms/eco-superai | platform-02 | AI/ML operations |
| eco-observops | platforms/eco-observops | platform-03 | Observability operations |

---

## GitOps Configuration

**Argo CD Applications**:
- `eco-base-platforms` — Synced / Healthy (auto-sync: prune + selfHeal)
- ApplicationSet `eco-platforms` — 6 ECO platform apps
- ApplicationSet `eco-infra-tools` — 4 infrastructure tool apps

**Sync Strategy**: Automated with prune propagation, retry limit 5, exponential backoff (5s → 3m)

---

## Supply Chain Security (Kyverno Policies)

| Policy | Mode | Scope | Rule |
|--------|------|-------|------|
| `disallow-latest-tag` | Enforce | platform-01/02/03, infra, eco-production | No `:latest` image tag |
| `require-resource-limits` | Enforce | platform-01/02/03, infra | CPU + memory limits required |
| `disallow-privileged-containers` | Enforce | platform-01/02/03, infra, eco-production | No privileged containers |
| `require-non-root-user` | Audit | platform-01/02/03, infra | `runAsNonRoot: true` |
| `require-eco-labels` | Audit | platform-01/02/03, infra | `app`, `version`, `eco.platform` labels |

---

## GitHub Secrets (63 total)

**GCP**: `GCP_PROJECT_ID`, `GCP_REGION`, `GCP_SA_EMAIL`, `GCP_SA_KEY`, `GKE_CLUSTER_NAME`, `GKE_REGION`  
**GitHub**: `GH_TOKEN`, `GH_PAT`, `GH_CI_TOKEN`, `GHCR_TOKEN`, `ECO_GITHUB_TOKEN`  
**Harbor**: `HARBOR_URL`, `HARBOR_ADMIN_PASSWORD`  
**Argo CD**: `ARGOCD_URL`, `ARGOCD_ADMIN_PASSWORD`  
**Monitoring**: `GRAFANA_ADMIN_PASSWORD`, `GRAFANA_URL`, `PROMETHEUS_URL`, `LOKI_URL`  
**ECO**: `ECO_REGISTRY`, `ECO_NAMESPACE_PREFIX`, `ECO_DEPLOY_ENV`  
**Namespaces**: `KYVERNO_NAMESPACE`, `GATEKEEPER_NAMESPACE`, `KEDA_NAMESPACE`, `FLAGGER_NAMESPACE`

---

## Mobile Application

**Path**: `mobile/`  
**Framework**: Expo SDK 54 | React Native 0.81 | TypeScript | NativeWind 4  
**Brand**: ECO Base | Primary: `#00D4FF` | Background: `#0D1B2A`  
**Features**: Expo Router 6, Argo CD status monitoring, ECO platform dashboard

---

## Repository Structure

```
indestructibleorg/eco-base/
├── platforms/
│   ├── eco-core/
│   ├── eco-govops/
│   ├── eco-seccompops/
│   ├── eco-dataops/
│   ├── eco-superai/
│   └── eco-observops/
├── infrastructure/
│   └── terraform/          # GKE cluster, VPC, IAM
├── gitops/
│   ├── applicationset-eco-platforms.yaml
│   └── policies/
│       └── kyverno-supply-chain.yaml
├── k8s/
│   └── k8s-manifests.yaml
├── mobile/                 # ECO Base React Native app
├── docs/
│   ├── phase2-deployment.md
│   └── phase3-deployment.md
├── .github/
│   └── workflows/
│       └── eco-deploy.yml  # AutoEcoOps CI/CD Pipeline
└── ARCHITECTURE.md         # This file
```

---

## CI/CD Pipeline

**Workflow**: `.github/workflows/eco-deploy.yml`  
**Triggers**: push to main, PR, manual dispatch  
**Stages**: SAST → SBOM → cosign sign → OCI push → Terraform plan → ArgoCD sync  
**Active Workflows**: 17 total
