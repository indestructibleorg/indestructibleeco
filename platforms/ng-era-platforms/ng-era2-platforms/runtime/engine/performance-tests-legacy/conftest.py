#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: conftest
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
"""
Configuration and fixtures for performance tests
"""
import pytest
import os
import sys
import time
import psutil
import statistics
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
# Environment configuration
os.environ["TEST_MODE"] = "true"
os.environ["LOG_LEVEL"] = "INFO"
class PerformanceMetrics:
    """Performance metrics collector"""
    def __init__(self):
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.operations: int = 0
        self.errors: int = 0
        self.latencies: List[float] = []
        self.cpu_samples: List[float] = []
        self.memory_samples: List[float] = []
        self.process = psutil.Process()
    def start(self):
        """Start metrics collection"""
        self.start_time = time.time()
        self.operations = 0
        self.errors = 0
        self.latencies.clear()
        self.cpu_samples.clear()
        self.memory_samples.clear()
    def stop(self):
        """Stop metrics collection"""
        self.end_time = time.time()
    def record_operation(self, latency: Optional[float] = None):
        """Record an operation"""
        self.operations += 1
        if latency:
            self.latencies.append(latency)
        self.record_sample()
    def record_error(self):
        """Record an error"""
        self.errors += 1
    def record_sample(self):
        """Record a sample of system metrics"""
        try:
            self.cpu_samples.append(self.process.cpu_percent())
            self.memory_samples.append(self.process.memory_info().rss / 1024 / 1024)  # MB
        except Exception:
            pass
    def get_throughput(self) -> float:
        """Calculate throughput (operations/second)"""
        if not self.start_time or not self.end_time:
            return 0.0
        duration = self.end_time - self.start_time
        if duration == 0:
            return 0.0
        return self.operations / duration
    def get_latency_stats(self) -> Dict[str, float]:
        """Calculate latency statistics"""
        if not self.latencies:
            return {
                "min": 0.0,
                "max": 0.0,
                "avg": 0.0,
                "p50": 0.0,
                "p95": 0.0,
                "p99": 0.0,
            }
        sorted_latencies = sorted(self.latencies)
        return {
            "min": min(sorted_latencies),
            "max": max(sorted_latencies),
            "avg": statistics.mean(sorted_latencies),
            "p50": sorted_latencies[int(len(sorted_latencies) * 0.5)],
            "p95": sorted_latencies[int(len(sorted_latencies) * 0.95)],
            "p99": sorted_latencies[int(len(sorted_latencies) * 0.99)],
        }
    def get_cpu_stats(self) -> Dict[str, float]:
        """Calculate CPU statistics"""
        if not self.cpu_samples:
            return {"avg": 0.0, "max": 0.0}
        return {
            "avg": statistics.mean(self.cpu_samples),
            "max": max(self.cpu_samples),
        }
    def get_memory_stats(self) -> Dict[str, float]:
        """Calculate memory statistics"""
        if not self.memory_samples:
            return {"avg": 0.0, "max": 0.0}
        return {
            "avg": statistics.mean(self.memory_samples),
            "max": max(self.memory_samples),
        }
    def get_summary(self) -> Dict[str, Any]:
        """Get complete metrics summary"""
        return {
            "duration": self.end_time - self.start_time if self.start_time and self.end_time else 0,
            "operations": self.operations,
            "errors": self.errors,
            "error_rate": self.errors / self.operations if self.operations > 0 else 0,
            "throughput": self.get_throughput(),
            "latency": self.get_latency_stats(),
            "cpu": self.get_cpu_stats(),
            "memory_mb": self.get_memory_stats(),
        }
    def compare_with_baseline(self, baseline: Dict[str, Any]) -> Dict[str, Any]:
        """Compare metrics with baseline"""
        current = self.get_summary()
        comparison = {}
        # Compare throughput
        if baseline.get("throughput"):
            throughput_diff = current["throughput"] - baseline["throughput"]
            comparison["throughput"] = {
                "current": current["throughput"],
                "baseline": baseline["throughput"],
                "diff": throughput_diff,
                "percent": (throughput_diff / baseline["throughput"]) * 100 if baseline["throughput"] > 0 else 0,
            }
        # Compare latencies
        if baseline.get("latency"):
            for percentile in ["p50", "p95", "p99"]:
                if baseline["latency"].get(percentile):
                    current_latency = current["latency"][percentile]
                    baseline_latency = baseline["latency"][percentile]
                    latency_diff = current_latency - baseline_latency
                    comparison[f"latency_{percentile}"] = {
                        "current": current_latency,
                        "baseline": baseline_latency,
                        "diff": latency_diff,
                        "percent": (latency_diff / baseline_latency) * 100 if baseline_latency > 0 else 0,
                    }
        return comparison
@pytest.fixture(scope="session")
def performance_config() -> Dict[str, Any]:
    """Global performance configuration"""
    return {
        "memory": {
            "add_operations": 10000,
            "get_operations": 20000,
            "delete_operations": 15000,
            "search_operations": 1000,
            "batch_size": 100,
        },
        "cache": {
            "hit_rate_target": 0.9,
            "miss_rate_target": 0.1,
        },
        "concurrency": {
            "users": [10, 50, 100],
            "duration": 60,  # seconds
        },
        "load": {
            "target_load": 1000,
            "ramp_up_time": 30,  # seconds
            "duration": 300,  # seconds
        },
        "baselines": {
            "memory_add": {
                "throughput": 10000,
                "latency": {
                    "p50": 0.001,
                    "p95": 0.005,
                    "p99": 0.010,
                },
            },
            "memory_get": {
                "throughput": 20000,
                "latency": {
                    "p50": 0.0005,
                    "p95": 0.002,
                    "p99": 0.005,
                },
            },
            "config_reload": {
                "throughput": 10,
                "latency": {
                    "p50": 0.1,
                    "p95": 0.5,
                    "p99": 1.0,
                },
            },
            "report_generation": {
                "throughput": 10,
                "latency": {
                    "p50": 5,
                    "p95": 8,
                    "p99": 10,
                },
            },
        },
    }
@pytest.fixture(scope="function")
def performance_metrics():
    """Performance metrics collector for each test"""
    metrics = PerformanceMetrics()
    yield metrics
    # Print summary
    summary = metrics.get_summary()
    if summary["operations"] > 0:
        print(f"\n{'='*60}")
        print(f"PERFORMANCE METRICS SUMMARY")
        print(f"{'='*60}")
        print(f"Duration: {summary['duration']:.2f}s")
        print(f"Operations: {summary['operations']}")
        print(f"Errors: {summary['errors']}")
        print(f"Error Rate: {summary['error_rate']*100:.2f}%")
        print(f"Throughput: {summary['throughput']:.2f} ops/sec")
        print(f"\nLatency:")
        for key, value in summary['latency'].items():
            print(f"  {key}: {value*1000:.2f}ms" if key != 'avg' else f"  {key}: {value*1000:.2f}ms")
        print(f"\nCPU Usage:")
        print(f"  Avg: {summary['cpu']['avg']:.2f}%")
        print(f"  Max: {summary['cpu']['max']:.2f}%")
        print(f"\nMemory Usage:")
        print(f"  Avg: {summary['memory_mb']['avg']:.2f}MB")
        print(f"  Max: {summary['memory_mb']['max']:.2f}MB")
        print(f"{'='*60}\n")
@pytest.fixture(scope="function")
def warmup():
    """Warmup fixture - run warmup iterations before test"""
    def run_warmup(iterations: int = 10):
        """Run warmup iterations"""
        for _ in range(iterations):
            # Perform dummy operations
            pass
        time.sleep(0.1)
    return run_warmup
@pytest.fixture(scope="session")
def test_environment(test_config):
    """Setup performance test environment"""
    # Create output directories
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "benchmarks").mkdir(exist_ok=True)
    (output_dir / "profiles").mkdir(exist_ok=True)
    (output_dir / "reports").mkdir(exist_ok=True)
    yield test_config
# Test markers configuration
def pytest_configure(config):
    """Configure custom markers"""
    config.addinivalue_line("markers", "performance: 性能測試 (performance tests)")
    config.addinivalue_line("markers", "unit_performance: 單元性能測試 (unit performance tests)")
    config.addinivalue_line("markers", "component_performance: 組件性能測試 (component performance tests)")
    config.addinivalue_line("markers", "system_performance: 系統性能測試 (system performance tests)")
    config.addinivalue_line("markers", "stress: 壓力測試 (stress tests)")
    config.addinivalue_line("markers", "endurance: 耐久測試 (endurance tests)")
    config.addinivalue_line("markers", "benchmark: 基準測試 (benchmark tests)")
def pytest_generate_tests(metafunc):
    """Parametrize performance tests"""
    if "concurrent_users" in metafunc.fixturenames:
        metafunc.parametrize("concurrent_users", [10, 50, 100])
    if "load_level" in metafunc.fixturenames:
        metafunc.parametrize("load_level", [0.5, 0.8, 1.0])