# 硬约束交付面 (Hard Constraints Delivery Surface)

> **核心目标**: 建立不可 bypass 的强制交付面，任何不符合硬约束的代码 CI 必须阻断。

---

## 已建立的硬约束交付面

### 1. 接口契约规范 (`HARD_CONSTRAINTS_SPEC.md`)

#### 1.1 公共函数契约
- ✅ 必须有类型注解
- ✅ 必须有 docstring
- ✅ 前置条件必须显式检查
- ✅ 异常必须向上传播，禁止吞掉

#### 1.2 初始化硬约束
- ✅ 初始化失败必须 raise 异常
- ✅ 所有依赖必须验证可用性
- ✅ 运行时检查使用 `_ensure_initialized()`

### 2. 硬约束检查脚本 (`hard_constraints_check.sh`)

| 检查项 | 说明 | CI 阻断 |
|--------|------|---------|
| 类型检查 | `mypy --strict` | ✅ |
| 软初始化 | `if not initialized: return None` | ✅ |
| 裸 except | `except:` 或 `except Exception:` | ✅ |
| 教学注释 | `# TODO:`, `# FIXME:`, `# 需要实现` | ✅ |
| 模拟数据 | `mock_data`, `example_data` | ✅ |
| 条件跳过 | `if not available: return` | ✅ |
| 测试 skip | `@pytest.mark.skip` | ✅ |
| 测试运行 | `pytest` | ✅ |
| 覆盖率 | `>= 80%` | ✅ |

### 3. 硬约束版本服务 (`platform_integration_service.py`)

#### 3.1 自定义异常体系
```python
class PlatformIntegrationError(Exception): ...
class ServiceNotInitializedError(PlatformIntegrationError): ...
class ProviderConfigError(PlatformIntegrationError): ...
class ProviderUnavailableError(PlatformIntegrationError): ...
```

#### 3.2 IntegrationResult 不变量
```python
@dataclass(frozen=True)
class IntegrationResult:
    # 不变量: success=True 时 data 必须不为 None
    # 不变量: success=False 时 error 必须不为 None
```

#### 3.3 运行时硬检查
```python
def _ensure_initialized(self) -> EcoPlatformService:
    """运行时检查，失败直接抛异常"""
    if not self._initialized or self._service is None:
        raise ServiceNotInitializedError(...)
    return self._service
```

### 4. 硬约束测试 (`test_platform_integration_hard_constraints.py`)

#### 4.1 测试分类
| 测试类 | 测试数 | 说明 |
|--------|--------|------|
| `TestInitializationHardConstraints` | 4 | 初始化硬约束 |
| `TestRuntimeHardConstraints` | 5 | 运行时硬约束 |
| `TestIntegrationResultInvariants` | 4 | 结果不变量 |
| `TestTypeAnnotations` | 1 | 类型注解检查 |
| `TestConfigValidation` | 2 | 配置验证 |
| `TestNoSoftFailurePatterns` | 2 | 无软失败模式 |
| `TestIntegration` | 3 | 集成测试 |

#### 4.2 测试特点
- ✅ 所有测试必须全部通过
- ✅ 无 `@pytest.mark.skip`
- ✅ 无 `pytest.skip()`
- ✅ 硬断言，失败即测试失败

---

## 使用方式

### 本地检查

```bash
# 运行硬约束检查
bash hard_constraints_check.sh

# 运行硬约束测试
cd eco-backend
pytest tests/test_platform_integration_hard_constraints.py -v
```

### CI 集成

```yaml
name: Hard Constraints Check

on:
  pull_request:
    branches: [main]

jobs:
  hard-constraints:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Hard Constraints Check
        run: bash hard_constraints_check.sh
```

---

## 禁止模式 vs 允许模式

### ❌ 禁止模式 (软实现)

```python
# 软初始化
def do_something(self):
    if not self._initialized:
        return None  # ❌ 软失败
    ...

# 裸 except
try:
    ...
except:  # ❌ 吞掉所有异常
    return None

# 教学注释
def do_something(self):
    # TODO: 实现这个功能  # ❌ 占位符
    pass

# 模拟数据
def get_data(self):
    mock_data = [...]  # ❌ 假数据
    return mock_data
```

### ✅ 允许模式 (硬实现)

```python
# 硬初始化
def do_something(self) -> ResultType:
    """前置条件: 服务已初始化"""
    service = self._ensure_initialized()  # ✅ 硬检查
    ...

# 异常传播
try:
    ...
except SpecificError as e:  # ✅ 特定异常处理
    raise PlatformIntegrationError(...) from e

# 完整实现
def do_something(self) -> ResultType:
    """完整实现，无占位符"""
    ...  # ✅ 真实实现

# 真实数据源
def get_data(self) -> List[DataType]:
    result = await self.query_data(...)  # ✅ 真实查询
    return result
```

---

## 验收清单

### 每个 PR 必须通过

- [ ] 硬约束检查通过 (`hard_constraints_check.sh`)
- [ ] 所有测试通过 (`pytest`)
- [ ] 覆盖率 >= 80%
- [ ] 无测试 skip
- [ ] 代码审查通过

### 人工审查重点

1. **是否有软失败模式？**
   - `if not initialized: return None/False/[]`
   - `try: ... except: return None`

2. **是否有教学注释？**
   - `# TODO:`
   - `# FIXME:`
   - `# 需要实现`

3. **是否有模拟数据？**
   - `mock_data = [...]`
   - `example_xxx = {...}`

4. **接口是否有契约定义？**
   - 输入参数类型
   - 返回值类型
   - 异常类型

---

## 下一步行动

### 1. 替换旧版本服务

```bash
# 备份旧版本
mv eco-backend/app/services/platform_integration_service.py \
   eco-backend/app/services/platform_integration_service_old.py

# 使用新版本（当前仓库已对齐为 platform_integration_service.py）
ls eco-backend/app/services/platform_integration_service.py
```

### 2. 更新应用启动代码

```python
@app.on_event("startup")
async def startup():
    # 硬约束: 初始化失败导致启动失败
    await platform_integration_service.initialize(config={
        "supabase": {"api_key": "...", "url": "..."},
        "openai": {"api_key": "..."},
    })
```

### 3. 更新 CI 配置

```yaml
# .github/workflows/hard-constraints.yml
name: Hard Constraints

on: [pull_request]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: bash hard_constraints_check.sh
```

---

**交付状态**: ✅ 硬约束交付面已建立  
**执行原则**: 任何不符合硬约束的代码，CI 必须阻断
