# ECO 供應鏈規範化 (Canonicalization) 規則

## 1. 目的
為確保 Kubernetes Manifests 的內容哈希 (SHA256) 具備決定性 (Determinism)，必須排除由 Kubernetes Controller 注入的運行時雜訊欄位。

## 2. 排除欄位清單
| 欄位路徑 | 理由 |
| :--- | :--- |
| `metadata.creationTimestamp` | 運行時生成，不代表部署意圖 |
| `metadata.generation` | 運行時遞增，不代表部署意圖 |
| `metadata.managedFields` | 記錄操作歷史，非配置內容 |
| `metadata.resourceVersion` | 運行時變動，非配置內容 |
| `metadata.uid` | 資源唯一標識，非配置內容 |
| `status` | 資源運行狀態，由 Controller 回寫 |

## 3. 變更流程
- 任何新增排除欄位的變更必須通過 PR 提交。
- 必須由 `CODEOWNERS` 中的供應鏈安全專家審核。
- 禁止隨意擴大排除範圍，以避免隱藏惡意配置變更。
