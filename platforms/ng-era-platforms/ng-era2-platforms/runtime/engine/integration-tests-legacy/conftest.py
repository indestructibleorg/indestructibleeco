#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: conftest
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
"""
Configuration and fixtures for integration tests
"""
# MNGA-002: Import organization needs review
import pytest
import os
import sys
import time
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import redis
import json
# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
# Environment configuration
os.environ["TEST_MODE"] = "true"
os.environ["LOG_LEVEL"] = "INFO"
# Test markers
pytest_plugins = []
class TestDataFactory:
    """Factory for creating test data"""
    @staticmethod
    def create_memory(count: int = 1, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Create test memory data"""
        memories = []
        for i in range(count):
            memory = {
                "id": f"test_memory_{int(time.time() * 1000)}_{i}",
                "content": f"Test memory content {i} with semantic meaning",
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {"test": True, "batch": i},
                "tags": ["test", "integration"],
            }
            memories.append(memory)
        return memories
    @staticmethod
    def create_configuration(version: str = "1.0.0") -> Dict[str, Any]:
        """Create test configuration"""
        return {
            "version": version,
            "settings": {
                "redis": {
                    "host": "localhost",
                    "port": 6379,
                    "db": 15,
                    "max_connections": 50,
                },
                "cache": {
                    "enabled": True,
                    "ttl": 3600,
                    "max_size": 1000,
                },
                "monitoring": {
                    "enabled": True,
                    "interval": 60,
                },
            },
            "features": {
                "vector_search": True,
                "semantic_cache": True,
                "memory_compaction": True,
            },
        }
    @staticmethod
    def create_report_data(num_charts: int = 5, num_tables: int = 3) -> Dict[str, Any]:
        """Create test report data"""
        import random
        charts = []
        for i in range(num_charts):
            chart_type = random.choice(["bar", "line", "pie", "scatter"])
            chart_data = {
                "type": chart_type,
                "title": f"Test Chart {i+1}",
                "data": {
                    "labels": [f"Item {j}" for j in range(10)],
                    "datasets": [{
                        "label": f"Dataset {i}",
                        "data": [random.randint(0, 100) for _ in range(10)],
                    }],
                },
            }
            charts.append(chart_data)
        tables = []
        for i in range(num_tables):
            table_data = {
                "title": f"Test Table {i+1}",
                "headers": ["Column 1", "Column 2", "Column 3"],
                "rows": [
                    [f"Row {j}", str(random.randint(0, 100)), str(random.random())]
                    for j in range(10)
                ],
            }
            tables.append(table_data)
        return {
            "title": "Integration Test Report",
            "created_at": datetime.now().isoformat(),
            "charts": charts,
            "tables": tables,
            "metadata": {
                "test": True,
                "generated_by": "integration-tests",
            },
        }
    @staticmethod
    def create_supply_chain_project(size: str = "small") -> Dict[str, Any]:
        """Create test supply chain project"""
        sizes = {
            "small": {"files": 10, "depth": 2, "services": 3},
            "medium": {"files": 50, "depth": 4, "services": 10},
            "large": {"files": 200, "depth": 6, "services": 30},
        }
        config = sizes.get(size, sizes["small"])
        return {
            "name": f"test_project_{size}_{int(time.time() * 1000)}",
            "size": size,
            "files": [
                {
                    "path": f"dir{i}/file{j}.yaml",
                    "content": f"apiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: test-{j}\ndata:\n  key: value{j}",
                    "hash": f"hash_{i}_{j}",
                }
                for i in range(config["depth"])
                for j in range(config["files"] // config["depth"])
            ],
            "services": [
                {
                    "name": f"service-{i}",
                    "image": f"nginx:{i}.0",
                    "ports": [80, 443],
                }
                for i in range(config["services"])
            ],
            "config": {
                "stages": ["lint", "schema", "dependency", "sbom", "sign", "admission", "runtime"],
                "severity": "strict",
            },
        }
@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """Global test configuration"""
    return {
        "redis_host": os.getenv("TEST_REDIS_HOST", "localhost"),
        "redis_port": int(os.getenv("TEST_REDIS_PORT", "6379")),
        "redis_db": int(os.getenv("TEST_REDIS_DB", "15")),
        "test_data_dir": Path(__file__).parent / "data",
        "output_dir": Path(__file__).parent / "output",
        "log_dir": Path(__file__).parent / "output" / "logs",
        "report_dir": Path(__file__).parent / "output" / "reports",
        "performance_baseline": {
            "memory_ops_per_second": 1000,
            "config_reload_latency_ms": 100,
            "report_generation_small_s": 5,
            "report_generation_medium_s": 15,
        },
    }
@pytest.fixture(scope="session")
def test_environment(test_config: Dict[str, Any]):
    """Setup test environment"""
    # Create necessary directories
    test_config["test_data_dir"].mkdir(parents=True, exist_ok=True)
    test_config["output_dir"].mkdir(parents=True, exist_ok=True)
    test_config["log_dir"].mkdir(parents=True, exist_ok=True)
    test_config["report_dir"].mkdir(parents=True, exist_ok=True)
    # Create subdirectories for test data
    (test_config["test_data_dir"] / "memories").mkdir(exist_ok=True)
    (test_config["test_data_dir"] / "configurations").mkdir(exist_ok=True)
    (test_config["test_data_dir"] / "reports").mkdir(exist_ok=True)
    (test_config["test_data_dir"] / "supply_chain").mkdir(exist_ok=True)
    yield test_config
    # Cleanup
    try:
        shutil.rmtree(test_config["output_dir"])
    except Exception as e:
        print(f"Warning: Failed to cleanup output directory: {e}")
@pytest.fixture(scope="function")
def redis_client(test_config: Dict[str, Any]):
    """Redis client for testing"""
    client = None
    try:
        client = redis.Redis(
            host=test_config["redis_host"],
            port=test_config["redis_port"],
            db=test_config["redis_db"],
            decode_responses=True,
        )
        # Test connection
        client.ping()
        yield client
    except redis.ConnectionError as e:
        pytest.skip(f"Redis connection failed: {e}")
    finally:
        if client:
            # Clean up test data
            try:
                client.flushdb()
            except Exception:
                pass
@pytest.fixture(scope="function")
def test_data(test_config: Dict[str, Any]):
    """Fresh test data for each test"""
    factory = TestDataFactory()
    data = {
        "memories": factory.create_memory(10),
        "configuration": factory.create_configuration(),
        "report_data": factory.create_report_data(),
        "supply_chain_small": factory.create_supply_chain_project("small"),
        "supply_chain_medium": factory.create_supply_chain_project("medium"),
        "supply_chain_large": factory.create_supply_chain_project("large"),
    }
    yield data
    # Cleanup will be handled by individual tests or redis_client fixture
@pytest.fixture(scope="function")
def performance_metrics():
    """Collect performance metrics during test"""
    metrics = {
        "start_time": None,
        "end_time": None,
        "duration_ms": None,
        "operations": 0,
        "errors": 0,
        "memory_usage_mb": None,
    }
    class MetricsCollector:
        def start(self):
            metrics["start_time"] = time.time()
        def stop(self):
            metrics["end_time"] = time.time()
            metrics["duration_ms"] = (metrics["end_time"] - metrics["start_time"]) * 1000
        def record_operation(self):
            metrics["operations"] += 1
        def record_error(self):
            metrics["errors"] += 1
        def get_metrics(self):
            if metrics["start_time"] and metrics["end_time"]:
                metrics["duration_ms"] = (metrics["end_time"] - metrics["start_time"]) * 1000
            return metrics
    collector = MetricsCollector()
    yield collector
    # Log metrics
    final_metrics = collector.get_metrics()
    if final_metrics["duration_ms"]:
        print(f"\n[PERFORMANCE] Duration: {final_metrics['duration_ms']:.2f}ms, "
              f"Operations: {final_metrics['operations']}, "
              f"Errors: {final_metrics['errors']}")
@pytest.fixture(scope="session")
def performance_baseline(test_config: Dict[str, Any]):
    """Performance baseline for comparison"""
    return test_config["performance_baseline"]
# Test markers configuration
def pytest_configure(config):
    """Configure custom markers"""
    config.addinivalue_line("markers", "smoke: 快速驗證測試 (quick verification tests)")
    config.addinivalue_line("markers", "functional: 功能測試 (functional tests)")
    config.addinivalue_line("markers", "performance: 性能測試 (performance tests)")
    config.addinivalue_line("markers", "security: 安全測試 (security tests)")
    config.addinivalue_line("markers", "reliability: 可靠性測試 (reliability tests)")
    config.addinivalue_line("markers", "user_journey: 用戶旅程測試 (user journey tests)")
    config.addinivalue_line("markers", "slow: 慢速測試 (slow tests)")
    config.addinivalue_line("markers", "integration: 整合測試 (integration tests)")