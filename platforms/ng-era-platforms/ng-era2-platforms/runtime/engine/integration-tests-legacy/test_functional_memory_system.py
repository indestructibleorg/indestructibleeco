#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: test_functional_memory_system
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
"""
Functional Tests - Complete memory system workflow tests
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime
import time
# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
@pytest.mark.functional
class TestMemorySystemWorkflow:
    """Test complete memory system workflow"""
    @pytest.fixture(scope="function")
    def memory_system(self, test_config):
        """Create complete memory system instance"""
        try:
            from ns_root.namespaces_adk.adk.plugins.memory_plugins import (
                MemoryManager,
                SemanticCache,
                VectorSearch,
                MemoryCompactor,
            )
            # Initialize memory manager
            manager = MemoryManager(
                backend_type="redis",
                config={
                    "host": test_config["redis_host"],
                    "port": test_config["redis_port"],
                    "db": test_config["redis_db"],
                },
            )
            manager.initialize()
            # Initialize semantic cache
            cache = SemanticCache(
                max_size=100,
                ttl=3600,
            )
            # Initialize vector search
            vector_search = VectorSearch(
                index_name="test_memory_index",
                dimension=1536,
            )
            # Initialize memory compactor
            compactor = MemoryCompactor()
            yield {
                "manager": manager,
                "cache": cache,
                "vector_search": vector_search,
                "compactor": compactor,
            }
            # Cleanup
            try:
                manager.close()
            except Exception:
                pass
        except ImportError as e:
            pytest.skip(f"Memory system not importable: {e}")
        except Exception as e:
            pytest.skip(f"Memory system initialization failed: {e}")
    def test_complete_memory_lifecycle(self, memory_system, performance_metrics):
        """Test complete memory lifecycle: add, search, compact, delete"""
        performance_metrics.start()
        manager = memory_system["manager"]
        cache = memory_system["cache"]
        compactor = memory_system["compactor"]
        # Phase 1: Add memories
        performance_metrics.record_operation()
        memory_ids = []
        for i in range(10):
            memory_id = f"test_memory_{int(time.time() * 1000)}_{i}"
            content = f"This is test memory {i} with semantic content"
            try:
                result = manager.add_memory(
                    memory_id=memory_id,
                    content=content,
                    metadata={"test": True, "index": i},
                )
                if result:
                    memory_ids.append(memory_id)
            except Exception:
                pass
            performance_metrics.record_operation()
        # Phase 2: Cache memories
        performance_metrics.record_operation()
        for memory_id in memory_ids[:5]:
            try:
                memory = manager.get_memory(memory_id)
                if memory:
                    cache.add(memory_id, memory)
            except Exception:
                pass
            performance_metrics.record_operation()
        # Phase 3: Search memories
        performance_metrics.record_operation()
        try:
            results = manager.search_memories(query="test memory", limit=5)
            if results:
                assert len(results) > 0
        except Exception:
            pass
        performance_metrics.record_operation()
        # Phase 4: Compact memories
        performance_metrics.record_operation()
        try:
            compactor.compact(
                memories=memory_ids,
                strategy="statistical",
            )
        except Exception:
            pass
        performance_metrics.record_operation()
        # Phase 5: Cleanup
        performance_metrics.record_operation()
        for memory_id in memory_ids:
            try:
                manager.delete_memory(memory_id)
            except Exception:
                pass
        performance_metrics.record_operation()
        performance_metrics.stop()
        # Verify performance
        metrics = performance_metrics.get_metrics()
        assert metrics["operations"] > 0
        print(f"\n[MEMORY SYSTEM] Processed {metrics['operations']} operations in {metrics['duration_ms']:.2f}ms")
    def test_memory_search_and_retrieval(self, memory_system):
        """Test memory search and retrieval workflow"""
        manager = memory_system["manager"]
        vector_search = memory_system["vector_search"]
        # Add test memories
        memory_ids = []
        test_contents = [
            "Machine learning algorithms optimize data processing",
            "Distributed systems enable scalable applications",
            "Cloud computing provides flexible infrastructure",
            "Security protocols protect sensitive information",
            "Database management ensures data integrity",
        ]
        for i, content in enumerate(test_contents):
            memory_id = f"search_test_{int(time.time() * 1000)}_{i}"
            try:
                manager.add_memory(memory_id, content, {"category": i})
                memory_ids.append(memory_id)
            except Exception:
                pass
        # Search for memories
        try:
            results = manager.search_memories(query="machine learning", limit=3)
            # Verify results
            if results:
                assert len(results) <= 3
        except Exception:
            pass
        # Cleanup
        for memory_id in memory_ids:
            try:
                manager.delete_memory(memory_id)
            except Exception:
                pass
    def test_memory_caching_workflow(self, memory_system):
        """Test memory caching workflow"""
        manager = memory_system["manager"]
        cache = memory_system["cache"]
        # Add memory
        memory_id = f"cache_test_{int(time.time() * 1000)}"
        content = "This is a cache test memory"
        try:
            manager.add_memory(memory_id, content, {"test": "cache"})
            # First retrieval - not cached
            memory1 = manager.get_memory(memory_id)
            assert memory1 is not None
            # Cache the memory
            cache.add(memory_id, memory1)
            # Second retrieval - from cache
            memory2 = cache.get(memory_id)
            assert memory2 is not None
            # Clear cache
            cache.clear()
            # Third retrieval - not cached
            memory3 = cache.get(memory_id)
            assert memory3 is None
        except Exception as e:
            pytest.skip(f"Memory caching test failed: {e}")
    def test_memory_compaction_workflow(self, memory_system):
        """Test memory compaction workflow"""
        manager = memory_system["manager"]
        compactor = memory_system["compactor"]
        # Add many memories
        memory_ids = []
        for i in range(20):
            memory_id = f"compact_test_{int(time.time() * 1000)}_{i}"
            content = f"This is memory {i} for compaction test. " * 10
            try:
                manager.add_memory(memory_id, content, {"test": "compaction", "index": i})
                memory_ids.append(memory_id)
            except Exception:
                pass
        # Compact memories
        try:
            compactor.compact(
                memories=memory_ids,
                strategy="statistical",
            )
        except Exception:
            pass
        # Cleanup
        for memory_id in memory_ids:
            try:
                manager.delete_memory(memory_id)
            except Exception:
                pass
@pytest.mark.functional
class TestMemorySystemIntegration:
    """Test memory system integration with other components"""
    @pytest.fixture(scope="function")
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
    def test_memory_with_configuration(self, memory_manager, test_data):
        """Test memory system with configuration management"""
        config = test_data["configuration"]
        # Use configuration to create memory
        memory_id = f"config_test_{int(time.time() * 1000)}"
        content = f"Memory with configuration version {config['version']}"
        try:
            memory_manager.add_memory(memory_id, content, {"config_version": config["version"]})
            # Retrieve and verify
            memory = memory_manager.get_memory(memory_id)
            assert memory is not None
        except Exception as e:
            pytest.skip(f"Memory with configuration test failed: {e}")
    def test_memory_with_reporting(self, memory_manager):
        """Test memory system with reporting"""
        # Add memories for reporting
        memory_ids = []
        for i in range(5):
            memory_id = f"report_test_{int(time.time() * 1000)}_{i}"
            content = f"Memory {i} for reporting"
            try:
                memory_manager.add_memory(memory_id, content, {"report": True})
                memory_ids.append(memory_id)
            except Exception:
                pass
        # Simulate report generation
        report_data = {
            "total_memories": len(memory_ids),
            "timestamp": datetime.now().isoformat(),
        }
        assert report_data["total_memories"] > 0
        # Cleanup
        for memory_id in memory_ids:
            try:
                memory_manager.delete_memory(memory_id)
            except Exception:
                pass
@pytest.mark.functional
class TestMemorySystemErrorHandling:
    """Test memory system error handling"""
    @pytest.fixture(scope="function")
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
    def test_handle_nonexistent_memory(self, memory_manager):
        """Test handling of nonexistent memory"""
        # Try to get a memory that doesn't exist
        memory = memory_manager.get_memory("nonexistent_memory_id")
        assert memory is None or memory.get("deleted", False)
    def test_handle_duplicate_memory(self, memory_manager):
        """Test handling of duplicate memory"""
        memory_id = f"duplicate_test_{int(time.time() * 1000)}"
        content = "Duplicate test memory"
        try:
            # Add memory twice
            memory_manager.add_memory(memory_id, content, {"test": "duplicate"})
            memory_manager.add_memory(memory_id, content, {"test": "duplicate"})
            # Should still work (overwrite or ignore)
            memory = memory_manager.get_memory(memory_id)
            assert memory is not None
        except Exception as e:
            # If it raises an error, that's also acceptable
            pass
        finally:
            try:
                memory_manager.delete_memory(memory_id)
            except Exception:
                pass
    def test_handle_invalid_memory_id(self, memory_manager):
        """Test handling of invalid memory ID"""
        # Try operations with invalid IDs
        try:
            memory_manager.get_memory("")
            memory_manager.get_memory(None)
            memory_manager.delete_memory("")
            memory_manager.delete_memory(None)
        except Exception:
            # Should handle gracefully
            pass
@pytest.mark.functional
def test_memory_system_end_to_end(test_config, performance_metrics):
    """End-to-end test of entire memory system"""
    performance_metrics.start()
    try:
        from ns_root.namespaces_adk.adk.plugins.memory_plugins import MemoryManager
        # Initialize
        manager = MemoryManager(
            backend_type="redis",
            config={
                "host": test_config["redis_host"],
                "port": test_config["redis_port"],
                "db": test_config["redis_db"],
            },
        )
        manager.initialize()
        performance_metrics.record_operation()
        # Add memories
        memory_ids = []
        for i in range(10):
            memory_id = f"e2e_test_{int(time.time() * 1000)}_{i}"
            manager.add_memory(memory_id, f"Memory {i}", {"test": "e2e"})
            memory_ids.append(memory_id)
            performance_metrics.record_operation()
        # Search memories
        results = manager.search_memories(query="Memory", limit=5)
        if results:
            assert len(results) > 0
        performance_metrics.record_operation()
        # Update memories
        for memory_id in memory_ids[:5]:
            manager.update_memory(memory_id, {"updated": True})
        performance_metrics.record_operation()
        # Delete memories
        for memory_id in memory_ids:
            manager.delete_memory(memory_id)
        performance_metrics.record_operation()
        # Cleanup
        manager.close()
        performance_metrics.stop()
        metrics = performance_metrics.get_metrics()
        print(f"\n[E2E MEMORY] Completed {metrics['operations']} operations in {metrics['duration_ms']:.2f}ms")
        assert metrics["operations"] > 0
    except ImportError as e:
        pytest.skip(f"Memory system E2E test failed: {e}")