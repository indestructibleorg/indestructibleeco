#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: test_unit_memory_operations
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
"""
Unit Performance Tests - Memory Operations
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
class TestMemoryAddPerformance:
    """Test memory add operation performance"""
    @pytest.fixture(scope="class")
    def memory_manager(self, test_config):
        """Create Memory Manager instance"""
        try:
            from ns_root.namespaces_adk.adk.plugins.memory_plugins import MemoryManager
            manager = MemoryManager(
                backend_type="redis",
                config={
                    "host": test_config["redis_host"],
                    "port": test_config["redis_port"],
                    "db": test_config["redis_db"],
                },
            )
            manager.initialize()
            yield manager
            try:
                manager.close()
            except Exception:
                pass
        except ImportError as e:
            pytest.skip(f"MemoryManager not importable: {e}")
    def test_single_add_performance(self, memory_manager, performance_metrics, warmup):
        """Test single memory add performance"""
        # Warmup
        warmup(10)
        # Start metrics
        performance_metrics.start()
        # Add memories
        iterations = 1000
        for i in range(iterations):
            start = time.perf_counter()
            try:
                memory_id = f"perf_test_{int(time.time() * 1000)}_{i}"
                memory_manager.add_memory(memory_id, f"Test content {i}", {"test": "performance"})
                latency = time.perf_counter() - start
                performance_metrics.record_operation(latency)
            except Exception as e:
                performance_metrics.record_error()
        performance_metrics.stop()
        # Verify performance
        summary = performance_metrics.get_summary()
        assert summary["throughput"] > 100, f"Throughput too low: {summary['throughput']} ops/sec"
        assert summary["latency"]["p99"] < 0.1, f"P99 latency too high: {summary['latency']['p99']}s"
    def test_batch_add_performance(self, memory_manager, performance_metrics, performance_config):
        """Test batch memory add performance"""
        batch_size = performance_config["memory"]["batch_size"]
        # Warmup
        for _ in range(10):
            for i in range(10):
                memory_id = f"warmup_{i}"
                memory_manager.add_memory(memory_id, f"Warmup {i}", {})
        # Start metrics
        performance_metrics.start()
        # Add batches
        num_batches = 10
        for batch in range(num_batches):
            start = time.perf_counter()
            try:
                for i in range(batch_size):
                    memory_id = f"batch_test_{batch}_{i}"
                    memory_manager.add_memory(memory_id, f"Batch content {i}", {"batch": batch})
                latency = time.perf_counter() - start
                performance_metrics.record_operation(latency)
            except Exception as e:
                performance_metrics.record_error()
        performance_metrics.stop()
        # Verify performance
        summary = performance_metrics.get_summary()
        assert summary["operations"] == num_batches, f"Expected {num_batches} batches, got {summary['operations']}"
    def test_concurrent_add_performance(self, memory_manager, performance_metrics, concurrent_users):
        """Test concurrent memory add performance"""
        import threading
        # Warmup
        for _ in range(10):
            memory_manager.add_memory(f"warmup_{_}", "Warmup", {})
        # Start metrics
        performance_metrics.start()
        # Add memories concurrently
        def add_memories(user_id: int):
            for i in range(10):
                start = time.perf_counter()
                try:
                    memory_id = f"concurrent_test_{user_id}_{i}"
                    memory_manager.add_memory(memory_id, f"Concurrent content {user_id}_{i}", {"user": user_id})
                    latency = time.perf_counter() - start
                    performance_metrics.record_operation(latency)
                except Exception as e:
                    performance_metrics.record_error()
        threads = []
        for user_id in range(concurrent_users):
            thread = threading.Thread(target=add_memories, args=(user_id,))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()
        performance_metrics.stop()
        # Verify performance
        summary = performance_metrics.get_summary()
        assert summary["operations"] == concurrent_users * 10, f"Expected {concurrent_users * 10} operations"
@pytest.mark.performance
@pytest.mark.unit_performance
class TestMemoryGetPerformance:
    """Test memory get operation performance"""
    @pytest.fixture(scope="class")
    def memory_manager(self, test_config):
        """Create Memory Manager instance"""
        try:
            from ns_root.namespaces_adk.adk.plugins.memory_plugins import MemoryManager
            manager = MemoryManager(
                backend_type="redis",
                config={
                    "host": test_config["redis_host"],
                    "port": test_config["redis_port"],
                    "db": test_config["redis_db"],
                },
            )
            manager.initialize()
            # Pre-populate with test data
            for i in range(1000):
                memory_id = f"get_test_{i}"
                manager.add_memory(memory_id, f"Test content {i}", {"test": "get"})
            yield manager
            try:
                manager.close()
            except Exception:
                pass
        except ImportError as e:
            pytest.skip(f"MemoryManager not importable: {e}")
    def test_single_get_performance(self, memory_manager, performance_metrics, warmup):
        """Test single memory get performance"""
        # Warmup
        for i in range(10):
            memory_manager.get_memory(f"get_test_{i}")
        # Start metrics
        performance_metrics.start()
        # Get memories
        iterations = 1000
        for i in range(iterations):
            start = time.perf_counter()
            try:
                memory = memory_manager.get_memory(f"get_test_{i % 1000}")
                latency = time.perf_counter() - start
                performance_metrics.record_operation(latency)
                if not memory:
                    performance_metrics.record_error()
            except Exception as e:
                performance_metrics.record_error()
        performance_metrics.stop()
        # Verify performance
        summary = performance_metrics.get_summary()
        assert summary["throughput"] > 1000, f"Throughput too low: {summary['throughput']} ops/sec"
        assert summary["latency"]["p99"] < 0.01, f"P99 latency too high: {summary['latency']['p99']}s"
    def test_batch_get_performance(self, memory_manager, performance_metrics):
        """Test batch memory get performance"""
        batch_size = 100
        # Warmup
        for i in range(10):
            for j in range(10):
                memory_manager.get_memory(f"get_test_{j}")
        # Start metrics
        performance_metrics.start()
        # Get batches
        num_batches = 10
        for batch in range(num_batches):
            start = time.perf_counter()
            try:
                for i in range(batch_size):
                    memory = memory_manager.get_memory(f"get_test_{(batch * batch_size + i) % 1000}")
                    if not memory:
                        performance_metrics.record_error()
                latency = time.perf_counter() - start
                performance_metrics.record_operation(latency)
            except Exception as e:
                performance_metrics.record_error()
        performance_metrics.stop()
        # Verify performance
        summary = performance_metrics.get_summary()
        assert summary["operations"] == num_batches
@pytest.mark.performance
@pytest.mark.unit_performance
class TestMemorySearchPerformance:
    """Test memory search operation performance"""
    @pytest.fixture(scope="class")
    def memory_manager(self, test_config):
        """Create Memory Manager instance"""
        try:
            from ns_root.namespaces_adk.adk.plugins.memory_plugins import MemoryManager
            manager = MemoryManager(
                backend_type="redis",
                config={
                    "host": test_config["redis_host"],
                    "port": test_config["redis_port"],
                    "db": test_config["redis_db"],
                },
            )
            manager.initialize()
            # Pre-populate with test data
            test_data = [
                "machine learning algorithms optimize data processing",
                "distributed systems enable scalable applications",
                "cloud computing provides flexible infrastructure",
                "security protocols protect sensitive information",
                "database management ensures data integrity",
                "network protocols enable communication",
                "software engineering best practices",
                "system architecture design principles",
                "data science and analytics",
                "artificial intelligence and automation",
            ]
            for i in range(100):
                for j, content in enumerate(test_data):
                    memory_id = f"search_test_{i}_{j}"
                    manager.add_memory(memory_id, f"{content} version {i}", {"category": j})
            yield manager
            try:
                manager.close()
            except Exception:
                pass
        except ImportError as e:
            pytest.skip(f"MemoryManager not importable: {e}")
    def test_search_performance(self, memory_manager, performance_metrics):
        """Test memory search performance"""
        queries = [
            "machine learning",
            "distributed systems",
            "cloud computing",
            "security",
            "database",
        ]
        # Start metrics
        performance_metrics.start()
        # Search memories
        iterations = 100
        for i in range(iterations):
            query = queries[i % len(queries)]
            start = time.perf_counter()
            try:
                results = memory_manager.search_memories(query=query, limit=10)
                latency = time.perf_counter() - start
                performance_metrics.record_operation(latency)
                if not results:
                    performance_metrics.record_error()
            except Exception as e:
                performance_metrics.record_error()
        performance_metrics.stop()
        # Verify performance
        summary = performance_metrics.get_summary()
        assert summary["operations"] == iterations
@pytest.mark.performance
@pytest.mark.unit_performance
class TestMemoryDeletePerformance:
    """Test memory delete operation performance"""
    @pytest.fixture(scope="class")
    def memory_manager(self, test_config):
        """Create Memory Manager instance"""
        try:
            from ns_root.namespaces_adk.adk.plugins.memory_plugins import MemoryManager
            manager = MemoryManager(
                backend_type="redis",
                config={
                    "host": test_config["redis_host"],
                    "port": test_config["redis_port"],
                    "db": test_config["redis_db"],
                },
            )
            manager.initialize()
            yield manager
            try:
                manager.close()
            except Exception:
                pass
        except ImportError as e:
            pytest.skip(f"MemoryManager not importable: {e}")
    def test_single_delete_performance(self, memory_manager, performance_metrics):
        """Test single memory delete performance"""
        # Pre-populate with test data
        memory_ids = []
        for i in range(1000):
            memory_id = f"delete_test_{i}"
            memory_manager.add_memory(memory_id, f"Test content {i}", {})
            memory_ids.append(memory_id)
        # Start metrics
        performance_metrics.start()
        # Delete memories
        for memory_id in memory_ids:
            start = time.perf_counter()
            try:
                memory_manager.delete_memory(memory_id)
                latency = time.perf_counter() - start
                performance_metrics.record_operation(latency)
            except Exception as e:
                performance_metrics.record_error()
        performance_metrics.stop()
        # Verify performance
        summary = performance_metrics.get_summary()
        assert summary["throughput"] > 500, f"Throughput too low: {summary['throughput']} ops/sec"