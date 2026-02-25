# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: documentation
# @ECO-audit-trail: ../../engine/governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated
# 命名治理實施指南 v1.0.0

## 文檔概述

**版本**: v1.0.0  
**最後更新**: 2025-01-18  
**維護者**: Platform Governance Committee

本文檔提供命名治理系統的完整實施指南，涵蓋從初始規劃到持續優化的全生命週期管理。

---

## 目錄

1. [快速開始](#快速開始)
2. [系統架構](#系統架構)
3. [安裝與配置](#安裝與配置)
4. [核心工具使用](#核心工具使用)
5. [CI/CD 集成](#cicd-集成)
6. [監控與觀察性](#監控與觀察性)
7. [變更管理](#變更管理)
8. [合規例外處理](#合規例外處理)
9. [故障排查](#故障排查)
10. [最佳實踐](#最佳實踐)

---

## 快速開始

### 前置要求

- Python 3.11+
- Kubernetes 1.24+
- Git/GitHub
- Prometheus + Grafana（可選）
- Docker（可選）

### 5 分鐘快速入門

```bash
# 1. 克隆倉庫
git clone <repository-url>
cd naming-governance-v1.0.0

# 2. 安裝依賴
pip install pyyaml jsonschema

# 3. 生成符合規範的資源名稱
python scripts/generation/naming_generator.py \
  --environment prod \
  --app payment \
  --resource-type deploy \
  --version v1.2.3 \
  --tenant finance

# 4. 驗證資源命名
python scripts/validation/naming_validator.py \
  --spec config/machine-spec.yaml \
  --directory k8s \
  --format text
```

---

## 系統架構

### 組件概覽

```
┌─────────────────────────────────────────────────────────────┐
│                    命名治理系統架構                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   命名生成器  │  │   命名驗證器  │  │  變更管理器   │     │
│  │  Generator   │  │   Validator  │  │ Change Mgr   │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                 │              │
│         └─────────────────┼─────────────────┘              │
│                           │                                │
│                    ┌──────▼──────┐                         │
│                    │ Machine Spec │                         │
│                    │  (單一數據源) │                         │
│                    └──────┬──────┘                         │
│                           │                                │
│  ┌────────────────────────┼────────────────────────┐      │
│  │                        │                        │      │
│  ▼                        ▼                        ▼      │
│ ┌─────────┐         ┌─────────┐           ┌─────────────┐ │
│ │ CI/CD   │         │監控系統  │           │  例外管理   │ │
│ │Pipeline │         │Prometheus│           │   Manager   │ │
│ │         │         │ Grafana  │           │             │ │
│ └────┬────┘         └────┬────┘           └──────┬──────┘ │
│      │                   │                      │         │
│      └───────────────────┼──────────────────────┘         │
│                          │                                │
│                     ┌────▼────┐                           │
│                     │ Kubernetes                          │
│                     │ Cluster                             │
│                     └─────────┘                           │
└─────────────────────────────────────────────────────────────┘
```

### 核心設計原則

1. **單一數據源**: `machine-spec.yaml` 作為所有命名規範的唯一來源
2. **聲明式配置**: 所有規則通過 YAML 定義，易於版本控制
3. **自動化優先**: 所有檢查自動化，減少人工干預
4. **可觀察性**: 完整的監控與日誌追蹤
5. **合規即代碼**: 規範即代碼，支持 GitOps 流程

---

## 安裝與配置

### 1. 環境準備

#### 安裝 Python 依賴

```bash
cd naming-governance-v1.0.0
pip install -r requirements.txt
```

#### 創建 `requirements.txt`

```txt
pyyaml>=6.0
jsonschema>=4.17.0
requests>=2.28.0
kubernetes>=27.0.0
prometheus-client>=0.16.0
```

### 2. 配置命名規範

編輯 `config/machine-spec.yaml` 以自定義命名規範：

```yaml
naming:
  strategy: "hierarchical"
  allowed_chars: "[a-z0-9-]"
  max_length: 63
  segments:
    - name: "environment"
      required: true
      pattern: "^(dev|staging|prod)$"
```

### 3. 設置腳本權限

```bash
chmod +x scripts/generation/naming_generator.py
chmod +x scripts/validation/naming_validator.py
chmod +x scripts/audit/change_manager.py
chmod +x scripts/audit/exception_manager.py
```

---

## 核心工具使用

### 命名生成器 (naming_generator.py)

#### 基本用法

```bash
python scripts/generation/naming_generator.py \
  --environment prod \
  --app payment-service \
  --resource-type deploy \
  --version v1.2.3 \
  --tenant finance \
  --suffix canary
```

#### 批量生成

創建 `resources.yaml`:

```yaml
resources:
  - environment: prod
    app.kubernetes.io/name: payment
    resource_type: deploy
    version: v1.2.3
    tenant: finance
    replicas: 3
    image: payment:v1.2.3
  
  - environment: staging
    app.kubernetes.io/name: payment
    resource_type: svc
    version: v1.2.3
    tenant: finance
```

批量生成:

```bash
python scripts/generation/naming_generator.py \
  --batch resources.yaml \
  --output generated/
```

### 命名驗證器 (naming_validator.py)

#### 驗證單一文件

```bash
python scripts/validation/naming_validator.py \
  --spec config/machine-spec.yaml \
  --file k8s/deployment.yaml \
  --format text \
  --strict
```

#### 驗證整個目錄

```bash
python scripts/validation/naming_validator.py \
  --spec config/machine-spec.yaml \
  --directory k8s \
  --pattern "*.yaml" \
  --output audit-report.json \
  --format json
```

#### CI/CD 集成

```yaml
- name: Validate Naming
  run: |
    python scripts/validation/naming_validator.py \
      --spec config/machine-spec.yaml \
      --directory k8s \
      --strict
```

---

## CI/CD 集成

### GitHub Actions 集成

完整的 GitHub Actions 工作流已提供在 `ci-cd/workflows/naming-governance-ci.yml`。

#### 主要功能

1. **命名驗證**: 自動檢查 PR 中的所有資源命名
2. **合規性檢查**: 驗證標籤和元數據
3. **安全掃描**: 使用 Trivy 掃描配置文件
4. **定期稽核**: 每日自動執行全集群稽核
5. **報告生成**: 自動生成稽核報告

#### 觸發條件

```yaml
on:
  push:
    branches: [main, develop]
    paths: ['k8s/**', 'helm/**']
  pull_request:
    branches: [main, develop]
  schedule:
    - cron: '0 2 * * *'  # 每日 UTC 02:00
```

### GitLab CI 集成

創建 `.gitlab-ci.yml`:

```yaml
stages:
  - validate
  - audit

naming_validation:
  stage: validate
  script:
    - pip install pyyaml
    - python naming-governance-v1.0.0/scripts/validation/naming_validator.py \
        --spec naming-governance-v1.0.0/config/machine-spec.yaml \
        --directory k8s \
        --strict
  only:
    - merge_requests
    - main

naming_audit:
  stage: audit
  script:
    - python naming-governance-v1.0.0/scripts/validation/naming_validator.py \
        --directory k8s \
        --output audit-report.json
  artifacts:
    paths:
      - audit-report.json
    expire_in: 30 days
  only:
    - schedules
```

---

## 監控與觀察性

### Prometheus 規則

部署監控規則:

```bash
kubectl apply -f monitoring/prometheus/naming-governance-rules.yaml
```

#### 主要指標

1. **命名合規率**: `naming:compliance:rate`
2. **違規總數**: `naming:violations:total`
3. **各環境合規率**: `naming:compliance:by_environment`
4. **缺少標籤數量**: `naming:missing_labels:count`

### Grafana Dashboard

導入 Dashboard:

```bash
kubectl apply -f monitoring/grafana/naming-governance-dashboard.json
```

或在 Grafana UI 中導入 JSON 文件。

#### Dashboard 包含

- 合規率總覽
- 違規趨勢圖
- 各環境指標
- 部署成功率
- 回滾次數統計
- 關鍵指標表格

### 警報配置

重要警報:

1. **NamingConventionViolation**: 偵測到命名違反
2. **ProductionNamingViolation**: 生產環境違反（嚴重）
3. **NamingComplianceRateLow**: 合規率低於 95%
4. **MissingRequiredLabels**: 缺少必要標籤

---

## 變更管理

### RFC 變更請求流程

#### 創建變更請求

```bash
python scripts/audit/change_manager.py create \
  --title "升級支付服務至 v1.3.0" \
  --type normal \
  --requester "team-lead" \
  --risk medium \
  --output rfc-chg-001.yaml
```

#### 編輯 RFC 文件

編輯生成的 `rfc-chg-001.yaml`，填寫詳細資訊:

```yaml
change_request:
  id: CHG-2025-001
  title: "升級支付服務至 v1.3.0"
  impact_assessment:
    services_affected:
      - "frontend"
      - "api"
    downtime_expected: "15 min"
  implementation_plan:
    steps:
      - "備份資料"
      - "部署新版本"
      - "執行測試"
  rollback_plan:
    steps:
      - "回復備份"
      - "通知團隊"
```

#### 驗證 RFC

```bash
python scripts/audit/change_manager.py validate \
  --rfc rfc-chg-001.yaml
```

#### 批准變更

```bash
python scripts/audit/change_manager.py approve \
  --rfc rfc-chg-001.yaml \
  --approver "platform-lead" \
  --notes "已審核，符合標準"
```

### 變更類型

| 類型 | 風險 | 審批方式 | 典型場景 |
|------|------|----------|----------|
| Standard | Low | 預審/自動化 | 例行維護 |
| Normal | Medium | CAB | 功能更新 |
| Emergency | High | 事後審核 | 緊急修復 |

---

## 合規例外處理

### 創建例外申請

```bash
python scripts/audit/exception_manager.py create \
  --applicant "team-alpha" \
  --type "命名規範豁免" \
  --justification "第三方系統整合需求" \
  --risk low \
  --expiry 2025-12-31 \
  --resources api-external-v1 \
  --mitigation "防火牆隔離" "定期稽核"
```

### 審核例外

#### 批准例外

```bash
python scripts/audit/exception_manager.py approve \
  --id EXC-20250118000000 \
  --reviewer "compliance-officer" \
  --notes "風險可控，批准為期 6 個月"
```

#### 拒絕例外

```bash
python scripts/audit/exception_manager.py reject \
  --id EXC-20250118000000 \
  --reviewer "compliance-officer" \
  --reason "風險過高，無法接受"
```

### 例外生命週期管理

```bash
# 檢查到期例外
python scripts/audit/exception_manager.py check-expired

# 撤銷例外
python scripts/audit/exception_manager.py revoke \
  --id EXC-20250118000000 \
  --reason "不再需要"

# 生成報告
python scripts/audit/exception_manager.py report \
  --status Approved \
  --output exception-report.yaml
```

### 定期複查

設置 Cron Job 自動檢查到期例外:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: exception-checker
spec:
  schedule: "0 9 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: checker
            image: python:3.11
            command:
            - python
            - /scripts/audit/exception_manager.py
            - check-expired
```

---

## 故障排查

### 常見問題

#### 1. 命名驗證失敗

**問題**: 資源名稱不符合規範

**解決方案**:
```bash
# 查看詳細錯誤
python scripts/validation/naming_validator.py \
  --file deployment.yaml \
  --format text

# 重新生成符合規範的名稱
python scripts/generation/naming_generator.py \
  --environment prod \
  --app payment \
  --resource-type deploy \
  --version v1.2.3 \
  --tenant finance
```

#### 2. Prometheus 指標無法查詢

**問題**: Grafana Dashboard 無數據

**解決方案**:
```bash
# 檢查 PrometheusRule 狀態
kubectl get prometheusrules -n monitoring

# 查看 Prometheus 日誌
kubectl logs -n monitoring prometheus-k8s-0

# 驗證規則語法
promtool check rules monitoring/prometheus/naming-governance-rules.yaml
```

#### 3. CI/CD 管道失敗

**問題**: GitHub Actions 驗證失敗

**解決方案**:
```bash
# 本地驗證
python scripts/validation/naming_validator.py \
  --directory k8s \
  --strict

# 查看詳細日誌
gh run view <run-id> --log

# 修復後重新提交
git add .
git commit -m "fix: 修正命名規範違規"
git push
```

### 日誌與調試

#### 啟用調試模式

```bash
export LOG_LEVEL=DEBUG
python scripts/validation/naming_validator.py --directory k8s
```

#### 查看稽核日誌

```bash
kubectl logs -n monitoring naming-validator-xxx
```

---

## 最佳實踐

### 命名規範

1. **使用小寫字母和連字符**: `prod-payment-deploy-v1.2.3`
2. **保持簡潔**: 避免過長的名稱（最大 63 字元）
3. **版本號遵循 SemVer**: `v1.2.3` 或 `v1.2.3-canary`
4. **環境前綴**: 明確標識環境（dev/staging/prod）

### CI/CD 集成

1. **所有檢查自動化**: 減少人工干預
2. **失敗快速反饋**: CI 失敗立即通知
3. **定期稽核**: 設置定時任務
4. **報告存檔**: 保留稽核歷史記錄

### 監控與觀察性

1. **設置合理閾值**: 合規率目標 95%
2. **分級警報**: 根據嚴重程度設置不同響應
3. **定期檢視 Dashboard**: 每週檢查趨勢
4. **主動監控**: 不要等到警報才行動

### 變更管理

1. **所有變更通過 RFC**: 確保可追溯性
2. **風險評估**: 必須評估影響和風險
3. **回滾計畫**: 每個變更必須有回滾方案
4. **審批流程**: 遵循組織的審批流程

### 例外管理

1. **例外應為例外**: 不應成為常態
2. **明確到期日期**: 所有例外必須有期限
3. **定期複查**: 到期前評估是否續期
4. **記錄理由**: 清楚記錄例外原因

---

## 附錄

### A. 完整示例

見 `examples/` 目錄中的完整示例文件。

### B. API 參考

詳細 API 文檔見 `docs/api/` 目錄。

### C. 更新日誌

見 `CHANGELOG.md`。

### D. 貢獻指南

見 `CONTRIBUTING.md`。

---

## 支援

如有問題或建議，請：

1. 查閱本文檔
2. 查看 FAQ
3. 提交 Issue
4. 聯繫 Platform Governance Committee

---

**文檔版本**: v1.0.0  
**最後更新**: 2025-01-18