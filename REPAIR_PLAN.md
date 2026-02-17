# 修復方案

## 推理結果

### 問題根源
1. **架構不匹配**：工作流程假設 monorepo 多平台架構，實際是單一全端應用
2. **缺失 lint script**：CI 需要 `pnpm run lint` 但 package.json 中不存在
3. **路徑過濾器錯誤**：build-and-deploy.yml 監聽不存在的目錄
4. **過度複雜的部署流程**：包含 Docker、Kubernetes、ArgoCD 等未配置的基礎設施

### 最佳修復方案

#### 方案 A：完全重寫工作流程（推薦）
**優點**：
- 與實際專案結構完全對齊
- 移除所有不必要的複雜度
- 確保每個步驟都可執行
- 防呆機制：只包含已驗證的步驟

**步驟**：
1. 新增 `lint` script 到 package.json
2. 重寫 ci.yml 為簡化版本
3. 重寫 build-and-deploy.yml 為簡化版本
4. 移除所有 Docker/K8s 相關步驟

#### 方案 B：修補現有工作流程
**缺點**：
- 仍保留不必要的複雜度
- 可能有隱藏的依賴問題
- 維護成本高

**結論**：採用方案 A

## 具體修改清單

### 1. package.json
```json
"scripts": {
  "lint": "tsc --noEmit",
  ...existing scripts
}
```

### 2. .github/workflows/ci.yml
- 移除 workspace 過濾器
- 使用根目錄建置命令
- 簡化為：checkout → install → lint → test → build

### 3. .github/workflows/build-and-deploy.yml
- 移除 paths 過濾器中的不存在目錄
- 移除 matrix strategy
- 移除所有 Docker/K8s/ArgoCD 步驟
- 保留：commit validation → lint → test → build

### 4. 移除 cd.yml（如果存在且不必要）

## 驗證計劃
1. 本地測試所有 npm scripts
2. 提交到新分支
3. 觀察 GitHub Actions 執行結果
4. 確認所有工作流程通過
5. 提交 PR
