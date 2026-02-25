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
# 性能基準測試
# Enterprise-Grade Performance Benchmarking

## 概述 (Overview)

本目錄包含 MachineNativeOps 系統的頂尖企業規格性能基準測試套件。這些測試建立完整的性能監控、分析和報告機制，確保系統在各種負載條件下達到企業級性能標準。

## 測試類型 (Test Types)

### 1. Unit Performance Tests（單元性能測試）
測試單個操作的性能，建立微基準。

- `test_unit_memory_operations.py` - 記憶體操作性能（add, get, delete, search）
- `test_unit_cache_operations.py` - 緩存操作性能（hit, miss, eviction）
- `test_unit_config_operations.py` - 配置操作性能（load, reload, validate）
- `test_unit_report_operations.py` - 報告操作性能（PDF generation, chart rendering）

### 2. Component Performance Tests（組件性能測試）
測試整個組件的性能，包括完整的工作流程。

- `test_component_memory_system.py` - 記憶體系統完整流程性能
- `test_component_config_system.py` - 配置系統完整流程性能
- `test_component_report_system.py` - 報告系統完整流程性能
- `test_component_supply_chain.py` - 供應鏈驗證完整流程性能

### 3. System Performance Tests（系統性能測試）
測試整個系統在負載下的性能表現。

- `test_system_throughput.py` - 吞吐量測試
- `test_system_latency.py` - 延遲測試（P50, P95, P99）
- `test_system_concurrency.py` - 並發測試
- `test_system_resource_usage.py` - 資源使用測試

### 4. Stress & Endurance Tests（壓力和耐久測試）
測試系統在極端條件下的穩定性和可靠性。

- `test_stress_load.py` - 負載測試
- `test_stress_spike.py` - 尖峰測試
- `test_endurance_stability.py` - 耐久測試（24h, 7d）

## 性能基準 (Performance Baselines)

### 記憶體系統基準

| 操作 | 吞吐量 | P50 | P95 | P99 |
|------|--------|-----|-----|-----|
| Add Memory | >10,000 ops/sec | <1ms | <5ms | <10ms |
| Get Memory | >20,000 ops/sec | <0.5ms | <2ms | <5ms |
| Delete Memory | >15,000 ops/sec | <1ms | <3ms | <8ms |
| Search Memory | >1,000 ops/sec | <10ms | <50ms | <100ms |
| Semantic Search | >500 ops/sec | <20ms | <100ms | <200ms |
| Cache Hit | >50,000 ops/sec | <0.1ms | <0.5ms | <1ms |
| Cache Miss | >10,000 ops/sec | <1ms | <5ms | <10ms |

### 配置管理基準

| 操作 | 吞吐量 | P50 | P95 | P99 |
|------|--------|-----|-----|-----|
| Load Configuration | >100 ops/sec | <10ms | <50ms | <100ms |
| Hot Reload | >10 ops/sec | <100ms | <500ms | <1s |
| Validate Configuration | >200 ops/sec | <5ms | <20ms | <50ms |

### 報告系統基準

| 操作 | 吞吐量 | P50 | P95 | P99 |
|------|--------|-----|-----|-----|
| Generate PDF (10p) | >10 ops/min | <5s | <8s | <10s |
| Generate PDF (50p) | >2 ops/min | <15s | <20s | <30s |
| Render Chart | >20 ops/sec | <100ms | <500ms | <1s |

### 供應鏈驗證基準

| 項目大小 | 驗證時間 | 內存 | CPU |
|----------|----------|------|-----|
| Small | <1min | <100MB | <50% |
| Medium | <5min | <500MB | <80% |
| Large | <15min | <2GB | <100% |

## 測試環境 (Test Environment)

### 前置條件
- Python 3.11+
- Docker 和 Docker Compose
- 足夠的系統資源（建議 8GB+ RAM, 4+ CPU）
- Redis Stack
- Prometheus（可選）
- Grafana（可選）

### 環境設置
```bash
# 1. 安裝測試依賴
pip install -r requirements-performance.txt

# 2. 啟動測試環境
cd performance-tests
docker-compose -f docker-compose.performance.yml up -d

# 3. 運行性能基準測試
pytest -m performance -v

# 4. 查看性能報告
pytest --benchmark-only --benchmark-json=benchmark.json
```

## 測試執行 (Test Execution)

### 運行所有性能測試
```bash
pytest -m performance -v
```

### 運行特定類型的性能測試
```bash
# Unit performance tests
pytest test_unit_memory_operations.py -v

# Component performance tests
pytest test_component_memory_system.py -v

# System performance tests
pytest test_system_throughput.py -v

# Stress tests
pytest test_stress_load.py -v
```

### 使用 pytest-benchmark
```bash
# 運行基準測試
pytest --benchmark-only -v

# 生成 JSON 報告
pytest --benchmark-only --benchmark-json=benchmark.json

# 生成 HTML 報告
pytest --benchmark-only --benchmark-html=benchmark.html

# 比較基準
pytest --benchmark-only --benchmark-autosave
pytest --benchmark-compare=baseline.json
```

### 使用 Locust 進行負載測試
```bash
# 啟動 Locust web interface
locust -f locustfiles/load_test.py --host=[EXTERNAL_URL_REMOVED]

# 運行 headless 模式
locust -f locustfiles/load_test.py --headless -u 100 -r 10 -t 10m

# 生成報告
locust -f locustfiles/load_test.py --headless -u 100 -r 10 -t 10m --html=locust_report.html
```

## 測試配置 (Test Configuration)

### pytest.ini
```ini
[pytest]
testpaths = .
python_files = test_*.py
python_classes = PerformanceTest*
python_functions = test_*

markers =
    performance: 性能測試
    unit_performance: 單元性能測試
    component_performance: 組件性能測試
    system_performance: 系統性能測試
    stress: 壓力測試
    endurance: 耐久測試
    benchmark: 基準測試

addopts =
    -v
    --strict-markers
    --tb=short
    --benchmark-disable
```

### Performance Config
```python
# config/performance_config.py
PERFORMANCE_CONFIG = {
    "memory": {
        "add_operations": 10000,
        "get_operations": 20000,
        "delete_operations": 15000,
        "search_operations": 1000,
    },
    "concurrency": {
        "users": [10, 50, 100],
        "duration": "10m",
    },
    "load": {
        "target_load": 1000,
        "ramp_up_time": "5m",
        "duration": "30m",
    },
}
```

## 性能監控 (Performance Monitoring)

### 系統監控
- **CPU**: CPU 使用率、CPU 時間
- **Memory**: 內存使用、內存分配
- **Disk I/O**: 讀寫速度、IOPS
- **Network**: 網絡帶寬、網絡延遲

### 應用監控
- **Throughput**: 操作/秒
- **Latency**: P50, P95, P99 延遲
- **Error Rate**: 錯誤率
- **Success Rate**: 成功率

### 監控工具
```bash
# 啟動 Prometheus
docker-compose -f docker-compose.performance.yml up -d prometheus

# 啟動 Grafana
docker-compose -f docker-compose.performance.yml up -d grafana

# 查看指標
curl [EXTERNAL_URL_REMOVED]
```

## 性能報告 (Performance Reports)

### 基準報告
```bash
pytest --benchmark-only --benchmark-json=benchmark.json

# 查看報告
python scripts/analyze_benchmark.py benchmark.json
```

### 趨勢報告
```bash
# 比較歷史基準
pytest --benchmark-compare=baseline.json

# 生成趨勢圖
python scripts/generate_trend_report.py
```

### 資源報告
```bash
# 收集資源使用數據
python scripts/collect_resource_metrics.py

# 生成資源報告
python scripts/generate_resource_report.py
```

## CI/CD 集成 (CI/CD Integration)

### GitHub Actions
```yaml
name: Performance Tests

on: [push, pull_request, schedule]

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements-performance.txt
      - name: Start test environment
        run: docker-compose -f performance-tests/docker-compose.performance.yml up -d
      - name: Run performance tests
        run: pytest performance-tests/ -m performance --benchmark-only
      - name: Upload benchmark results
        uses: actions/upload-artifact@v3
        with:
          name: benchmark-results
          path: benchmark.json
```

## 最佳實踐 (Best Practices)

### 1. 測試隔離
每個性能測試應該獨立運行，避免相互影響。

### 2. 預熱測試
運行性能測試前進行預熱，確保系統達到穩定狀態。

### 3. 多次運行
每個測試運行多次，取平均值減少波動。

### 4. 資源監控
同時監控系統資源使用，分析性能瓶頸。

### 5. 基準比較
與歷史基準比較，檢測性能回歸。

### 6. 環境一致性
使用一致的測試環境，確保結果可比較。

## 性能優化 (Performance Optimization)

### 常見瓶頸
1. **CPU**: 計算密集型操作
2. **Memory**: 內存分配和釋放
3. **I/O**: 磁盤和網絡 I/O
4. **Lock**: 並發鎖競爭

### 優化策略
1. **算法優化**: 使用更高效的算法
2. **緩存優化**: 增加緩存命中率
3. **並發優化**: 提高並發處理能力
4. **資源優化**: 優化資源使用效率

## 故障排查 (Troubleshooting)

### 性能不達標
```bash
# 1. 運行性能分析
python -m cProfile -o profile.stats test_unit_memory_operations.py

# 2. 分析性能熱點
python scripts/analyze_profile.py profile.stats

# 3. 檢查資源使用
python scripts/check_resource_usage.py
```

### 測試不穩定
```bash
# 1. 檢查系統負載
top -b -n 1

# 2. 檢查網絡延遲
ping localhost

# 3. 檢查磁盤 I/O
iostat -x 1 5
```

## 聯繫方式 (Contact)

如有問題或建議，請聯繫開發團隊。