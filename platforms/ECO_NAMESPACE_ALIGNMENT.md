# ECO 命名空間規範對齊文件 (ECO Namespace Alignment Document)

**日期**: 2026-02-25  
**版本**: 1.0  
**狀態**: 執行中

---

## 1. 平台結構對齊 (Platform Structure Alignment)

### 1.1 平台層級架構

```
eco-base/
├── platforms/
│   ├── platform-eco/              # Platform-01: IndestructibleAutoOps (ECO)
│   │   ├── k8s/
│   │   ├── helm/
│   │   ├── config/
│   │   ├── docs/
│   │   └── README.md
│   │
│   ├── platform-superai/          # Platform-02 (SuperAI) / Platform-03 (MachineNativeOps)
│   │   ├── k8s/
│   │   ├── helm/
│   │   ├── infrastructure/
│   │   ├── ai/
│   │   ├── src/
│   │   └── README.md
│   │
│   └── platform-core/             # 共享內核 (Core Services)
│       ├── auth/
│       ├── memory-hub/
│       ├── event-bus/
│       ├── policy-audit/
│       └── infra-manager/
│
├── kubernetes/
│   ├── namespaces/
│   ├── rbac/
│   ├── network-policies/
│   └── resource-quotas/
│
├── terraform/
│   ├── gcp/
│   ├── modules/
│   └── variables.tf
│
└── docs/
    ├── ECO命名空間規範.md
    ├── ARCHITECTURE.md
    └── DEPLOYMENT_GUIDE.md
```

### 1.2 命名空間對應表

| 邏輯層 | Kubernetes 命名空間 | 平台資料夾 | 用途 |
|--------|-------------------|-----------|------|
| 基礎設施 | `k8s-namespace-infra-prod` | `platform-core/infra` | Argo Events, Tekton, Harbor, Argo CD, Prometheus, Grafana, Loki |
| Platform-01 | `k8s-namespace-platform-01-prod` | `platform-eco/` | IndestructibleAutoOps (觀測、自癒、修復編排) |
| Platform-02 | `k8s-namespace-platform-02-prod` | `platform-superai/` | IAOps (IaC、GitOps、供應鏈合規) |
| Platform-03 | `k8s-namespace-platform-03-prod` | `platform-superai/` | MachineNativeOps (節點基線、硬體納管、邊緣代理) |

---

## 2. 資源命名規範應用 (Resource Naming Convention Application)

### 2.1 Platform-ECO 資源命名

**前綴**: `eco-` 或 `platform-01-`

| 資源類型 | 命名模式 | 範例 |
|---------|--------|------|
| Kubernetes 部署 | `k8s-deployment-eco-<service>-<env>` | `k8s-deployment-eco-observability-prod` |
| Helm Release | `helm-release-eco-<component>-<version>` | `helm-release-eco-argo-cd-v2.8.0` |
| ConfigMap | `eco-config-<component>-<purpose>` | `eco-config-observability-prometheus` |
| Secret | `eco-secret-<service>-<type>` | `eco-secret-github-actions-token` |
| Service Account | `eco-sa-<component>-<env>` | `eco-sa-github-actions-prod` |

### 2.2 Platform-SuperAI 資源命名

**前綴**: `superai-` 或 `platform-02-` / `platform-03-`

| 資源類型 | 命名模式 | 範例 |
|---------|--------|------|
| AI 服務部署 | `k8s-deployment-superai-ai-<model>-<env>` | `k8s-deployment-superai-ai-llm-prod` |
| 量子模擬 | `k8s-job-superai-quantum-<circuit>-<env>` | `k8s-job-superai-quantum-vqe-staging` |
| IaC 配置 | `k8s-configmap-superai-iac-<provider>` | `k8s-configmap-superai-iac-terraform` |
| 機械硬體 | `k8s-daemonset-superai-hardware-<type>` | `k8s-daemonset-superai-hardware-edge-agent` |

---

## 3. 環境變數命名規範 (Environment Variable Specification)

### 3.1 Platform-ECO 環境變數

```bash
# 基礎設施
ECO_INFRA_CLUSTER_NAME=eco-base-gke
ECO_INFRA_REGION=asia-east1
ECO_INFRA_PROJECT_ID=my-project-ops-1991

# Argo Events
ECO_ARGO_EVENTS_NAMESPACE=infra
ECO_ARGO_EVENTS_WEBHOOK_PORT=12000

# Tekton
ECO_TEKTON_NAMESPACE=infra
ECO_TEKTON_REGISTRY=asia-east1-docker.pkg.dev/my-project-ops-1991/eco-base

# Argo CD
ECO_ARGOCD_NAMESPACE=infra
ECO_ARGOCD_SERVER_URL=https://argocd.example.com

# GitHub Actions
ECO_GITHUB_ACTIONS_SA=eco-sa-github-actions-prod
ECO_GITHUB_WORKLOAD_IDENTITY_PROVIDER=projects/my-project-ops-1991/locations/global/workloadIdentityPools/github-pool

# Monitoring
ECO_PROMETHEUS_NAMESPACE=infra
ECO_GRAFANA_NAMESPACE=infra
ECO_LOKI_NAMESPACE=infra
```

### 3.2 Platform-SuperAI 環境變數

```bash
# SuperAI 基礎設施
SUPERAI_NAMESPACE=platform-02
SUPERAI_REGION=asia-east1

# AI 服務
SUPERAI_AI_MODEL_REGISTRY=asia-east1-docker.pkg.dev/my-project-ops-1991/superai-models
SUPERAI_AI_SERVICE_URL=http://svc-ai.platform-02.svc.cluster.local:8001
SUPERAI_AI_API_KEY=${SUPERAI_AI_API_KEY_SECRET}

# 量子計算
SUPERAI_QUANTUM_SIMULATOR=qiskit
SUPERAI_QUANTUM_BACKEND=qasm_simulator
SUPERAI_QUANTUM_SHOTS=1024

# IaC (Terraform)
SUPERAI_TERRAFORM_BACKEND=gs://eco-base-terraform-state
SUPERAI_TERRAFORM_WORKSPACE=superai-prod

# 機械硬體
SUPERAI_HARDWARE_EDGE_AGENTS=5
SUPERAI_HARDWARE_MONITORING_INTERVAL=30s
```

---

## 4. URI 與 URN 規範應用 (URI & URN Application)

### 4.1 Platform-ECO 資源 URI/URN

**Kubernetes 部署**:
- URI: `eco-base://k8s/platform-01/deployment/observability-stack`
- URN: `urn:eco-base:k8s:platform-01:deployment:observability-stack:6ba7b811-9dad-11d1-80b4-00c04fd430c8`

**Argo CD 應用**:
- URI: `eco-base://service/platform-01/argocd/app-deployment`
- URN: `urn:eco-base:service:platform-01:argocd:app-deployment:sha256-abcdef123456`

**GitHub Actions 工作流程**:
- URI: `eco-base://gh/platform-01/workflow/ci-cd-pipeline`
- URN: `urn:eco-base:gh:platform-01:workflow:ci-cd-pipeline:github-action-123456`

### 4.2 Platform-SuperAI 資源 URI/URN

**AI 服務**:
- URI: `eco-base://service/platform-02/ai/llm-inference`
- URN: `urn:eco-base:service:platform-02:ai:llm-inference:6ba7b811-9dad-11d1-80b4-00c04fd430c8`

**量子模擬任務**:
- URI: `eco-base://job/platform-02/quantum/vqe-optimization`
- URN: `urn:eco-base:job:platform-02:quantum:vqe-optimization:sha256-quantum-123456`

**機械硬體代理**:
- URI: `eco-base://daemonset/platform-03/hardware/edge-agent`
- URN: `urn:eco-base:daemonset:platform-03:hardware:edge-agent:hardware-agent-node-001`

---

## 5. 標籤與註解規範應用 (Labels & Annotations Application)

### 5.1 Platform-ECO 標籤示例

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: k8s-deployment-eco-observability-prod
  namespace: infra
  labels:
    app.kubernetes.io/name: observability-stack
    app.kubernetes.io/instance: observability-prod
    app.kubernetes.io/version: v1.0.0
    app.kubernetes.io/component: monitoring
    app.kubernetes.io/part-of: eco-base
    eco-base/platform: platform-01
    eco-base/environment: production
    eco-base/owner: platform-team
  annotations:
    eco-base/uri: "eco-base://k8s/platform-01/deployment/observability-stack"
    eco-base/urn: "urn:eco-base:k8s:platform-01:deployment:observability-stack:6ba7b811-9dad-11d1-80b4-00c04fd430c8"
    eco-base/governance-policy: "qyaml-governance.rego"
    eco-base/audit-log-level: "full"
```

### 5.2 Platform-SuperAI 標籤示例

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: k8s-deployment-superai-ai-llm-prod
  namespace: platform-02
  labels:
    app.kubernetes.io/name: ai-service
    app.kubernetes.io/instance: ai-llm-prod
    app.kubernetes.io/version: v2.0.0
    app.kubernetes.io/component: backend
    app.kubernetes.io/part-of: eco-base
    eco-base/platform: platform-02
    eco-base/environment: production
    eco-base/owner: ai-team
    superai/model: llm
    superai/inference-type: batch
  annotations:
    eco-base/uri: "eco-base://service/platform-02/ai/llm-inference"
    eco-base/urn: "urn:eco-base:service:platform-02:ai:llm-inference:6ba7b811-9dad-11d1-80b4-00c04fd430c8"
    eco-base/governance-policy: "qyaml-governance.rego"
    eco-base/audit-log-level: "full"
    superai/quantum-optimization: "enabled"
```

---

## 6. 依賴關係映射 (Dependency Mapping)

### 6.1 Platform-ECO 依賴關係

```
Platform-01 (ECO)
├── 依賴: core-auth (Auth Service)
├── 依賴: core-memory-hub (Memory Hub)
├── 依賴: core-event-bus (Event Bus)
├── 依賴: core-policy-audit (Policy & Audit)
├── 依賴: core-infra-manager (Infra Manager)
├── 依賴: svc-prometheus (Prometheus)
├── 依賴: svc-grafana (Grafana)
├── 依賴: svc-loki (Loki)
├── 依賴: svc-argo-cd (Argo CD)
├── 依賴: svc-argo-events (Argo Events)
├── 依賴: svc-tekton (Tekton)
└── 依賴: svc-harbor (Harbor)
```

### 6.2 Platform-SuperAI 依賴關係

```
Platform-02 (SuperAI)
├── 依賴: core-auth (Auth Service)
├── 依賴: core-memory-hub (Memory Hub)
├── 依賴: core-event-bus (Event Bus)
├── 依賴: core-policy-audit (Policy & Audit)
├── 依賴: svc-ai-inference (AI Inference Service)
├── 依賴: svc-quantum-simulator (Quantum Simulator - Qiskit)
├── 依賴: svc-iac-manager (IaC Manager - Terraform)
├── 依賴: svc-supabase (Supabase - Database)
└── 依賴: svc-github-actions (GitHub Actions)

Platform-03 (MachineNativeOps)
├── 依賴: core-auth (Auth Service)
├── 依賴: core-infra-manager (Infra Manager)
├── 依賴: svc-hardware-agent (Hardware Agent)
├── 依賴: svc-node-monitoring (Node Monitoring)
└── 依賴: svc-edge-computing (Edge Computing)
```

---

## 7. 合規性檢查清單 (Compliance Checklist)

### 7.1 Platform-ECO 合規性

- [ ] 所有資源使用 `eco-` 或 `platform-01-` 前綴
- [ ] 所有 Kubernetes 資源包含強制標籤
- [ ] 所有 Kubernetes 資源包含強制註解（URI、URN、治理政策、審計日誌級別）
- [ ] 所有環境變數遵循 `ECO_*` 命名規範
- [ ] 所有敏感資訊通過 Secrets 管理系統管理
- [ ] 所有依賴關係明確聲明
- [ ] 所有資源通過 OPA 政策驗證

### 7.2 Platform-SuperAI 合規性

- [ ] 所有資源使用 `superai-`、`platform-02-` 或 `platform-03-` 前綴
- [ ] 所有 Kubernetes 資源包含強制標籤
- [ ] 所有 Kubernetes 資源包含強制註解（URI、URN、治理政策、審計日誌級別）
- [ ] 所有環境變數遵循 `SUPERAI_*` 或 `PLATFORM_02_*` 命名規範
- [ ] 所有敏感資訊通過 Secrets 管理系統管理
- [ ] 所有依賴關係明確聲明
- [ ] 所有資源通過 OPA 政策驗證
- [ ] 量子模擬資源包含 `superai/quantum-*` 標籤
- [ ] 機械硬體資源包含 `superai/hardware-*` 標籤

---

## 8. 後續行動 (Next Steps)

1. **驗證現有資源**: 掃描 `platform-eco` 和 `platform-superai` 中的所有資源，確保符合命名規範
2. **更新配置**: 根據本文件更新所有 Kubernetes 配置、Helm Charts 和 Terraform 代碼
3. **實施 OPA 政策**: 部署 OPA/Kyverno 政策以強制執行命名規範
4. **文檔更新**: 更新所有平台文檔以反映新的命名規範
5. **團隊培訓**: 對開發和運維團隊進行命名規範培訓

---

**版本歷史**:
- v1.0 (2026-02-25): 初始版本，定義 Platform-ECO 和 Platform-SuperAI 的命名規範對齊

