# ECO Workflow 清理與保留規範 (Workflow Cleanup Spec)

## 1. 保留清單 (Keep List)
以下 Workflow 為 ECO 核心治理與供應鏈安全之必備流程，必須保留並確保 100% 綠燈。

| Workflow 文件 | 功能說明 | 治理等級 |
| :--- | :--- | :--- |
| `ci.yaml` | 5-gate 核心 CI 管道 | P0 (Critical) |
| `eco-supplychain-hashlock.yml` | 供應鏈 Hashlock 驗證與 PR 自動修復 | P0 (Critical) |
| `eco-supplychain-attest.yml` | 供應鏈 Cosign 簽章與 Attestation 生成 | P0 (Critical) |
| `ci-failure-to-issue.yaml` | 集中診斷報告生成 (8 步閉環步驟 1-3) | P1 (High) |
| `issues-pr-joint-repair.yaml` | 批次修復引擎執行 (8 步閉環步驟 4-5) | P1 (High) |
| `policy-check.yml` | OPA/Rego 資源合規性檢查 | P1 (High) |
| `auto-sync-deploy.yaml` | 自動化部署與同步 | P2 (Medium) |

## 2. 刪除清單 (Delete List)
以下 Workflow 為冗餘、過時、功能重疊或不再需要的流程，應予以刪除以精簡架構。

| Workflow 文件 | 刪除原因 |
| :--- | :--- |
| `auto-fix-ci.yaml` | 功能已併入 `issues-pr-joint-repair.yaml` |
| `auto-repair.yaml` | 功能已併入 `issues-pr-joint-repair.yaml` |
| `auto-resolve-issues.yaml` | 功能已併入 `issues-pr-joint-repair.yaml` |
| `autonomous-bot.yaml` | 職責不明確，與現有治理機器人衝突 |
| `issues-auto.yaml` | 功能已併入 `ci-failure-to-issue.yaml` |
| `issues-replay.yaml` | 冗餘的重播邏輯 |
| `pr-automation.yaml` | 功能已併入 `Mergify` 與 `joint-repair` |
| `pr-intelligence.yaml` | 功能已併入 `ci-failure-to-issue.yaml` |
| `yaml-lint.yml` | 已由 `policy-check.yml` 與 `hashlock.py` 取代 |
| `test-workflow-syntax.yaml` | 臨時測試文件 |
| `replay.yaml` | 冗餘文件 |
| `issue-automation.yaml` | 功能重疊 |
| `increase-quota.yaml` | 非核心治理流程 |
| `framework-self-maintenance.yaml` | 功能重疊 |

## 3. 執行策略
- **文件刪除**：直接從 `.github/workflows/` 移除對應的 `.yaml` 文件。
- **歷史清理**：使用 `gh run delete` 批量清理已刪除 Workflow 的歷史記錄。
- **綠燈確保**：重新觸發保留清單中的所有 Workflow，確保無錯誤、無警告。
