# ECO 供應鏈信任模型 (Trust Model)

## 1. 角色與權限
| 角色 | 權限 | 實體 |
| :--- | :--- | :--- |
| **產生者 (Generator)** | 產生 `hashlock.json` 與 Attestation | GitHub Actions (`eco-supplychain-hashlock.yml`) |
| **驗證者 (Verifier)** | 驗證漂移與證據鏈 | CI Main Pipeline, 審計員 (Local CLI) |
| **維護者 (Maintainer)** | 修改治理腳本與政策 | 專案核心開發者 (PR 審核) |

## 2. 信任鏈 (Chain of Trust)
1. **原始碼**：受 GitHub 分支保護與 PR 審核保護。
2. **生成環境**：GitHub Actions 託管環境，使用受限的 `GH_TOKEN`。
3. **證據鏈**：`hashlock.attestation.intoto.json` 記錄生成時的 Commit SHA 與 Run ID。
4. **驗證**：在 `main` 分支合併前強制執行 `verify_attestation.py` 與 `hashlock.py --mode verify`。

## 3. 異常處理
- **漂移 (Drift)**：任何未經授權的內容變動將導致 CI 失敗。
- **偽造 (Forgery)**：Attestation 哈希不匹配將導致驗證失敗。
- **手動修改**：PR 階段禁止手動編輯 URN/URI，違者阻斷。
