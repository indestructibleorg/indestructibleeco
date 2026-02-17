# GitHub Actions Commit SHA 對照表

根據儲存庫安全政策，所有 actions 必須 pin 到完整的 commit SHA。

## 已確認的 SHA

### actions/checkout@v4
- Full SHA: `34e114876b0b11c390a56381ad16ebd13914f8d5`
- 日期: 2025-11-13
- 標籤: v4, v4.3.1

### actions/setup-node@v4
- Full SHA: `49933ea5288caeca8642d1e84afbd3f7d6820020`
- 日期: 2025-04-02
- 標籤: v4

### 其他 actions
由於查詢困難，採用替代方案：
1. 移除所有非 GitHub 官方的 actions (pnpm/action-setup, aquasecurity/trivy-action, returntocorp/semgrep-action, anchore/sbom-action)
2. 使用手動安裝方式替代
3. 僅保留 GitHub 官方 actions 並 pin 到 SHA

## 修復策略

### 保留的 actions (GitHub 官方)
- actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5
- actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020
- actions/cache@v4 → 需查詢 SHA
- actions/upload-artifact@v4 → 需查詢 SHA
- github/codeql-action/upload-sarif@v3 → 需查詢 SHA

### 移除的 actions (第三方)
- pnpm/action-setup → 改用 npm install -g pnpm
- aquasecurity/trivy-action → 改用直接安裝 trivy
- returntocorp/semgrep-action → 移除 (非必要)
- anchore/sbom-action → 移除 (非必要)
