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

---

## Phase 4 — 平台基線 Gate 套件（2026-02-26）

### 4-A: Argo CD 安全護欄

| 元件 | 配置 | 狀態 |
|------|------|------|
| AppProject `eco-platforms` | sourceRepos: indestructibleorg/eco-base, destinations: platform-01/02/03 | Applied |
| AppProject `eco-infra` | sourceRepos: indestructibleorg/eco-base, destinations: infra/monitoring/keda/flagger-system | Applied |
| Diff Gate CI | `.github/workflows/argocd-diff-gate.yml` (argocd-diff + drift-detection jobs) | Active |

### 4-B: 供應鏈 Gate

| 元件 | 配置 | 狀態 |
|------|------|------|
| Supply Chain CI | `.github/workflows/supply-chain-gate.yml` (cosign sign/verify + syft SBOM + SLSA) | Active |
| Kyverno Admission | `verify-image-signatures` ClusterPolicy (Audit → Enforce 2026-03-28) | Applied |

### 4-C: SLO / 回滾閉環

| 元件 | 配置 | 狀態 |
|------|------|------|
| Flagger Canary | `gitops/slo/flagger-canary-template.yaml` (p99 latency ≤200ms, error rate ≤1%, RPS ≥10) | Template |
| KEDA ScaledObject | `gitops/slo/keda-scaledobject-template.yaml` (Prometheus SLI, minReplicas=2, maxReplicas=20) | Template |

### P1 雷點修復

| 問題 | 修復 | 狀態 |
|------|------|------|
| EventBus required anti-affinity | `eventbus-name: default` label selector, cpu=30m, 3 pods on 3 different nodes | FIXED |
| Kyverno webhook namespace exclusion | 11 system namespaces excluded via Helm values | FIXED |
| Loki query limits | max_query_length=720h, parallelism=32, entries=50000, timeout=120s | FIXED |

### EventBus JetStream 最終節點分佈（3 pods × 3 nodes × 2 zones）

| Pod | Node | Zone |
|-----|------|------|
| eventbus-default-js-0 | f14d316a-6w8q | asia-east1-b |
| eventbus-default-js-1 | 9fe3d7b3-6lgk | asia-east1-a |
| eventbus-default-js-2 | 9fe3d7b3-zjc0 | asia-east1-a |

---
## Bolt 修復紀錄（2026-02-26）

### Bolt-1: EventBus 跨區分佈
| 項目 | 值 |
|------|-----|
| 修復方式 | topologySpreadConstraints (maxSkew=1, zone) |
| 最終分佈 | js-0: asia-east1-b, js-1: asia-east1-a, js-2: asia-east1-a |
| 說明 | asia-east1-c 資源不足，2+1 分佈符合 maxSkew:1 約束 |
| 狀態 | **PASS** |

### Bolt-2: Kyverno PolicyException 遷移
| 項目 | 值 |
|------|-----|
| 遷移方式 | webhook namespace 排除 → 9 個 PolicyException（含 expiry/owner/issue） |
| Webhook 排除 | 僅保留 `kyverno`（自我保護） |
| PolicyException 數量 | 9 個，全部含 `eco.policy/expires`、`eco.policy/owner`、`eco.policy/issue` |
| CI Gate | `policy-gate.yml` job `exception-expiry-check`：過期 exception 阻斷 merge |
| 報告 | `tests/reports/bolt2-policy-exception-report.json` |
| 狀態 | **PASS** |

| PolicyException | 命名空間 | 到期日 | Issue |
|-----------------|----------|--------|-------|
| argo-events-root-exception | argo-events | 2026-04-01 | #3 |
| tekton-pipelines-exception | tekton-pipelines | 2026-04-15 | #4 |
| harbor-exception | harbor | 2026-04-15 | #5 |
| argocd-exception | argocd | 2026-04-15 | #6 |
| gatekeeper-exception | gatekeeper-system | 2026-04-15 | #7 |
| keda-exception | keda | 2026-04-15 | #8 |
| flagger-exception | flagger-system | 2026-04-15 | #9 |
| monitoring-stack-exception | monitoring | 2026-05-01 | #10 |
| kube-system-resource-limits-exception | kube-system/kube-public/gke-managed-system | 2026-06-01 | #11 |

### Bolt-3: Flagger Rollback Drill
| 項目 | 值 |
|------|-----|
| 測試命名空間 | platform-01 |
| 注入失敗 | 高錯誤率映像（stefanprodan/podinfo:fake） |
| SLI 閾值 | error_rate ≤1%、p99 latency ≤200ms、failure_threshold=3 |
| Flagger 偵測 | Progressing → Failed（分析週期 10s × 3 次失敗） |
| 最終狀態 | phase=Failed, weight=0（回滾完成） |
| 回滾時間 | ~64 秒（01:39:36 → 01:40:44） |
| 報告 | `tests/reports/bolt3-flagger-rollback-report.json` |
| 狀態 | **PASS** |

---
## 最終系統狀態（2026-02-26）

### Helm Releases（9/9 deployed）
| Release | Namespace | Chart | App Version | Status |
|---------|-----------|-------|-------------|--------|
| argocd | argocd | argo-cd-9.4.4 | v3.3.2 | deployed |
| flagger | flagger-system | flagger-1.42.0 | 1.42.0 | deployed |
| gatekeeper | gatekeeper-system | gatekeeper-3.21.1 | v3.21.1 | deployed |
| harbor | harbor | harbor-1.18.2 | 2.14.2 | deployed |
| keda | keda | keda-2.19.0 | 2.19.0 | deployed |
| kyverno | kyverno | kyverno-3.7.1 | v1.17.1 | deployed |
| loki | monitoring | loki-6.53.0 | 3.6.5 | deployed |
| prometheus | monitoring | kube-prometheus-stack-82.4.0 | v0.89.0 | deployed |
| promtail | monitoring | promtail-6.17.1 | 3.5.1 | deployed |

### Pod 健康狀態
| 命名空間 | Running/Total |
|----------|--------------|
| argo-events | 4/4 |
| tekton-pipelines | 4/4 |
| harbor | 9/9 |
| argocd | 7/7 |
| kyverno | 5/5 |
| gatekeeper-system | 2/2 |
| monitoring | 32/32 |
| keda | 3/3 |
| flagger-system | 2/2 |

### Validation Gates（全部通過）
| Gate | 結果 |
|------|------|
| P0 驗證（23/23） | PASS |
| Bolt-1 EventBus 跨區 | PASS |
| Bolt-2 PolicyException 遷移 | PASS |
| Bolt-3 Flagger Rollback Drill | PASS |
