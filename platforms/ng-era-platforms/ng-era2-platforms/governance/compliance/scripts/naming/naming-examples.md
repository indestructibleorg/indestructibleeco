# @ECO-layer: GL60-80
# @ECO-governed
# GL 命名驗證工具使用範例

## 概述

本文檔提供 GL Naming Validator 工具的完整使用範例和最佳實踐。

## 安裝

```bash
# 複製腳本到可執行路徑
chmod +x gl-governance-compliance/scripts/naming/gl_naming_validator.py

# 或創建符號鏈接
ln -s /path/to/gl_naming_validator.py /usr/local/bin/gl-naming-validator
```

## 命令行使用

### 1. 驗證語意節點（Semantic Node）

**有效範例**：
```bash
# 驗證實體類型
python3 gl_naming_validator.py semantic-node entity user
# 輸出: ✅ All naming conventions are valid!

# 驗證事件類型
python3 gl_naming_validator.py semantic-node event user_created
# 輸出: ✅ All naming conventions are valid!

# 驗證屬性類型
python3 gl_naming_validator.py semantic-node attribute email
# 輸出: ✅ All naming conventions are valid!
```

**無效範例**：
```bash
# 錯誤的實體類型
python3 gl_naming_validator.py semantic-node invalid_type user
# 輸出: ❌ Naming validation failed with violations.
# [1] Name: invalid_type
#     Message: 無效的實體類型: invalid_type
#     Expected: 必須是以下之一: entity, relation, attribute, event

# 錯誤的實體名稱格式（使用駝峰命名）
python3 gl_naming_validator.py semantic-node entity UserProfile
# 輸出: ❌ Naming validation failed with violations.
# [1] Name: UserProfile
#     Message: 實體名稱格式錯誤: UserProfile
#     Expected: 必須使用全小寫，用下劃線分隔多個單詞
#     Example: user, created_at, is_active
```

### 2. 驗證語意鍵（Semantic Key）

**有效範例**：
```bash
# API 相關鍵
python3 gl_naming_validator.py semantic-key api schema
# 輸出: ✅ All naming conventions are valid!

python3 gl_naming_validator.py semantic-key api endpoint
# 輸出: ✅ All naming conventions are valid!

# 配置相關鍵
python3 gl_naming_validator.py semantic-key config timeout
# 輸出: ✅ All naming conventions are valid!

python3 gl_naming_validator.py semantic-key config retry
# 輸出: ✅ All naming conventions are valid!

# 元資料相關鍵
python3 gl_naming_validator.py semantic-key metadata label
# 輸出: ✅ All naming conventions are valid!
```

**無效範例**：
```bash
# 錯誤的鍵類別格式（使用大寫）
python3 gl_naming_validator.py semantic-key API schema
# 輸出: ❌ Naming validation failed with violations.
# [1] Name: API
#     Message: 鍵類別格式錯誤: API
#     Expected: 必須使用全小寫和數字

# 錯誤的鍵名格式（使用連字符）
python3 gl_naming_validator.py semantic-key api api-schema
# 輸出: ❌ Naming validation failed with violations.
# [1] Name: api-schema
#     Message: 鍵名格式錯誤: api-schema
#     Expected: 必須使用全小寫和數字
```

### 3. 驗證 API 路徑（API Path）

**有效範例**：
```bash
# 單層路徑
python3 gl_naming_validator.py api-path runtime
# 輸出: ✅ All naming conventions are valid!

# 多層路徑
python3 gl_naming_validator.py api-path runtime dag
# 輸出: ✅ All naming conventions are valid!

python3 gl_naming_validator.py api-path runtime jobs list
# 輸出: ✅ All naming conventions are valid!

# API 路徑
python3 gl_naming_validator.py api-path api schema
# 輸出: ✅ All naming conventions are valid!
```

**無效範例**：
```bash
# 空路徑
python3 gl_naming_validator.py api-path
# 輸出: ❌ Naming validation failed with violations.
# [1] Name: 
#     Message: API 路徑不能為空

# 錯誤的路徑格式（使用連字符）
python3 gl_naming_validator.py api-path runtime-dag
# 輸出: ❌ Naming validation failed with violations.
# [1] Name: runtime-dag
#     Message: 路徑部分格式錯誤: runtime-dag
#     Expected: 必須使用全小寫和數字
#     Example: runtime, dag, jobs
```

### 4. 驗證 K8s 標籤（K8s Label）

**有效範例**：
```bash
# 平台相關標籤
python3 gl_naming_validator.py k8s-label platform runtime
# 輸出: ✅ All naming conventions are valid!

python3 gl_naming_validator.py k8s-label service dag
# 輸出: ✅ All naming conventions are valid!

# 版本標籤
python3 gl_naming_validator.py k8s-label version v1.0.0
# 輸出: ✅ All naming conventions are valid!
```

**無效範例**：
```bash
# 空標籤
python3 gl_naming_validator.py k8s-label
# 輸出: ❌ Naming validation failed with violations.
# [1] Name: 
#     Message: K8s 標籤不能為空

# 錯誤的標籤格式（使用大寫）
python3 gl_naming_validator.py k8s-label Platform Runtime
# 輸出: ❌ Naming validation failed with violations.
# [1] Name: Platform
#     Message: 標籤部分格式錯誤: Platform
#     Expected: 必須使用全小寫和數字
#     Example: platform, runtime, service
```

## Python API 使用

### 基本使用

```python
from gl_naming_validator import GLNamingValidator, NamingType

# 創建驗證器實例
validator = GLNamingValidator()

# 驗證語意節點
result = validator.validate_semantic_node('entity', 'user')
print(f"Semantic node validation: {'✅' if result else '❌'}")

# 驗證語意鍵
result = validator.validate_semantic_key('api', 'schema')
print(f"Semantic key validation: {'✅' if result else '❌'}")

# 驗證 API 路徑
result = validator.validate_api_path('runtime', 'dag')
print(f"API path validation: {'✅' if result else '❌'}")

# 驗證 K8s 標籤
result = validator.validate_k8s_label('platform', 'runtime')
print(f"K8s label validation: {'✅' if result else '❌'}")

# 生成報告
print(validator.generate_report())
```

### 批量驗證

```python
from gl_naming_validator import GLNamingValidator

# 創建驗證器實例
validator = GLNamingValidator()

# 批量驗證多個名稱
names_to_validate = [
    ('semantic-node', 'entity', 'user'),
    ('semantic-key', 'api', 'schema'),
    ('api-path', 'runtime', 'dag'),
    ('k8s-label', 'platform', 'runtime')
]

for naming_type, *args in names_to_validate:
    if naming_type == 'semantic-node':
        validator.validate_semantic_node(*args)
    elif naming_type == 'semantic-key':
        validator.validate_semantic_key(*args)
    elif naming_type == 'api-path':
        validator.validate_api_path(*args)
    elif naming_type == 'k8s-label':
        validator.validate_k8s_label(*args)

# 生成並打印報告
print(validator.generate_report())
```

## 完整範例

### 範例 1：驗證完整的用戶服務命名

```python
from gl_naming_validator import GLNamingValidator

validator = GLNamingValidator()

# 驗證用戶實體
validator.validate_semantic_node('entity', 'user')

# 驗證用戶屬性
validator.validate_semantic_node('attribute', 'email')
validator.validate_semantic_node('attribute', 'created_at')

# 驗證 API 配置鍵
validator.validate_semantic_key('api', 'schema')
validator.validate_semantic_key('config', 'timeout')
validator.validate_semantic_key('config', 'retry')

# 驗證 API 路徑
validator.validate_api_path('api', 'users', 'list')
validator.validate_api_path('api', 'users', 'create')

# 驗證 K8s 標籤
validator.validate_k8s_label('service', 'users')
validator.validate_k8s_label('version', 'v1.0.0')

# 生成報告
print(validator.generate_report())
```

### 範例 2：集成到 CI/CD Pipeline

```yaml
# .github/workflows/naming-validation.yml
name: Naming Convention Validation

on: [push, pull_request]

jobs:
  validate-naming:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install pyyaml
      
      - name: Validate naming conventions
        run: |
          python3 gl-governance-compliance/scripts/naming/gl_naming_validator.py \
            semantic-node entity user
          python3 gl-governance-compliance/scripts/naming/gl_naming_validator.py \
            semantic-key api schema
          python3 gl-governance-compliance/scripts/naming/gl_naming_validator.py \
            api-path runtime dag
```

### 範例 3：Pre-commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash

echo "Validating naming conventions..."

# 驗證所有新增的 Python 文件中的命名
for file in $(git diff --name-only --cached | grep '\.py$'); do
    # 檢查文件中的 GL 命名
    python3 gl-governance-compliance/scripts/naming/gl_naming_validator.py \
        --file "$file"
done

echo "Naming validation complete!"
```

## 錯誤處理

### 處理驗證失敗

```python
from gl_naming_validator import GLNamingValidator

validator = GLNamingValidator()

# 執行驗證
validator.validate_semantic_node('invalid_type', 'user')

# 檢查是否有違規
if validator.violations:
    print("❌ Naming validation failed:")
    for violation in validator.violations:
        print(f"  - {violation['message']}")
        print(f"    Expected: {violation.get('expected', 'N/A')}")
        print(f"    Example: {violation.get('example', 'N/A')}")

# 檢查是否有警告
if validator.warnings:
    print("⚠️  Warnings:")
    for warning in validator.warnings:
        print(f"  - {warning['message']}")
```

### 獲取詳細報告

```python
from gl_naming_validator import GLNamingValidator

validator = GLNamingValidator()

# 執行驗證
validator.validate_semantic_node('entity', 'user')
validator.validate_semantic_key('api', 'schema')

# 獲取完整報告
report = validator.generate_report()

# 保存報告到文件
with open('naming_validation_report.txt', 'w') as f:
    f.write(report)

print("Report saved to naming_validation_report.txt")
```

## 最佳實踐

### 1. 在開發過程中使用

```python
# 在定義新的語意節點時立即驗證
validator = GLNamingValidator()

# 驗證新實體定義
entity_type = 'entity'
entity_name = 'order'

if validator.validate_semantic_node(entity_type, entity_name):
    print(f"✅ Entity '{entity_name}' naming is valid")
    # 繼續實現
else:
    print(f"❌ Entity '{entity_name}' naming is invalid")
    print(validator.generate_report())
    # 修復命名錯誤
```

### 2. 集成到測試套件

```python
# tests/test_naming_conventions.py
import unittest
from gl_naming_validator import GLNamingValidator

class TestNamingConventions(unittest.TestCase):
    def setUp(self):
        self.validator = GLNamingValidator()
    
    def test_valid_semantic_nodes(self):
        """測試有效的語意節點"""
        valid_nodes = [
            ('entity', 'user'),
            ('entity', 'order'),
            ('attribute', 'email'),
            ('event', 'user_created')
        ]
        
        for entity_type, entity_name in valid_nodes:
            with self.subTest(type=entity_type, name=entity_name):
                self.assertTrue(
                    self.validator.validate_semantic_node(entity_type, entity_name),
                    f"Valid naming failed for {entity_type}.{entity_name}"
                )
    
    def test_invalid_semantic_nodes(self):
        """測試無效的語意節點"""
        invalid_nodes = [
            ('invalid_type', 'user'),
            ('entity', 'UserProfile'),
            ('attribute', 'User-Email')
        ]
        
        for entity_type, entity_name in invalid_nodes:
            with self.subTest(type=entity_type, name=entity_name):
                self.assertFalse(
                    self.validator.validate_semantic_node(entity_type, entity_name),
                    f"Invalid naming passed for {entity_type}.{entity_name}"
                )
    
    def test_api_paths(self):
        """測試 API 路徑驗證"""
        valid_paths = [
            ('runtime', 'dag'),
            ('api', 'users'),
            ('api', 'orders', 'create')
        ]
        
        for path_parts in valid_paths:
            with self.subTest(path=path_parts):
                self.assertTrue(
                    self.validator.validate_api_path(*path_parts),
                    f"Valid API path failed for {'/'.join(path_parts)}"
                )

if __name__ == '__main__':
    unittest.main()
```

### 3. 自動化修復建議

```python
from gl_naming_validator import GLNamingValidator

validator = GLNamingValidator()

# 檢查無效命名
validator.validate_semantic_node('entity', 'UserProfile')

# 根據違規提供修復建議
if validator.violations:
    print("❌ Found naming violations:")
    print()
    for violation in validator.violations:
        name = violation.get('name', 'N/A')
        message = violation.get('message', '')
        expected = violation.get('expected', '')
        
        print(f"Name: {name}")
        print(f"Issue: {message}")
        print(f"Fix: {expected}")
        print()
        
        # 自動生成建議的修復
        if '駝峰命名' in message:
            # 轉換為蛇形命名
            fixed_name = ''.join(['_' + c.lower() if c.isupper() else c 
                                  for c in name]).lstrip('_')
            print(f"💡 Suggested fix: {fixed_name}")
```

## 擴展功能

### 自定義驗證規則

```python
from gl_naming_validator import GLNamingValidator

class CustomNamingValidator(GLNamingValidator):
    def validate_custom_rule(self, name: str, pattern: str) -> bool:
        """自定義驗證規則"""
        import re
        if not re.match(pattern, name):
            self.violations.append({
                'name': name,
                'message': f'Custom validation failed for {name}',
                'expected': f'Pattern: {pattern}'
            })
            return False
        return True

# 使用自定義驗證器
validator = CustomNamingValidator()

# 添加自定義驗證規則
validator.validate_custom_rule('custom_entity', r'^custom_[a-z_]+$')
```

### 批量文件驗證

```python
import os
import re
from gl_naming_validator import GLNamingValidator

def validate_file_names(directory: str):
    """驗證目錄中的所有文件名"""
    validator = GLNamingValidator()
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            # 只檢查以 gl 開頭的文件
            if file.startswith('gl'):
                file_path = os.path.join(root, file)
                
                # 驗證文件名是否符合平台命名規則
                result = validator.validate(file, NamingType.PLATFORM, file_path)
                
                if not result:
                    print(f"❌ Invalid file name: {file}")
    
    # 生成報告
    print(validator.generate_report())

# 使用
validate_file_names('./gl-governance-compliance')
```

## 故障排除

### 常見問題

**Q: 為什麼我的命名驗證失敗？**

A: 檢查以下幾點：
1. 是否使用了正確的命名類型
2. 是否符合該類型的格式要求
3. 是否使用了正確的字符集（全小寫、下劃線等）
4. 查看驗證報告中的詳細錯誤信息

**Q: 如何處理遺留代碼中的不符合規範的命名？**

A: 建議採用以下策略：
1. 先驗證新代碼的命名
2. 逐步重構遺留代碼
3. 使用工具自動修復常見問題
4. 添加過渡期的例外處理

**Q: 能否自定義驗證規則？**

A: 可以繼承 `GLNamingValidator` 類並添加自定義驗證方法。參考「擴展功能」部分。

## 參考資源

- [GL 前綴使用原則（工程版）](../contracts/naming-governance/gl-prefix-principles-engineering.md)
- [GL 擴展命名本體 v3.0.0](../contracts/naming-governance/gl-naming-ontology-expanded.yaml)
- [GL 命名契約註冊表](../../registry/naming/gl-naming-contracts-registry.yaml)

---

**文檔版本**: 1.0.0  
**最後更新**: 2026-02-01  
**維護者**: GL Governance Team