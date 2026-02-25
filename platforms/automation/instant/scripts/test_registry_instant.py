# 
# @ECO-governed
# @ECO-layer: data
# @ECO-semantic: test_registry_instant
# @ECO-audit-trail: ../../engine/gov-platform.governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated

"""
Unit Tests for Registry - INSTANT 模式
驗證所有功能符合 INSTANT 執行標準
延遲目標：<500ms (p99)
"""
import time
import pytest
from namespace_registry.cache import CacheLevel, MultiLayerCache
from namespace_registry.registry_instant import RegistryManagerInstant
from namespace_registry.schema_validator import SchemaValidationStatus, SchemaValidator
from namespace_registry.validator import RegistryValidator, ValidationStatus
class TestRegistryValidator:
    """測試 Registry Validator"""
    @pytest.fixture
    def validator(self):
        return RegistryValidator()
    @pytest.fixture
    def valid_namespace_data(self):
        return {
            "taxonomy": {
                "domain": "platform",
                "name": "registry",
                "type": "service",
                "version": "v1",
                "naming_format": "kebab",
            },
            "schema": {"version": "1.0.0", "type": "object", "properties": {}},
            "metadata": {
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "owner": "platform-team",
                "status": "active",
            },
            "compliance": {"instant": True, "taxonomy": True},
            "security": {"access_control": "rbac"},
        }
    @pytest.mark.asyncio
    async def test_validate_namespace_valid(self, validator, valid_namespace_data):
        """測試驗證有效的 namespace"""
        result = await validator.validate_namespace(
            "platform-registry-service-v1", valid_namespace_data
        )
        assert result.status == ValidationStatus.PASSED
        assert len(result.errors) == 0
        assert result.latency_ms < 100  # <100ms
    @pytest.mark.asyncio
    async def test_validate_namespace_invalid(self, validator):
        """測試驗證無效的 namespace"""
        invalid_data = {}
        result = await validator.validate_namespace("invalid-namespace", invalid_data)
        assert result.status == ValidationStatus.FAILED_INVALID
        assert len(result.errors) > 0
    @pytest.mark.asyncio
    async def test_validate_all_parallel(self, validator, valid_namespace_data):
        """測試並行驗證所有 namespaces"""
        registry = {
            "platform-registry-service-v1": valid_namespace_data,
            "platform-agent-service-v1": valid_namespace_data,
            "platform-gateway-service-v1": valid_namespace_data,
        }
        results = await validator.validate_all(registry)
        assert len(results) == 3
        assert all(r.status == ValidationStatus.PASSED for r in results.values())
        assert (
            sum(r.latency_ms for r in results.values()) / len(results) < 500
        )  # <500ms
class TestMultiLayerCache:
    """測試 Multi-Layer Cache"""
    @pytest.fixture
    def cache(self):
        return MultiLayerCache()
    @pytest.mark.asyncio
    async def test_cache_set_get(self, cache):
        """測試緩存設置和獲取"""
        await cache.set("test-key", {"data": "value"})
        result = await cache.get("test-key")
        assert result is not None
        assert result["data"] == "value"
    @pytest.mark.asyncio
    async def test_cache_hit_local(self, cache):
        """測試 Local Cache 命中"""
        await cache.set("test-key", {"data": "value"}, level=CacheLevel.LOCAL)
        # 第一次獲取
        result1 = await cache.get("test-key")
        assert result1 is not None
        # 第二次獲取，應該命中 Local
        result2 = await cache.get("test-key")
        assert result2 is not None
        stats = cache.get_stats()
        assert stats["local_hits"] >= 1
    @pytest.mark.asyncio
    async def test_cache_miss(self, cache):
        """測試 Cache Miss"""
        result = await cache.get("nonexistent-key")
        assert result is None
        stats = cache.get_stats()
        assert stats["misses"] == 1
    @pytest.mark.asyncio
    async def test_cache_delete(self, cache):
        """測試緩存刪除"""
        await cache.set("test-key", {"data": "value"})
        # 驗證存在
        result = await cache.get("test-key")
        assert result is not None
        # 刪除
        await cache.delete("test-key")
        # 驗證不存在
        result = await cache.get("test-key")
        assert result is None
    @pytest.mark.asyncio
    async def test_cache_invalidate(self, cache):
        """測試批量失效"""
        await cache.set("key1", {"data": "value1"})
        await cache.set("key2", {"data": "value2"})
        await cache.set("other-key", {"data": "value3"})
        # 失效所有 key- 開頭的
        count = await cache.invalidate("key")
        assert count >= 2
    @pytest.mark.asyncio
    async def test_cache_latency(self, cache):
        """測試緩存延遲"""
        await cache.set("test-key", {"data": "value"})
        start = time.time()
        result = await cache.get("test-key")
        latency = (time.time() - start) * 1000
        assert result is not None
        assert latency < 50  # <50ms (p99)
class TestSchemaValidator:
    """測試 Schema Validator"""
    @pytest.fixture
    def validator(self):
        return SchemaValidator()
    @pytest.fixture
    def valid_schema(self):
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "version": "1.0.0",
            "properties": {"namespace": {"type": "string", "format": "uuid"}},
        }
    @pytest.mark.asyncio
    async def test_validate_schema_valid(self, validator, valid_schema):
        """測試驗證有效的 schema"""
        result = await validator.validate_schema("test-schema", valid_schema)
        assert result.status == SchemaValidationStatus.PASSED
        assert len(result.errors) == 0
        assert result.latency_ms < 100  # <100ms
    @pytest.mark.asyncio
    async def test_validate_schema_invalid(self, validator):
        """測試驗證無效的 schema"""
        invalid_schema = {"type": "invalid_type"}
        result = await validator.validate_schema("test-schema", invalid_schema)
        assert result.status in [
            SchemaValidationStatus.FAILED_INVALID,
            SchemaValidationStatus.FAILED_UNREALIZABLE,
        ]
        assert len(result.errors) > 0
    @pytest.mark.asyncio
    async def test_validate_all_schemas(self, validator, valid_schema):
        """測試並行驗證所有 schemas"""
        schemas = {
            "schema1": valid_schema,
            "schema2": valid_schema,
            "schema3": valid_schema,
        }
        results = await validator.validate_all(schemas)
        assert len(results) == 3
        assert all(r.status == SchemaValidationStatus.PASSED for r in results.values())
class TestRegistryManagerInstant:
    """測試 Registry Manager - INSTANT 模式"""
    @pytest.fixture
    def registry(self):
        return RegistryManagerInstant()
    @pytest.fixture
    def valid_namespace_data(self):
        return {
            "taxonomy": {
                "domain": "platform",
                "name": "registry",
                "type": "service",
                "version": "v1",
                "naming_format": "kebab",
            },
            "schema": {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "version": "1.0.0",
                "properties": {},
            },
            "metadata": {
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "owner": "platform-team",
                "status": "active",
            },
            "compliance": {"instant": True, "taxonomy": True},
            "security": {"access_control": "rbac"},
        }
    @pytest.mark.asyncio
    async def test_create_namespace(self, registry, valid_namespace_data):
        """測試創建 namespace"""
        result = await registry.create_namespace(
            "platform-registry-service-v1", valid_namespace_data
        )
        assert result is True
        assert "platform-registry-service-v1" in registry.namespaces
    @pytest.mark.asyncio
    async def test_create_namespace_invalid(self, registry):
        """測試創建無效的 namespace"""
        result = await registry.create_namespace("invalid-namespace", {})
        assert result is False
    @pytest.mark.asyncio
    async def test_get_namespace_cache_hit(self, registry, valid_namespace_data):
        """測試獲取 namespace（緩存命中）"""
        # 創建
        await registry.create_namespace(
            "platform-registry-service-v1", valid_namespace_data
        )
        # 第一次獲取
        result1 = await registry.get_namespace("platform-registry-service-v1")
        assert result1 is not None
        # 第二次獲取，應該命中緩存
        result2 = await registry.get_namespace("platform-registry-service-v1")
        assert result2 is not None
        # 驗證緩存命中
        stats = await registry.get_stats()
        assert stats["cache"]["local_hits"] >= 1
    @pytest.mark.asyncio
    async def test_update_namespace(self, registry, valid_namespace_data):
        """測試更新 namespace"""
        # 創建
        await registry.create_namespace(
            "platform-registry-service-v1", valid_namespace_data
        )
        # 更新
        updated_data = valid_namespace_data.copy()
        updated_data["metadata"]["status"] = "updated"
        result = await registry.update_namespace(
            "platform-registry-service-v1", updated_data
        )
        assert result is True
    @pytest.mark.asyncio
    async def test_delete_namespace(self, registry, valid_namespace_data):
        """測試刪除 namespace"""
        # 創建
        await registry.create_namespace(
            "platform-registry-service-v1", valid_namespace_data
        )
        # 刪除
        result = await registry.delete_namespace("platform-registry-service-v1")
        assert result is True
        assert "platform-registry-service-v1" not in registry.namespaces
    @pytest.mark.asyncio
    async def test_list_namespaces(self, registry, valid_namespace_data):
        """測試列出 namespaces"""
        # 創建多個
        await registry.create_namespace("ns1", valid_namespace_data)
        await registry.create_namespace("ns2", valid_namespace_data)
        await registry.create_namespace("ns3", valid_namespace_data)
        # 列出
        namespaces = await registry.list_namespaces()
        assert len(namespaces) == 3
    @pytest.mark.asyncio
    async def test_search_namespaces(self, registry, valid_namespace_data):
        """測試搜索 namespaces"""
        # 創建
        await registry.create_namespace(
            "platform-registry-service", valid_namespace_data
        )
        await registry.create_namespace("platform-agent-service", valid_namespace_data)
        await registry.create_namespace("other-namespace", valid_namespace_data)
        # 搜索
        results = await registry.search_namespaces("platform")
        assert len(results) == 2
    @pytest.mark.asyncio
    async def test_validate_all(self, registry, valid_namespace_data):
        """測試驗證所有 namespaces"""
        # 創建多個
        await registry.create_namespace("ns1", valid_namespace_data)
        await registry.create_namespace("ns2", valid_namespace_data)
        await registry.create_namespace("ns3", valid_namespace_data)
        # 驗證所有
        result = await registry.validate_all()
        assert result["total"] == 3
        assert result["passed"] == 3
        assert result["failed"] == 0
        assert result["latency_ms"] < 500  # <500ms
    @pytest.mark.asyncio
    async def test_operation_latency(self, registry, valid_namespace_data):
        """測試操作延遲"""
        # 創建
        start = time.time()
        await registry.create_namespace("test-ns", valid_namespace_data)
        create_latency = (time.time() - start) * 1000
        assert create_latency < 500  # <500ms
        # 獲取
        start = time.time()
        await registry.get_namespace("test-ns")
        get_latency = (time.time() - start) * 1000
        assert get_latency < 50  # <50ms (緩存)
        # 更新
        start = time.time()
        await registry.update_namespace("test-ns", valid_namespace_data)
        update_latency = (time.time() - start) * 1000
        assert update_latency < 500  # <500ms
        # 刪除
        start = time.time()
        await registry.delete_namespace("test-ns")
        delete_latency = (time.time() - start) * 1000
        assert delete_latency < 100  # <100ms
# 運行測試
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
