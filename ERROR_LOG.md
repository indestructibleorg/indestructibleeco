# 錯誤日誌

## 第二輪錯誤：Actions 權限問題

### 錯誤訊息
```
The actions pnpm/action-setup@v2, actions/checkout@v4, actions/setup-node@v4, actions/cache@v4, 
actions/upload-artifact@v4, and 2 others are not allowed in machops/ecosystem because all actions 
must be from a repository owned by machops, created by GitHub, or verified in the GitHub Marketplace. 
All actions must also be pinned to a full-length commit SHA.
```

### 根本原因
儲存庫設定要求：
1. 所有 actions 必須來自 machops 組織、GitHub 官方或經過驗證的 Marketplace
2. 所有 actions 必須 pin 到完整的 commit SHA（不能使用 @v2, @v4 等標籤）

### 修復策略
需要將所有 actions 的版本從標籤改為完整的 commit SHA：
- `actions/checkout@v4` → `actions/checkout@<full-sha>`
- `actions/setup-node@v4` → `actions/setup-node@<full-sha>`
- `pnpm/action-setup@v2` → `pnpm/action-setup@<full-sha>`
- `actions/cache@v4` → `actions/cache@<full-sha>`
- `actions/upload-artifact@v4` → `actions/upload-artifact@<full-sha>`
- `aquasecurity/trivy-action@master` → `aquasecurity/trivy-action@<full-sha>`
- `github/codeql-action/upload-sarif@v3` → `github/codeql-action/upload-sarif@<full-sha>`
- `returntocorp/semgrep-action@v1` → `returntocorp/semgrep-action@<full-sha>`
- `anchore/sbom-action@v0` → `anchore/sbom-action@<full-sha>`

### 下一步
1. 查詢每個 action 的最新穩定版本對應的 commit SHA
2. 更新所有三個工作流程檔案
3. 重新提交並驗證
