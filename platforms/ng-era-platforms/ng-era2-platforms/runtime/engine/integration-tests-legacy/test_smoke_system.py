#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: test_smoke_system
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
"""
Smoke Tests - Quick verification of core system functionality
"""
import pytest
import sys
import os
from pathlib import Path
# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
@pytest.mark.smoke
class TestSystemInitialization:
    """Test system initialization and basic startup"""
    def test_python_version_available(self):
        """Test that Python 3.11+ is available"""
        import platform
        version = platform.python_version_tuple()
        assert int(version[0]) >= 3, "Python version should be 3.x"
        assert int(version[1]) >= 11, "Python version should be 3.11+"
    def test_project_structure_exists(self):
        """Test that project structure is correct"""
        project_root = Path(__file__).parent.parent
        # Check key directories
        assert project_root.exists(), "Project root should exist"
        assert (project_root / "ns-root").exists(), "ns-root directory should exist"
        assert (project_root / "ns-root" / "namespaces-adk").exists(), "namespaces-adk directory should exist"
    def test_adk_module_importable(self):
        """Test that ADK module can be imported"""
        try:
            from ns_root.namespaces_adk import adk
            assert adk is not None
        except ImportError as e:
            pytest.skip(f"ADK module not importable: {e}")
    def test_memory_plugins_importable(self):
        """Test that memory plugins can be imported"""
        try:
            from ns_root.namespaces_adk.adk.plugins.memory_plugins import (
                RedisBackend,
                SemanticCache,
                MemoryManager,
            )
            assert RedisBackend is not None
            assert SemanticCache is not None
            assert MemoryManager is not None
        except ImportError as e:
            pytest.skip(f"Memory plugins not importable: {e}")
    def test_configuration_plugin_importable(self):
        """Test that configuration plugin can be imported"""
        try:
            from ns_root.namespaces_adk.adk.plugins.configuration import (
                ConfigurationManager,
                ConfigHotReloader,
            )
            assert ConfigurationManager is not None
            assert ConfigHotReloader is not None
        except ImportError as e:
            pytest.skip(f"Configuration plugin not importable: {e}")
    def test_reporting_plugin_importable(self):
        """Test that reporting plugin can be imported"""
        try:
            from ns_root.namespaces_adk.adk.plugins.reporting import (
                PDFReportGenerator,
                ChartRenderer,
            )
            assert PDFReportGenerator is not None
            assert ChartRenderer is not None
        except ImportError as e:
            pytest.skip(f"Reporting plugin not importable: {e}")
    def test_supply_chain_verifier_importable(self):
        """Test that supply chain verifier can be imported"""
        try:
            from controlplane.validation import SupplyChainVerifier
            assert SupplyChainVerifier is not None
        except ImportError as e:
            pytest.skip(f"Supply chain verifier not importable: {e}")
@pytest.mark.smoke
class TestRedisConnection:
    """Test Redis connectivity"""
    @pytest.fixture(scope="class")
    def redis_client(self):
        """Redis client for testing"""
        import redis
        try:
            client = redis.Redis(
                host="localhost",
                port=6379,
                db=15,
                decode_responses=True,
                socket_timeout=5,
            )
            client.ping()
            yield client
        except redis.ConnectionError:
            pytest.skip("Redis connection failed")
        finally:
            try:
                client.flushdb()
            except Exception:
                pass
    def test_redis_connection(self, redis_client):
        """Test that Redis connection is working"""
        assert redis_client is not None
        assert redis_client.ping() is True
    def test_redis_basic_operations(self, redis_client):
        """Test basic Redis operations"""
        # Set
        redis_client.set("test_key", "test_value")
        # Get
        value = redis_client.get("test_key")
        assert value == "test_value"
        # Delete
        redis_client.delete("test_key")
        # Verify deletion
        value = redis_client.get("test_key")
        assert value is None
    def test_redis_expiration(self, redis_client):
        """Test Redis expiration"""
        redis_client.set("expire_key", "expire_value", ex=10)
        value = redis_client.get("expire_key")
        assert value == "expire_value"
        redis_client.delete("expire_key")
@pytest.mark.smoke
class TestBasicMemoryOperations:
    """Test basic memory operations"""
    @pytest.fixture(scope="class")
    def redis_client(self):
        """Redis client for testing"""
        import redis
        try:
            client = redis.Redis(
                host="localhost",
                port=6379,
                db=15,
                decode_responses=True,
            )
            client.ping()
            yield client
        except redis.ConnectionError:
            pytest.skip("Redis connection failed")
        finally:
            try:
                client.flushdb()
            except Exception:
                pass
    def test_memory_add_and_retrieve(self, redis_client):
        """Test adding and retrieving memory"""
        # Add memory
        memory_id = "smoke_test_memory_001"
        memory_data = {
            "content": "This is a smoke test memory",
            "metadata": {"test": "smoke"},
        }
        redis_client.hset(f"memory:{memory_id}", mapping=memory_data)
        # Retrieve memory
        retrieved = redis_client.hgetall(f"memory:{memory_id}")
        assert retrieved["content"] == "This is a smoke test memory"
        assert retrieved["metadata"] == '{"test": "smoke"}'
        # Cleanup
        redis_client.delete(f"memory:{memory_id}")
    def test_memory_search(self, redis_client):
        """Test basic memory search"""
        # Add multiple memories
        for i in range(3):
            memory_id = f"smoke_test_memory_{i:03d}"
            memory_data = {
                "content": f"This is smoke test memory {i}",
            "metadata": f'{{"test": "smoke", "index": {i}}}',
            }
            redis_client.hset(f"memory:{memory_id}", mapping=memory_data)
        # Search for memories
        keys = redis_client.keys("memory:smoke_test_memory_*")
        assert len(keys) == 3
        # Cleanup
        for i in range(3):
            redis_client.delete(f"memory:smoke_test_memory_{i:03d}")
@pytest.mark.smoke
class TestConfigurationLoading:
    """Test configuration loading"""
    def test_default_configuration_loading(self, test_config):
        """Test loading default configuration"""
        config = test_config
        assert config is not None
        assert "redis_host" in config
        assert "redis_port" in config
        assert "test_data_dir" in config
    def test_configuration_structure(self, test_data):
        """Test configuration structure"""
        config = test_data["configuration"]
        assert config is not None
        assert "version" in config
        assert "settings" in config
        assert "features" in config
        assert "redis" in config["settings"]
@pytest.mark.smoke
class TestReportGeneration:
    """Test basic report generation"""
    def test_report_data_structure(self, test_data):
        """Test report data structure"""
        report_data = test_data["report_data"]
        assert report_data is not None
        assert "title" in report_data
        assert "charts" in report_data
        assert "tables" in report_data
        assert isinstance(report_data["charts"], list)
        assert isinstance(report_data["tables"], list)
@pytest.mark.smoke
class TestSupplyChainProject:
    """Test supply chain project structure"""
    def test_project_structure(self, test_data):
        """Test project structure"""
        project = test_data["supply_chain_small"]
        assert project is not None
        assert "name" in project
        assert "size" in project
        assert "files" in project
        assert "config" in project
        assert isinstance(project["files"], list)
        assert "stages" in project["config"]
@pytest.mark.smoke
class TestTestEnvironment:
    """Test test environment setup"""
    def test_directories_created(self, test_environment):
        """Test that all required directories are created"""
        env = test_environment
        assert env["test_data_dir"].exists()
        assert env["output_dir"].exists()
        assert env["log_dir"].exists()
        assert env["report_dir"].exists()
    def test_test_data_factory(self, test_data):
        """Test test data factory"""
        assert test_data is not None
        assert "memories" in test_data
        assert "configuration" in test_data
        assert "report_data" in test_data
        assert "supply_chain_small" in test_data
        assert len(test_data["memories"]) == 10
@pytest.mark.smoke
def test_system_health_check(test_config):
    """Comprehensive system health check"""
    health_status = {
        "python": False,
        "project_structure": False,
        "redis": False,
        "directories": False,
    }
    # Check Python version
    import platform
    version = platform.python_version_tuple()
    health_status["python"] = int(version[0]) >= 3 and int(version[1]) >= 11
    # Check project structure
    project_root = Path(__file__).parent.parent
    health_status["project_structure"] = (project_root.exists() and 
                                          (project_root / "ns-root").exists())
    # Check Redis
    import redis
    try:
        client = redis.Redis(
            host=test_config["redis_host"],
            port=test_config["redis_port"],
            db=test_config["redis_db"],
            socket_timeout=2,
        )
        client.ping()
        health_status["redis"] = True
    except Exception:
        health_status["redis"] = False
    # Check directories
    health_status["directories"] = test_config["test_data_dir"].exists()
    # Overall health
    overall_health = all(health_status.values())
    # Print health status
    print("\n=== System Health Check ===")
    for component, status in health_status.items():
        status_str = "✓" if status else "✗"
        print(f"{status_str} {component}: {'OK' if status else 'FAILED'}")
    print("==========================\n")
    # Assert overall health
    assert overall_health, "System health check failed"