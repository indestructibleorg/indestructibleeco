# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: documentation
# @ECO-audit-trail: ../../engine/governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated
# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: documentation
# @ECO-audit-trail: ../../engine/governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated
# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: documentation
# @ECO-audit-trail: ../../engine/governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated
# 端到端整合測試
# Enterprise-Grade End-to-End Integration Tests

## 概述 (Overview)

本目錄包含 MachineNativeOps 系統的頂尖企業規格端到端整合測試套件。這些測試驗證整個系統的完整功能流程、性能、可靠性和安全性。

## 測試類型 (Test Types)

### 1. Smoke Tests (快速驗證)
快速驗證核心功能的基本可用性，通常在每次部署後執行。

- `test_smoke_system.py` - 系統初始化和基本功能
- `test_smoke_memory.py` - 記憶體系統基本操作
- `test_smoke_config.py` - 配置管理基本功能
- `test_smoke_reporting.py` - 報告系統基本功能
- `test_smoke_supply_chain.py` - 供應鏈驗證基本流程

### 2. Functional Tests (功能測試)
驗證系統功能的完整性和正確性。

- `test_functional_memory_system.py` - 完整記憶體系統流程
- `test_functional_config_hot_reload.py` - 配置熱重載流程
- `test_functional_report_generation.py` - 完整報告生成流程
- `test_functional_supply_chain_verification.py` - 供應鏈驗證完整流程
- `test_functional_cross_module.py` - 跨模組整合流程

### 3. Performance Tests (性能測試)
驗證系統在負載下的性能表現。

- `test_performance_memory_system.py` - 記憶體系統性能基準
- `test_performance_config_reload.py` - 配置熱重載性能
- `test_performance_report_generation.py` - 報告生成性能
- `test_performance_supply_chain.py` - 供應鏈驗證性能

### 4. Security Tests (安全性測試)
驗證系統的安全性和合規性。

- `test_security_memory_system.py` - 記憶體系統安全
- `test_security_config_management.py` - 配置管理安全
- `test_security_supply_chain.py` - 供應鏈驗證安全
- `test_security_access_control.py` - 訪問控制驗證

### 5. Reliability Tests (可靠性測試)
驗證系統的可靠性和容錯能力。

- `test_reliability_failure_recovery.py` - 故障恢復測試
- `test_reliability_boundary_conditions.py` - 邊界條件測試
- `test_reliability_concurrency.py` - 並發測試

### 6. User Journey Tests (用戶旅程測試)
模擬真實用戶場景的端到端測試。

- `test_journey_devops.py` - DevOps 工程師工作流程
- `test_journey_security_engineer.py` - 安全工程師工作流程
- `test_journey_developer.py` - 開發者工作流程

## 測試環境 (Test Environment)

### 前置條件
- Python 3.11+
- Docker 和 Docker Compose
- Redis Stack
- 足夠的磁盤空間 (至少 5GB)

### 環境設置
```bash
# 1. 啟動測試環境
cd integration-tests
docker-compose -f docker-compose.test.yml up -d

# 2. 安裝測試依賴
pip install -r requirements-test.txt

# 3. 運行所有測試
pytest -v

# 4. 查看測試報告
pytest --html=report.html --cov=. --cov-report=html
```

## 測試執行 (Test Execution)

### 運行所有測試
```bash
pytest -v
```

### 運行特定類型的測試
```bash
# Smoke tests
pytest -m smoke -v

# Functional tests
pytest -m functional -v

# Performance tests
pytest -m performance -v

# Security tests
pytest -m security -v

# Reliability tests
pytest -m reliability -v

# User journey tests
pytest -m user_journey -v
```

### 運行特定測試文件
```bash
pytest test_smoke_system.py -v
```

### 運行特定測試用例
```bash
pytest test_smoke_system.py::test_system_initialization -v
```

### 並行執行
```bash
pytest -n auto -v
```

### 生成覆蓋率報告
```bash
pytest --cov=. --cov-report=html --cov-report=term
```

## 測試配置 (Test Configuration)

### pytest.ini
```ini
[pytest]
testpaths = .
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    smoke: 快速驗證測試
    functional: 功能測試
    performance: 性能測試
    security: 安全測試
    reliability: 可靠性測試
    user_journey: 用戶旅程測試
addopts =
    -v
    --strict-markers
    --tb=short
    --cov=../../ns-root/namespaces-adk
    --cov-report=html
    --cov-report=term
```

### conftest.py
```python
import pytest
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Environment configuration
os.environ["TEST_MODE"] = "true"
os.environ["LOG_LEVEL"] = "DEBUG"

@pytest.fixture(scope="session")
def test_config():
    """Global test configuration"""
    return {
        "redis_host": "localhost",
        "redis_port": 6379,
        "redis_db": 15,  # Use separate DB for tests
        "test_data_dir": Path(__file__).parent / "data",
        "output_dir": Path(__file__).parent / "output",
    }

@pytest.fixture(scope="function")
def test_data(test_config):
    """Fresh test data for each test"""
    data = {
        "test_memories": [],
        "test_configurations": [],
        "test_reports": [],
    }
    yield data
    # Cleanup
    for item in data["test_memories"]:
        # Cleanup test memories
        pass
```

## 測試數據管理 (Test Data Management)

### 測試數據結構
```
integration-tests/
├── data/
│   ├── memories/          # 測試記憶體數據
│   ├── configurations/    # 測試配置文件
│   ├── reports/           # 測試報告模板
│   └── supply_chain/      # 測試供應鏈數據
├── output/                # 測試輸出
│   ├── logs/             # 測試日誌
│   ├── reports/          # 測試報告
│   └── coverage/         # 覆蓋率報告
```

### 測試數據生成
使用工廠模式生成一致的測試數據：

```python
class TestDataFactory:
    """Factory for creating test data"""
    
    @staticmethod
    def create_memory(count=1):
        """Create test memory data"""
        memories = []
        for i in range(count):
            memory = {
                "id": f"test_memory_{i}",
                "content": f"Test memory content {i}",
                "timestamp": datetime.now(),
                "metadata": {"test": True},
            }
            memories.append(memory)
        return memories
    
    @staticmethod
    def create_configuration():
        """Create test configuration"""
        return {
            "version": "1.0.0",
            "settings": {
                "redis": {
                    "host": "localhost",
                    "port": 6379,
                }
            }
        }
```

## 測試報告 (Test Reports)

### HTML 報告
```bash
pytest --html=report.html --self-contained-html
```

### 覆蓋率報告
```bash
pytest --cov=. --cov-report=html
```

### 性能報告
```bash
pytest --benchmark-only --benchmark-json=benchmark.json
```

## CI/CD 集成 (CI/CD Integration)

### GitHub Actions
```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements-test.txt
      - name: Start test environment
        run: docker-compose -f integration-tests/docker-compose.test.yml up -d
      - name: Run integration tests
        run: pytest integration-tests/ -v
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## 最佳實踐 (Best Practices)

### 1. 測試隔離
每個測試應該是獨立的，不依賴其他測試的執行順序或結果。

### 2. 測試清理
每個測試執行後應該清理測試數據和資源。

### 3. 測試命名
使用清晰、描述性的測試名稱，遵循 `test_[feature]_[scenario]_[expected]` 格式。

### 4. 測試斷言
使用明確的斷言消息，便於調試。

### 5. 測試數據
使用一致的測試數據，避免隨機數據導致測試不穩定。

### 6. 測試並行
使用並行執行加速測試，但要確保測試隔離。

### 7. 測試文檔
為複雜的測試添加文檔字符串，說明測試目的和步驟。

## 故障排查 (Troubleshooting)

### 測試環境問題
```bash
# 重啟測試環境
docker-compose -f docker-compose.test.yml down
docker-compose -f docker-compose.test.yml up -d

# 查看日誌
docker-compose -f docker-compose.test.yml logs
```

### 測試失敗
```bash
# 運行失敗的測試並輸出詳細信息
pytest test_smoke_system.py::test_system_initialization -vvv -s

# 運行失敗測試並進入調試器
pytest test_smoke_system.py::test_system_initialization --pdb
```

### Redis 連接問題
```bash
# 檢查 Redis 狀態
docker ps | grep redis
docker logs <redis-container-id>

# 測試 Redis 連接
redis-cli -h localhost -p 6379 ping
```

## 貢獻指南 (Contributing)

### 添加新測試
1. 確定測試類型和場景
2. 創建測試文件，使用適當的 marker
3. 編寫測試用例，遵循最佳實踐
4. 添加測試數據和工具函數
5. 更新文檔
6. 執行測試確保通過

### 測試審查清單
- [ ] 測試是否有明確的目的
- [ ] 測試是否獨立且可重複
- [ ] 測試是否清理測試數據
- [ ] 測試是否有適當的斷言
- [ ] 測試是否有足夠的文檔
- [ ] 測試是否通過所有性能標準

## 聯繫方式 (Contact)

如有問題或建議，請聯繫開發團隊。