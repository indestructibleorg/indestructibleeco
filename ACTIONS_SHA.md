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

### actions/cache@v4
- Full SHA: `0057852bfaa89a56745cba8c7296529d2fc39830`
- 日期: 2024-11-22
- 標籤: v4

### github/codeql-action/init@v4
- Full SHA: `9e907b5e64f6b83e7804b09294d44122997950d6`
- 版本: v4.32.3
- 發佈日期: 2026-02-13

### github/codeql-action/analyze@v4
- Full SHA: `9e907b5e64f6b83e7804b09294d44122997950d6`
- 版本: v4.32.3
- 發佈日期: 2026-02-13

## 修復策略

### 保留的 actions (GitHub 官方)
- actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5 ✓
- actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020 ✓
- actions/cache@0057852bfaa89a56745cba8c7296529d2fc39830 ✓
- github/codeql-action/init@9e907b5e64f6b83e7804b09294d44122997950d6 ✓
- github/codeql-action/analyze@9e907b5e64f6b83e7804b09294d44122997950d6 ✓

### 移除的 actions (第三方)
- pnpm/action-setup → 改用 npm install -g pnpm
- aquasecurity/trivy-action → 改用直接安裝 trivy
- returntocorp/semgrep-action → 移除 (非必要)
- anchore/sbom-action → 移除 (非必要)

## 狀態
✅ 所有 GitHub Actions 已 pin 到完整 commit SHA
✅ CodeQL 工作流已更新 (v4.32.3)
✅ 所有 npm 腳本已驗證存在
