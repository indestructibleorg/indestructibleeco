<!-- @ECO-governed -->
<!-- @ECO-layer: GL90-99 -->
<!-- @ECO-semantic: governed-documentation -->
<!-- @ECO-audit-trail: engine/governance/GL_SEMANTIC_ANCHOR.json -->

# GL (Governance Layers) 架構

GL 是 MachineNativeOps 的核心治理架構，定義了從戰略到執行的完整治理層級。

## 目錄結構

```
gl/
├── architecture/          # GL 核心架構定義
├── 00-strategic/          # GL00-09 戰略層
├── 10-operational/        # GL10-29 運營層
├── 30-execution/          # GL30-49 執行層
├── 50-observability/      # GL50-59 觀測層
├── 60-feedback/           # GL60-80 回饋層
├── 81-extended/           # GL81-83 擴展層
├── 90-meta/               # GL90-99 元規範層
└── sealed/                # 已封存的治理決策
```

## GL 層級速查

| 層級 | 名稱 | 職責 |
|------|------|------|
| GL00-09 | Strategic | 願景、架構、決策、風險、合規 |
| GL10-29 | Operational | 政策、流程、工具、品質管理 |
| GL30-49 | Execution | 模板、Schema、自動化、配置 |
| GL50-59 | Observability | 監控、指標、告警、洞察 |
| GL60-80 | Feedback | AI優化、回饋機制、審計 |
| GL81-83 | Extended | 外部整合、自動評論 |
| GL90-99 | Meta | 命名規範、語意定義 |

## 快速使用

```bash
# 查詢檔案的 GL 層級
./scripts/gl-check src/core/

# 驗證 GL 結構
python scripts/gl-engine/gl_validator.py --workspace .
```

## 在程式碼中標註 GL 層級

```python
# ECO-Layer: GL30-49 (Execution)
"""模組說明"""
```

```yaml
# ECO-Layer: GL10-29
metadata:
  layer: "GL10-29"
```