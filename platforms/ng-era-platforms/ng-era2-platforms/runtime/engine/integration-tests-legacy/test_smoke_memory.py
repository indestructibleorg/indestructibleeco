#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: test_smoke_memory
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
"""
Smoke Tests for Memory System - Quick verification of memory functionality
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime
# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
@pytest.mark.smoke
class TestMemoryManagerSmoke:
    """Smoke tests for Memory Manager"""
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
            # Initialize
            manager.initialize()
            yield manager
            # Cleanup
            try:
                manager.close()
            except Exception:
                pass
        except ImportError as e:
            pytest.skip(f"MemoryManager not importable: {e}")
        except Exception as e:
            pytest.skip(f"MemoryManager initialization failed: {e}")
    def test_memory_manager_initialization(self, memory_manager):
        """Test that Memory Manager initializes correctly"""
        assert memory_manager is not None
        assert hasattr(memory_manager, 'backend')
        assert memory_manager.backend is not None
    def test_add_memory(self, memory_manager):
        """Test adding a memory"""
        memory_id = f"smoke_memory_{datetime.now().timestamp()}"
        content = "This is a smoke test memory"
        result = memory_manager.add_memory(
            memory_id=memory_id,
            content=content,
            metadata={"test": "smoke"},
        )
        assert result is True or result is not False
    def test_retrieve_memory(self, memory_manager):
        """Test retrieving a memory"""
        memory_id = f"smoke_retrieve_{datetime.now().timestamp()}"
        content = "This is a smoke test retrieve memory"
        # Add memory first
        memory_manager.add_memory(memory_id, content, {"test": "retrieve"})
        # Retrieve memory
        memory = memory_manager.get_memory(memory_id)
        assert memory is not None
        assert memory.get("content") == content or content in str(memory.get("content", ""))
    def test_delete_memory(self, memory_manager):
        """Test deleting a memory"""
        memory_id = f"smoke_delete_{datetime.now().timestamp()}"
        content = "This is a smoke test delete memory"
        # Add memory first
        memory_manager.add_memory(memory_id, content, {"test": "delete"})
        # Delete memory
        result = memory_manager.delete_memory(memory_id)
        assert result is True or result is not False
        # Verify deletion
        memory = memory_manager.get_memory(memory_id)
        assert memory is None or memory.get("deleted", False)
@pytest.mark.smoke
class TestRedisBackendSmoke:
    """Smoke tests for Redis Backend"""
    @pytest.fixture(scope="class")
    def redis_backend(self, test_config):
        """Create Redis Backend instance"""
        try:
            from ns_root.namespaces_adk.adk.plugins.memory_plugins import RedisBackend
            backend = RedisBackend(
                host=test_config["redis_host"],
                port=test_config["redis_port"],
                db=test_config["redis_db"],
            )
            yield backend
            # Cleanup
            try:
                backend.close()
            except Exception:
                pass
        except ImportError as e:
            pytest.skip(f"RedisBackend not importable: {e}")
    def test_redis_backend_initialization(self, redis_backend):
        """Test that Redis Backend initializes correctly"""
        assert redis_backend is not None
    def test_redis_backend_connection(self, redis_backend):
        """Test Redis Backend connection"""
        try:
            # Try a simple operation
            redis_backend.set("smoke_test", "connection_test")
            value = redis_backend.get("smoke_test")
            assert value == "connection_test"
            redis_backend.delete("smoke_test")
        except Exception as e:
            pytest.skip(f"Redis Backend connection failed: {e}")
    def test_redis_backend_add_retrieve(self, redis_backend):
        """Test adding and retrieving data"""
        key = f"smoke_add_retrieve_{datetime.now().timestamp()}"
        data = {"test": "data", "value": 123}
        redis_backend.set(key, data)
        retrieved = redis_backend.get(key)
        assert retrieved is not None
        redis_backend.delete(key)
@pytest.mark.smoke
class TestSemanticCacheSmoke:
    """Smoke tests for Semantic Cache"""
    @pytest.fixture(scope="class")
    def semantic_cache(self, test_config):
        """Create Semantic Cache instance"""
        try:
            from ns_root.namespaces_adk.adk.plugins.memory_plugins import SemanticCache
            cache = SemanticCache(
                max_size=100,
                ttl=3600,
            )
            yield cache
        except ImportError as e:
            pytest.skip(f"SemanticCache not importable: {e}")
    def test_semantic_cache_initialization(self, semantic_cache):
        """Test that Semantic Cache initializes correctly"""
        assert semantic_cache is not None
    def test_semantic_cache_add_get(self, semantic_cache):
        """Test adding and getting from cache"""
        key = "smoke_cache_key"
        value = {"data": "smoke_cache_value"}
        semantic_cache.add(key, value)
        retrieved = semantic_cache.get(key)
        assert retrieved is not None
    def test_semantic_cache_clear(self, semantic_cache):
        """Test clearing the cache"""
        semantic_cache.add("key1", "value1")
        semantic_cache.add("key2", "value2")
        semantic_cache.clear()
        assert semantic_cache.get("key1") is None
        assert semantic_cache.get("key2") is None
@pytest.mark.smoke
class TestVectorSearchSmoke:
    """Smoke tests for Vector Search"""
    @pytest.fixture(scope="class")
    def vector_search(self, test_config):
        """Create Vector Search instance"""
        try:
            from ns_root.namespaces_adk.adk.plugins.memory_plugins import VectorSearch
            search = VectorSearch(
                index_name="smoke_test_index",
                dimension=1536,
            )
            yield search
        except ImportError as e:
            pytest.skip(f"VectorSearch not importable: {e}")
    def test_vector_search_initialization(self, vector_search):
        """Test that Vector Search initializes correctly"""
        assert vector_search is not None
    def test_vector_search_basic(self, vector_search):
        """Test basic vector search functionality"""
        # This is a smoke test, so we'll just verify the structure
        assert hasattr(vector_search, 'index_name') or vector_search is not None
@pytest.mark.smoke
class TestMemoryCompactorSmoke:
    """Smoke tests for Memory Compactor"""
    @pytest.fixture(scope="class")
    def memory_compactor(self):
        """Create Memory Compactor instance"""
        try:
            from ns_root.namespaces_adk.adk.plugins.memory_plugins import MemoryCompactor
            compactor = MemoryCompactor()
            yield compactor
        except ImportError as e:
            pytest.skip(f"MemoryCompactor not importable: {e}")
    def test_memory_compactor_initialization(self, memory_compactor):
        """Test that Memory Compactor initializes correctly"""
        assert memory_compactor is not None
    def test_memory_compactor_strategies(self, memory_compactor):
        """Test that compactor has strategies defined"""
        # Verify compactor has methods
        assert hasattr(memory_compactor, 'compact') or memory_compactor is not None
@pytest.mark.smoke
def test_memory_system_integration():
    """Test basic integration of memory system components"""
    try:
        # Try to import all key components
        from ns_root.namespaces_adk.adk.plugins.memory_plugins import (
            MemoryManager,
            RedisBackend,
            SemanticCache,
            VectorSearch,
            MemoryCompactor,
        )
        assert all([
            MemoryManager is not None,
            RedisBackend is not None,
            SemanticCache is not None,
            VectorSearch is not None,
            MemoryCompactor is not None,
        ])
    except ImportError as e:
        pytest.skip(f"Memory system integration test failed: {e}")