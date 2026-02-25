# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: documentation
# @ECO-audit-trail: ../../engine/governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated
# Governance

MachineNativeOps 治理中心，定義合規要求、內部政策與技術標準。

## 目錄結構

```
governance/
├── compliance/    # 法規合規（GDPR, HIPAA, SOC2）
├── policies/      # 內部政策與流程
└── standards/     # 技術標準與規範
```

## 三層治理架構

| 層級 | 目錄 | 說明 | 維護者 |
|------|------|------|--------|
| 合規 | compliance/ | 外部法規要求 | 法務/合規團隊 |
| 政策 | policies/ | 內部運作規範 | 各領域負責人 |
| 標準 | standards/ | 技術實踐標準 | 架構團隊 |

## Compliance（合規）

法規合規要求文檔：

- `GDPR.md` - 歐盟一般資料保護規則
- `HIPAA.md` - 美國健康保險可攜性和責任法案
- `SOC2.md` - 服務組織控制報告標準

## Policies（政策）

內部政策與流程規範：

| 政策 | 說明 |
|------|------|
| change-management | 變更管理流程 |
| exception | 例外處理政策 |
| gatekeeper | 准入控制政策 |
| migration | 遷移政策 |
| naming | 命名規範 |
| observability | 可觀測性政策 |
| security | 安全政策 |
| validation | 驗證規則 |

## Standards（標準）

技術標準定義：

- `api-standards.md` - API 設計標準
- `coding-standards.md` - 編碼標準

## 目前狀態

> 此目錄結構已建立，部分文件內容待補充。

## 相關資源

- [DIRECTORY.md](./DIRECTORY.md) - 詳細目錄說明
- [docs/governance/](../docs/governance/) - 治理框架文檔
- [config/governance/](../config/governance/) - 治理配置文件
