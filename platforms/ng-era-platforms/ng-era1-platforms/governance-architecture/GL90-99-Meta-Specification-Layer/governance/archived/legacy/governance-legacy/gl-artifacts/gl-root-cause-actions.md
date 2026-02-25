# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: documentation
# @ECO-audit-trail: ../../engine/governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated
# GL 未成功的真正原因與立即行動

## A. GL 未成功的真正原因

1. **GL 是獨立的「治理專案」，不是開發流程的一部分**
   - GL 檔案放在 `governance/` 目錄，開發者日常工作在 `src/`、`scripts/`、`config/`，兩邊完全不交集。

2. **沒有人在寫 code 時會想到 GL**
   - 沒有 pre-commit hook 檢查 GL 合規、沒有 PR template 要求對應 GL 層級、CI 跑過就算過。

3. **GL 定義太多，實際使用為零**
   - 有 84 個 GL 相關檔案、7 層架構、完整的 YAML 規範，但沒有任何一個功能模組真正「掛載」到 GL 層級上。

4. **重複目錄造成混亂，沒人知道哪個是正確的**
   - `governance/` 和 `workspace/governance/` 完全重複，開發者不知道該看哪個、該改哪個。

5. **GL 是「寫給機器看的規範」，不是「開發者會用的工具」**
   - 沒有 CLI 工具讓開發者快速查詢「我這個功能屬於哪個 GL 層級」、沒有自動分類、沒有實際幫助。

---

## B. 讓 GL 成為主線的立即行動

### 1. 今天：刪掉重複目錄
```bash
rm -rf workspace/governance/
```
一個入口，沒有混亂。

### 2. 今天：在 PR template 加一行
在 `.github/PULL_REQUEST_TEMPLATE.md` 加入：
```markdown
- [ ] 本 PR 涉及的 GL 層級：GL__-__ (如不適用請填 N/A)
```
強迫開發者思考 GL，哪怕只是填 N/A。

### 3. 明天：在 CI 加 GL 標註檢查
在 `.github/workflows/gl-layer-validation.yml` 加一個 job：
- 不用完美，只要「有標註」就 pass，「沒標註」就 warning。
- 讓 GL 出現在每次 PR 的視野裡。

### 4. 本週：在主要模組加 GL 層級註解
在每個主要模組的入口檔案頂部加一行：
```python
# ECO-Layer: GL30-49 (Execution)
```
不用改架構，只是標註。讓 GL 和 code 產生連結。

### 5. 本週：寫一個簡單的 GL 查詢 CLI
```bash
./gl-check src/core/
# 輸出：src/core/ -> GL30-49 (Execution Layer)
```
讓開發者可以「問」GL，而不是「讀」GL 文件。

---

**核心邏輯**：GL 要活，就必須出現在開發者每天會碰到的地方——PR、CI、code 註解。不是放在 `governance/` 目錄裡等人來看。