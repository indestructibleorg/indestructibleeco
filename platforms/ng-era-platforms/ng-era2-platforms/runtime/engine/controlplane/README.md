<!-- @ECO-governed -->
<!-- @ECO-layer: GL90-99 -->
<!-- @ECO-semantic: governed-documentation -->
<!-- @ECO-audit-trail: engine/governance/GL_SEMANTIC_ANCHOR.json -->

# Controlplane - 治理控制層

## 📋 概述

Controlplane 是 MachineNativeOps Taxonomy Root Layer 的治理控制層，集中管理所有配置、規格、驗證和治理文件。

### Taxonomy 配置 / 命名索引

- `../root.bootstrap.yaml` - Taxonomy 根入口，定義 controlplane 路徑與版本鎖定
- `../root.fs.map` - FHS 掛載與唯讀範圍索引（controlplane 掛載到 /controlplane）
- `../root.env.sh` - 環境變數索引，提供 controlplane / workspace 錨點
- `config/root.config.yaml` - 根層基線配置
- `config/root.governance.yaml` - 治理與命名策略
- `config/root.modules.yaml` - 模組分類映射
- `registries/` - 模組與 URN 註冊表

---

## 🏗️ 目錄結構

```
controlplane/
├── config/              # 核心配置文件
├── specifications/      # 規格定義
├── registries/          # 模塊和 URN 註冊
├── validation/          # 驗證工具和腳本
├── integration/         # 集成配置
└── documentation/       # 治理文檔
```

---

## 📁 目錄說明

### config/ - 核心配置

**用途**: 存放所有核心配置文件

**文件列表**:
- `root.config.yaml` - 根配置
- `root.governance.yaml` - 治理配置
- `root.modules.yaml` - 模塊配置
- `root.super-execution.yaml` - 超級執行配置
- `root.trust.yaml` - 信任配置
- `root.provenance.yaml` - 來源配置
- `root.integrity.yaml` - 完整性配置
- `root.naming-policy.yaml` - 命名策略
- `root.devices.map` - 設備映射
- `root.kernel.map` - 內核映射

### specifications/ - 規格定義

**用途**: 定義系統規格和標準

**文件列表**:
- `root.specs.naming.yaml` - 命名規格
- `root.specs.references.yaml` - 引用規格
- `root.specs.mapping.yaml` - 映射規格
- `root.specs.logic.yaml` - 邏輯規格
- `root.specs.context.yaml` - 上下文規格

### registries/ - 註冊表

**用途**: 管理模塊和 URN 註冊

**文件列表**:
- `root.registry.modules.yaml` - 模塊註冊表
- `root.registry.urns.yaml` - URN 註冊表

### validation/ - 驗證工具

**用途**: 提供驗證和檢查工具

**文件列表**:
- `root.validator.schema.yaml` - 驗證器模式
- `verify_refactoring.py` - 重構驗證腳本
- `supply-chain-complete-verifier.py` - 供應鏈驗證器

### integration/ - 集成配置

**用途**: 管理系統集成配置

**狀態**: 待添加

### documentation/ - 治理文檔

**用途**: 存放治理相關文檔

**狀態**: 待添加

---

## 🔒 訪問模式

### 運行時

Controlplane 在運行時應該是**只讀**的：

```yaml
# root.fs.map
mounts:
  - name: controlplane
    from: "./controlplane"
    to: "/controlplane"
    mode: "ro"  # 只讀模式
```

### 更新流程

更新 controlplane 配置應該通過：

1. **版本控制**: 通過 Git 提交和審查
2. **CI/CD**: 自動化測試和部署
3. **受控流程**: 需要審批和驗證

---

## 📖 使用指南

### 訪問配置

```bash
# 使用環境變數
source ../root.env.sh

# 查看配置
cat ${CONTROLPLANE_CONFIG}/root.config.yaml

# 查看規格
cat ${CONTROLPLANE_SPECS}/root.specs.naming.yaml

# 查看註冊表
cat ${CONTROLPLANE_REGISTRIES}/root.registry.modules.yaml
```

### 運行驗證

```bash
# 驗證重構
python ${CONTROLPLANE_VALIDATION}/verify_refactoring.py

# 驗證供應鏈
python ${CONTROLPLANE_VALIDATION}/supply-chain-complete-verifier.py
```

### 在代碼中使用

```python
import os
import yaml

# 讀取配置
config_path = os.path.join(
    os.environ['CONTROLPLANE_CONFIG'],
    'root.config.yaml'
)

with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

# 讀取規格
specs_path = os.path.join(
    os.environ['CONTROLPLANE_SPECS'],
    'root.specs.naming.yaml'
)

with open(specs_path, 'r') as f:
    specs = yaml.safe_load(f)
```

---

## 🔍 配置文件說明

### root.config.yaml

**用途**: 根配置文件，定義系統的核心配置

**關鍵配置**:
- 系統版本
- 基礎路徑
- 默認設置

### root.governance.yaml

**用途**: 治理配置，定義治理規則和流程

**關鍵配置**:
- 治理模型
- 審批流程
- 權限控制

### root.modules.yaml

**用途**: 模塊配置，定義系統模塊

**關鍵配置**:


- 模塊列表
- 模塊依賴
- 模塊版本

### root.super-execution.yaml

**用途**: 超級執行配置，定義高級執行策略

**關鍵配置**:


- 執行模式
- 資源限制
- 安全策略

---

## 🎯 設計原則

1. **集中管理**: 所有治理文件集中在一處
2. **版本控制**: 所有配置都在 Git 中追蹤
3. **只讀運行**: 運行時不可修改
4. **分類清晰**: 按功能分類組織
5. **易於訪問**: 通過環境變數訪問

---

## 📊 文件統計

| 目錄 | 文件數 | 說明 |
|------|--------|------|
| config/ | 10 | 核心配置文件 |
| specifications/ | 5 | 規格定義文件 |
| registries/ | 2 | 註冊表文件 |
| validation/ | 3 | 驗證工具 |
| integration/ | 0 | 待添加 |
| documentation/ | 0 | 待添加 |
| **總計** | **20** | **所有文件** |

---

## ⚠️ 注意事項

### 不要直接修改

❌ **錯誤做法**:
```bash
# 直接修改 controlplane 文件
vim controlplane/config/root.config.yaml
```

✅ **正確做法**:
```bash
# 1. 在開發分支修改
git checkout -b update-config

# 2. 修改文件
vim controlplane/config/root.config.yaml

# 3. 提交和審查
git add controlplane/config/root.config.yaml
git commit -m "Update root config"
git push origin update-config

# 4. 創建 PR 並審查
gh pr create --title "Update root config"
```

### 版本管理

所有 controlplane 文件都應該：
- ✅ 在 Git 中追蹤
- ✅ 通過 PR 審查
- ✅ 有清晰的提交信息
- ✅ 經過驗證測試

### 環境變數

始終使用環境變數訪問 controlplane：

```bash
# 正確
cat ${CONTROLPLANE_CONFIG}/root.config.yaml

# 避免硬編碼
cat controlplane/config/root.config.yaml
```

---

## 🔗 相關資源

- **根層 README**: `../README.md`
- **重構報告**: `../workspace/PROJECT_RESTRUCTURE_REPORT.md`
- **項目文檔**: `../workspace/docs/`

---

**版本**: v1.0.0  
**最後更新**: 2024-12-23  
**維護者**: MachineNativeOps Team
