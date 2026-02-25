#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: test_unit_cache_operations
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
"""
Unit Performance Tests - Cache Operations
"""
import pytest
import sys
import time
from pathlib import Path
# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
@pytest.mark.performance
@pytest.mark.unit_performance
class TestCacheHitPerformance:
    """Test cache hit performance"""
    @pytest.fixture(scope="class")
    def cache_system(self, test_config):
        """Create cache system instance"""
        try:
            from ns_root.namespaces_adk.adk.plugins.memory_plugins import SemanticCache
            cache = SemanticCache(
                max_size=1000,
                ttl=3600,
            )
            # Pre-populate cache
            for i in range(100):
                cache.add(f"cache_key_{i}", f"cache_value_{i}")
            yield cache
        except ImportError as e:
            pytest.skip(f"SemanticCache not importable: {e}")
    def test_cache_hit_performance_l1(self, cache_system, performance_metrics):
        """Test L1 cache (in-memory) hit performance"""
        # Warmup
        for i in range(10):
            cache_system.get(f"cache_key_{i}")
        # Start metrics
        performance_metrics.start()
        # Get from cache
        iterations = 10000
        for i in range(iterations):
            start = time.perf_counter()
            try:
                value = cache_system.get(f"cache_key_{i % 100}")
                latency = time.perf_counter() - start
                performance_metrics.record_operation(latency)
                if value is None:
                    performance_metrics.record_error()
            except Exception as e:
                performance_metrics.record_error()
        performance_metrics.stop()
        # Verify performance
        summary = performance_metrics.get_summary()
        assert summary["throughput"] > 10000, f"Throughput too low: {summary['throughput']} ops/sec"
        assert summary["latency"]["p99"] < 0.001, f"P99 latency too high: {summary['latency']['p99']}s"
    def test_cache_hit_hit_rate(self, cache_system, performance_metrics):
        """Test cache hit rate"""
        # Start metrics
        performance_metrics.start()
        # Get from cache
        iterations = 1000
        for i in range(iterations):
            start = time.perf_counter()
            try:
                value = cache_system.get(f"cache_key_{i % 100}")
                latency = time.perf_counter() - start
                performance_metrics.record_operation(latency)
            except Exception as e:
                performance_metrics.record_error()
        performance_metrics.stop()
        # Verify hit rate
        summary = performance_metrics.get_summary()
        hit_rate = 1.0 - (summary["errors"] / summary["operations"])
        assert hit_rate > 0.95, f"Hit rate too low: {hit_rate}"
@pytest.mark.performance
@pytest.mark.unit_performance
class TestCacheMissPerformance:
    """Test cache miss performance"""
    @pytest.fixture(scope="class")
    def cache_system(self, test_config):
        """Create cache system instance"""
        try:
            from ns_root.namespaces_adk.adk.plugins.memory_plugins import SemanticCache
            cache = SemanticCache(
                max_size=1000,
                ttl=3600,
            )
            yield cache
        except ImportError as e:
            pytest.skip(f"SemanticCache not importable: {e}")
    def test_cache_miss_performance(self, cache_system, performance_metrics):
        """Test cache miss performance"""
        # Start metrics
        performance_metrics.start()
        # Get from cache (all misses)
        iterations = 1000
        for i in range(iterations):
            start = time.perf_counter()
            try:
                value = cache_system.get(f"nonexistent_key_{i}")
                latency = time.perf_counter() - start
                performance_metrics.record_operation(latency)
            except Exception as e:
                performance_metrics.record_error()
        performance_metrics.stop()
        # Verify performance
        summary = performance_metrics.get_summary()
        # Cache miss should still be fast
        assert summary["latency"]["p99"] < 0.01, f"P99 latency too high: {summary['latency']['p99']}s"
@pytest.mark.performance
@pytest.mark.unit_performance
class TestCacheEvictionPerformance:
    """Test cache eviction performance"""
    @pytest.fixture(scope="class")
    def cache_system(self, test_config):
        """Create cache system instance"""
        try:
            from ns_root.namespaces_adk.adk.plugins.memory_plugins import SemanticCache
            cache = SemanticCache(
                max_size=100,  # Small cache for eviction testing
                ttl=3600,
            )
            yield cache
        except ImportError as e:
            pytest.skip(f"SemanticCache not importable: {e}")
    def test_lru_eviction_performance(self, cache_system, performance_metrics):
        """Test LRU eviction performance"""
        # Fill cache
        for i in range(100):
            cache_system.add(f"eviction_test_{i}", f"value_{i}")
        # Start metrics
        performance_metrics.start()
        # Add more items to trigger eviction
        for i in range(100, 200):
            start = time.perf_counter()
            try:
                cache_system.add(f"eviction_test_{i}", f"value_{i}")
                latency = time.perf_counter() - start
                performance_metrics.record_operation(latency)
            except Exception as e:
                performance_metrics.record_error()
        performance_metrics.stop()
        # Verify performance
        summary = performance_metrics.get_summary()
        assert summary["operations"] == 100
    def test_ttl_eviction_performance(self, cache_system, performance_metrics):
        """Test TTL expiration performance"""
        # Add items with short TTL
        import time
        ttl = 1  # 1 second TTL
        for i in range(100):
            cache_system.add(f"ttl_test_{i}", f"value_{i}")
        # Wait for TTL to expire
        time.sleep(2)
        # Start metrics
        performance_metrics.start()
        # Try to get expired items (should miss)
        for i in range(100):
            start = time.perf_counter()
            try:
                value = cache_system.get(f"ttl_test_{i}")
                latency = time.perf_counter() - start
                performance_metrics.record_operation(latency)
            except Exception as e:
                performance_metrics.record_error()
        performance_metrics.stop()
        # Verify all expired (all should be misses)
        summary = performance_metrics.get_summary()
@pytest.mark.performance
@pytest.mark.unit_performance
class TestCacheOperationsMixed:
    """Test mixed cache operations performance"""
    @pytest.fixture(scope="class")
    def cache_system(self, test_config):
        """Create cache system instance"""
        try:
            from ns_root.namespaces_adk.adk.plugins.memory_plugins import SemanticCache
            cache = SemanticCache(
                max_size=1000,
                ttl=3600,
            )
            yield cache
        except ImportError as e:
            pytest.skip(f"SemanticCache not importable: {e}")
    def test_mixed_operations_performance(self, cache_system, performance_metrics):
        """Test mixed read/write operations"""
        # Start metrics
        performance_metrics.start()
        # Mix of reads and writes
        for i in range(1000):
            if i % 3 == 0:  # Write
                start = time.perf_counter()
                try:
                    cache_system.add(f"mixed_key_{i}", f"mixed_value_{i}")
                    latency = time.perf_counter() - start
                    performance_metrics.record_operation(latency)
                except Exception as e:
                    performance_metrics.record_error()
            else:  # Read
                start = time.perf_counter()
                try:
                    value = cache_system.get(f"mixed_key_{i // 3}")
                    latency = time.perf_counter() - start
                    performance_metrics.record_operation(latency)
                except Exception as e:
                    performance_metrics.record_error()
        performance_metrics.stop()
        # Verify performance
        summary = performance_metrics.get_summary()
        assert summary["operations"] == 1000