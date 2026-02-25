# ECO Platform Integration Master Document
# eco-base 平台整合主文件

**版本**: 1.0.0  
**日期**: 2026-02-26  
**規範依據**: ECO 命名空間規範 v1.0

---

## 1. 平台目錄結構

```
eco-base-platforms/
├── platform-core/          # 共享內核 (_shared kernel)
├── platform-govops/        # GovOps — 治理工作流程平台 (port: 8091/9091)
├── platform-dataops/       # DataOps — 資料與證據操作平台 (port: 8093/9093)
├── platform-observops/     # ObservOps — 可觀測性操作平台 (port: 8094/9094)
├── platform-seccompops/    # SecCompOps — 安全與合規操作平台 (port: 8095/9095)
├── platform-superai/       # SuperAI — AI 與量子計算平台 (port: 8096/9096)
├── platform-eco/           # Platform-ECO — AutoEcoOps 主平台
├── ECO_PLATFORM_INTEGRATION_MASTER.md  ← 本文件
├── ECO_NAMESPACE_ALIGNMENT.md
└── PLATFORM_STRUCTURE.md
```

---

## 2. 平台身份映射表 (Platform Identity Mapping)

| 平台目錄 | ECO 命名前綴 | glName | K8s 命名空間 | API Port | Metrics Port |
|---------|------------|--------|------------|---------|-------------|
| platform-core | `core-` | `core.shared-kernel` | `eco-core` | — | — |
| platform-govops | `platform-govops-` | `gl.gov.ops-platform` | `eco-govops` | 8091 | 9091 |
| platform-dataops | `platform-dataops-` | `gl.data-ops.evidence-platform` | `eco-dataops` | 8093 | 9093 |
| platform-observops | `platform-observops-` | `gl.observ-ops.platform` | `eco-observops` | 8094 | 9094 |
| platform-seccompops | `platform-seccompops-` | `gl.sec-ops.compliance-platform` | `eco-seccompops` | 8095 | 9095 |
| platform-superai | `platform-superai-` | `gl.super-ai.quantum-platform` | `eco-superai` | 8096 | 9096 |

---

## 3. ECO 命名空間差距分析 (Gap Analysis)

### 3.1 現有平台的不符合項

| 平台 | 差距類型 | 現有值 | ECO 規範要求值 |
|------|---------|--------|--------------|
| govops | K8s 命名空間名稱 | `govops` | `eco-govops` |
| govops | 標籤缺失 | 無 `eco-base/platform` | `eco-base/platform: platform-govops` |
| govops | 標籤缺失 | 無 `eco-base/environment` | `eco-base/environment: production` |
| govops | 標籤缺失 | 無 `eco-base/owner` | `eco-base/owner: governance-operations-team` |
| govops | 標籤缺失 | 無 `app.kubernetes.io/instance` | `app.kubernetes.io/instance: govops-engine-prod` |
| govops | 註解缺失 | 無 `eco-base/uri` | `eco-base://k8s/platform-govops/deployment/govops-engine` |
| govops | 註解缺失 | 無 `eco-base/urn` | `urn:eco-base:k8s:platform-govops:deployment:govops-engine:<uuid>` |
| govops | 註解缺失 | 無 `eco-base/governance-policy` | `eco-govops-governance.rego` |
| govops | 註解缺失 | 無 `eco-base/audit-log-level` | `full` |
| dataops | K8s 命名空間名稱 | `dataops` | `eco-dataops` |
| dataops | 標籤/註解缺失 | 同 govops | 同 govops 規範 |
| seccompops | K8s 命名空間名稱 | `seccompops` | `eco-seccompops` |
| seccompops | 標籤/註解缺失 | 同 govops | 同 govops 規範 |
| seccompops | 部署標籤缺失 | 無 `governance.io/managed` | `governance.io/managed: "true"` |
| observops | 缺少 K8s 配置 | 無 k8s/ 目錄 | 需新建完整 k8s 配置 |
| observops | 缺少 .platform/ | 無 manifest.yaml | 需新建 manifest.yaml |
| observops | 缺少 Helm chart | 無 helm/ 目錄 | 需新建 Helm chart |

### 3.2 整合路徑優先順序

**優先級 P0（基礎設施必要條件）：**
1. platform-core — 共享內核，所有平台依賴
2. platform-seccompops — 安全基線，必須最先部署

**優先級 P1（核心業務域）：**
3. platform-govops — 治理工作流程，驅動策略執行
4. platform-dataops — 資料管道，支撐證據鏈

**優先級 P2（可觀測性與補充）：**
5. platform-observops — 監控告警，部署後立即啟用
6. platform-superai — AI/量子計算，補充層

---

## 4. ECO 規範對齊後的 K8s 命名空間模板

```yaml
# 模板：ECO 規範對齊的 Namespace
apiVersion: v1
kind: Namespace
metadata:
  name: eco-<platform-name>
  labels:
    app.kubernetes.io/name: <platform-name>-platform
    app.kubernetes.io/part-of: eco-base
    app.kubernetes.io/managed-by: argocd
    eco-base/platform: platform-<platform-name>
    eco-base/environment: production
    eco-base/owner: <platform-name>-team
    governance.io/managed: "true"
  annotations:
    eco-base/uri: "eco-base://k8s/platform-<platform-name>/namespace/eco-<platform-name>"
    eco-base/urn: "urn:eco-base:k8s:platform-<platform-name>:namespace:eco-<platform-name>:<uuid>"
    eco-base/governance-policy: "eco-<platform-name>-governance.rego"
    eco-base/audit-log-level: "full"
    description: "<Platform DisplayName> — <description>"
```

---

## 5. 環境變數命名對齊表

| 平台 | 現有環境變數模式 | ECO 規範對齊後 |
|------|--------------|--------------|
| govops DB | `DATABASE_URL` | `PLATFORM_GOVOPS_DB_URL` |
| govops Redis | `REDIS_URL` | `PLATFORM_GOVOPS_REDIS_URL` |
| dataops DB | `DATABASE_URL` | `PLATFORM_DATAOPS_DB_URL` |
| seccompops DB | `DATABASE_URL` | `PLATFORM_SECCOMPOPS_DB_URL` |
| observops Prometheus | `PROMETHEUS_URL` | `PLATFORM_OBSERVOPS_PROMETHEUS_URL` |
| 全局 Supabase | `SUPABASE_URL` | `ECO_SUPABASE_URL` |
| 全局 Auth | `AUTH_SERVICE_URL` | `ECO_AUTH_SERVICE_URL` |

---

## 6. 整合路徑與部署排序

```
Phase 0 — 基礎設施準備
  └─ GKE 叢集 + VPC + Workload Identity
  └─ eco-core 命名空間 + RBAC
  └─ Cert-Manager + Ingress Controller

Phase 1 — 安全基線 (P0)
  └─ platform-seccompops → eco-seccompops
  └─ OPA/Kyverno 策略引擎
  └─ 不可變審計日誌儲存

Phase 2 — 治理與資料 (P1)
  └─ platform-govops → eco-govops
  └─ platform-dataops → eco-dataops
  └─ 事件匯流排 (Kafka/Redis Streams)

Phase 3 — 可觀測性 (P2)
  └─ platform-observops → eco-observops
  └─ Prometheus + Grafana + Loki + Tempo
  └─ 告警規則與 SLO 配置

Phase 4 — AI/量子補充層 (P3)
  └─ platform-superai → eco-superai
  └─ Qiskit 量子模擬環境
  └─ AI 推論引擎
```

---

## 7. GitHub Actions CI/CD 整合

每個平台的 `.github/workflows/ci.yaml` 需對齊以下 ECO 規範：

```yaml
# 強制環境變數命名
env:
  ECO_PLATFORM_ID: platform-<name>
  ECO_NAMESPACE: eco-<name>
  ECO_REGISTRY: asia-east1-docker.pkg.dev/eco-base/eco-registry

# 強制步驟
steps:
  - name: ECO Namespace Validation    # 驗證命名空間規範
  - name: Security Scan (Trivy)       # 漏洞掃描
  - name: Code Quality (SonarCloud)   # 代碼品質
  - name: SBOM Generation             # 供應鏈安全
  - name: Image Sign (cosign)         # 鏡像簽名
  - name: Deploy to eco-<name>        # 部署到 ECO 命名空間
  - name: Audit Log Write             # 寫入審計日誌
```

---

## 8. 跨平台依賴關係圖

```
platform-core (共享內核)
    ├── platform-seccompops (消費: 審計日誌、策略決策)
    ├── platform-govops (消費: 策略執行、事件匯流排)
    ├── platform-dataops (消費: 事件匯流排、向量檢索)
    ├── platform-observops (消費: 所有平台指標)
    └── platform-superai (消費: 事件匯流排、Memory Hub)

通信協議: EventBus (Kafka/Redis Streams) + HTTP API
認證: ECO Auth Service (OIDC/JWT)
審計: platform-seccompops (不可變儲存)
```

---

## 9. 合規框架映射

| 平台 | NIST 800-53 | ISO 27001 | SOC2 Type II | GDPR |
|------|------------|-----------|--------------|------|
| platform-seccompops | AC, AU, SI | A.12, A.14 | CC6, CC7 | Art.32 |
| platform-govops | CA, CM, PL | A.6, A.18 | CC1, CC2 | Art.5 |
| platform-dataops | AU, SI, MP | A.8, A.12 | CC4, CC5 | Art.17 |
| platform-observops | AU, IR, SI | A.12, A.16 | CC7, CC8 | Art.33 |
| platform-superai | SA, SC, SI | A.14, A.15 | CC3, CC9 | Art.22 |
