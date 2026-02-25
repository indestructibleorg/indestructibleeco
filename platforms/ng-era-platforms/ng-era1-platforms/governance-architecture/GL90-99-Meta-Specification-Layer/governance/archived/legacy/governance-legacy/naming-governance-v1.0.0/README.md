# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: documentation
# @ECO-audit-trail: ../../engine/governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated
# 命名治理系統 v1.0.0

[![License: MIT]([EXTERNAL_URL_REMOVED])]([EXTERNAL_URL_REMOVED])
[![Python 3.11+]([EXTERNAL_URL_REMOVED])]([EXTERNAL_URL_REMOVED])
[![Kubernetes 1.24+]([EXTERNAL_URL_REMOVED])]([EXTERNAL_URL_REMOVED])
[![CI/CD]([EXTERNAL_URL_REMOVED])]([EXTERNAL_URL_REMOVED])

## 概述

命名治理系統是一個組織層級的命名規範管理與自動化合規檢查平台，提供從規範制定、工具生成、自動驗證到監控稽核的全生命週期解決方案。

### 核心特性

- 📋 **單一數據源**: `machine-spec.yaml` 作為所有命名規範的唯一來源
- 🔄 **自動化生成**: 標準化的資源命名生成工具
- ✅ **合規驗證**: 自動化命名規範稽核工具
- 📊 **監控觀察**: Prometheus + Grafana 完整監控方案
- 🚀 **CI/CD 集成**: GitHub Actions / GitLab CI 無縫集成
- 📝 **變更管理**: RFC 變更請求與審批流程
- ⚠️ **例外管理**: 合規例外申請與生命週期管理
- 🎓 **角色培訓**: 完整的角色培訓課程與認證體系

## 快速開始

### 1. 安裝依賴

```bash
# Python 依賴
pip install pyyaml jsonschema requests kubernetes

# 設置腳本權限
chmod +x scripts/generation/*.py
chmod +x scripts/validation/*.py
chmod +x scripts/audit/*.py
```

### 2. 生成符合規範的資源名稱

```bash
python scripts/generation/naming_generator.py \
  --environment prod \
  --app payment \
  --resource-type deploy \
  --version v1.2.3 \
  --tenant finance
```

輸出:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prod-payment-deploy-v1.2.3
  labels:
    app.kubernetes.io/name: payment
    environment: prod
    tenant: finance
    version: v1.2.3
spec:
  replicas: 3
  # ...
```

### 3. 驗證資源命名

```bash
python scripts/validation/naming_validator.py \
  --spec config/machine-spec.yaml \
  --directory k8s \
  --format text
```

### 4. 部署監控規則

```bash
kubectl apply -f monitoring/prometheus/naming-governance-rules.yaml
```

## 項目結構

```
naming-governance-v1.0.0/
├── config/
│   └── machine-spec.yaml              # 單一數據源：命名規範配置
├── scripts/
│   ├── generation/
│   │   └── naming_generator.py        # 命名生成器
│   ├── validation/
│   │   └── naming_validator.py        # 命名驗證器
│   └── audit/
│       ├── change_manager.py          # 變更管理器
│       └── exception_manager.py       # 例外管理器
├── templates/
│   ├── k8s/                           # Kubernetes 資源模板
│   ├── gitlab/                        # GitLab CI 模板
│   └── github/                        # GitHub Actions 模板
├── monitoring/
│   ├── prometheus/
│   │   └── naming-governance-rules.yaml  # Prometheus 監控規則
│   └── grafana/
│       └── naming-governance-dashboard.json  # Grafana Dashboard
├── ci-cd/
│   └── workflows/
│       └── naming-governance-ci.yml   # GitHub Actions 工作流
├── training/
│   └── modules/
│       └── roles-curriculum.yaml     # 角色培訓課程
├── docs/
│   ├── guides/
│   │   └── implementation-guide.md    # 實施指南
│   ├── api/
│   ├── best-practices/
│   │   └── naming-patterns.md        # 命名模式最佳實踐
│   └── examples/
└── examples/
    ├── yaml/
    ├── bash/
    └── policy/
```

## 核心工具

### 命名生成器 (naming_generator.py)

生成符合規範的 Kubernetes 資源配置。

```bash
# 基本用法
python scripts/generation/naming_generator.py \
  --environment prod \
  --app payment \
  --resource-type deploy \
  --version v1.2.3 \
  --tenant finance

# 批量生成
python scripts/generation/naming_generator.py \
  --batch resources.yaml \
  --output generated/
```

### 命名驗證器 (naming_validator.py)

自動化驗證資源命名合規性。

```bash
# 驗證單一文件
python scripts/validation/naming_validator.py \
  --file k8s/deployment.yaml \
  --format text

# 驗證整個目錄
python scripts/validation/naming_validator.py \
  --directory k8s \
  --output audit-report.json \
  --format json
```

### 變更管理器 (change_manager.py)

管理 RFC 變更請求的生命週期。

```bash
# 創建變更請求
python scripts/audit/change_manager.py create \
  --title "升級支付服務至 v1.3.0" \
  --type normal \
  --requester "team-lead" \
  --risk medium \
  --output rfc-chg-001.yaml

# 批准變更
python scripts/audit/change_manager.py approve \
  --rfc rfc-chg-001.yaml \
  --approver "platform-lead"
```

### 例外管理器 (exception_manager.py)

管理合規例外的申請與審核。

```bash
# 創建例外申請
python scripts/audit/exception_manager.py create \
  --applicant "team-alpha" \
  --type "命名規範豁免" \
  --justification "第三方系統整合" \
  --risk low \
  --expiry 2025-12-31

# 批准例外
python scripts/audit/exception_manager.py approve \
  --id EXC-20250118000000 \
  --reviewer "compliance-officer"
```

## CI/CD 集成

### GitHub Actions

完整的 CI/CD 管道已配置，包括：

- ✅ 命名規範驗證
- ✅ 合規性檢查
- ✅ 標籤驗證
- ✅ 安全掃描
- ✅ 定期稽核
- ✅ 自動報告生成

```yaml
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  schedule:
    - cron: '0 2 * * *'
```

### GitLab CI

參考 `ci-cd/templates/gitlab/` 目錄中的模板。

## 監控與觀察性

### Prometheus 指標

- `naming:compliance:rate` - 命名合規率
- `naming:violations:total` - 違規總數
- `naming:compliance:by_environment` - 各環境合規率
- `naming:missing_labels:count` - 缺少標籤數量

### Grafana Dashboard

導入 `monitoring/grafana/naming-governance-dashboard.json` 以查看完整的治理儀表板。

### 警報規則

- `NamingConventionViolation` - 命名規範違反
- `ProductionNamingViolation` - 生產環境違反（嚴重）
- `NamingComplianceRateLow` - 合規率低於 95%
- `MissingRequiredLabels` - 缺少必要標籤

## 命名規範

### 標準格式

```
{environment}-{app}-{resource_type}-{version}[-{suffix}]
```

### 示例

```yaml
# 部署
prod-payment-deploy-v1.2.3
staging-order-deploy-v1.0.0-canary

# 服務
prod-payment-svc-v1.2.3
dev-inventory-svc-v0.9.0-beta

# ConfigMap
prod-payment-cm-v1.2.3
```

### 必要標籤

```yaml
metadata:
  labels:
    app.kubernetes.io/name: payment
    app.kubernetes.io/managed-by: platform-team
    environment: prod
    tenant: finance
    version: v1.2.3
```

詳細規範請參考 `config/machine-spec.yaml`。

## 角色培訓

系統提供完整的角色培訓課程：

- 🎓 **命名守門人** - 進階命名規則、審核實作、RFC 撰寫
- 💻 **技術負責人** - 自動化工具、YAML/腳本實作、CI 集成
- 🔧 **維運工程師** - 版本管理、回滾演練、指標監測
- 💼 **業務窗口** - 命名原則、政策宣導、跨部門溝通
- 👥 **一般用戶** - 基礎規則、自助檢查、錯誤案例

詳細課程請參考 `training/modules/roles-curriculum.yaml`。

## 文檔

- 📖 [實施指南](docs/guides/implementation-guide.md) - 完整的實施指南
- 🎨 [命名模式最佳實踐](docs/best-practices/naming-patterns.md) - 命名模式與最佳實踐
- 📚 [API 參考](docs/api/) - 工具 API 詳細文檔
- 💡 [示例](examples/) - 各種使用示例

## 貢獻

歡迎貢獻！請閱讀 [CONTRIBUTING.md](CONTRIBUTING.md) 了解詳情。

### 開發流程

1. Fork 項目
2. 創建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 創建 Pull Request

### 代碼規範

- 遵循 PEP 8 Python 代碼規範
- 添加必要的單元測試
- 更新相關文檔
- 確保所有 CI 檢查通過

## 許可證

本項目採用 MIT 許可證 - 詳見 [LICENSE](LICENSE) 文件。

## 支援

如有問題或建議：

- 📧 Email: platform-governance@example.com
- 💬 Slack: #platform-governance
- 🐛 Issue Tracker: [GitHub Issues]([EXTERNAL_URL_REMOVED])
- 📖 文檔: [docs/](docs/)

## 更新日誌

### v1.0.0 (2025-01-18)

#### 新增功能
- ✨ 初始版本發布
- 📋 完整的命名規範配置系統
- 🔄 自動化命名生成工具
- ✅ 命名驗證與稽核工具
- 📊 Prometheus + Grafana 監控集成
- 🚀 GitHub Actions CI/CD 管道
- 📝 RFC 變更管理系統
- ⚠️ 合規例外管理系統
- 🎓 完整的角色培訓課程
- 📖 詳細的實施指南與文檔

#### 技術特性
- 🐍 Python 3.11+ 支持
- ☸️ Kubernetes 1.24+ 兼容
- 📦 單一數據源架構
- 🔧 完全自動化工作流
- 📈 可觀察性優先設計

## 路線圖

### v1.1.0 (計劃中)
- [ ] Web UI 管理介面
- [ ] 多雲平台支持（AWS/GCP/Azure）
- [ ] 進階規則引擎
- [ ] 自動修復功能

### v1.2.0 (計劃中)
- [ ] AI 智能命名建議
- [ ] 成本分析與優化
- [ ] 合規報告自動生成
- [ ] 與外部系統集成

### v2.0.0 (遠期規劃)
- [ ] 分布式架構支持
- [ ] 企業級多租戶
- [ ] 高可用部署
- [ ] 完整的審計追蹤

## 致謝

感謝所有貢獻者和支持者！

特別感謝：
- Platform Governance Committee 的指導
- 各開發團隊的反饋與建議
- 開源社區的支持

---

**項目版本**: v1.0.0  
**最後更新**: 2025-01-18  
**維護者**: Platform Governance Committee

[⬆ 回到頂部](#命名治理系統-v100)