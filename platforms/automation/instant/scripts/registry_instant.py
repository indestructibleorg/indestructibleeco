# 
# @ECO-governed
# @ECO-layer: data
# @ECO-semantic: registry_instant
# @ECO-audit-trail: ../../engine/gov-platform.governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated

"""
Registry Manager - INSTANT 模式增強版
整合 Validator、Cache、Schema Validator
延遲目標：<500ms (p99) 完整操作
"""
import asyncio
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from .cache import MultiLayerCache
from .schema_validator import SchemaValidator
from .validator import RegistryValidator, ValidationStatus
@dataclass
class NamespaceEntry:
    """Namespace 條目"""
    namespace: str
    data: Dict[str, Any]
    status: str
    created_at: datetime
    updated_at: datetime
    version: str = "1.0.0"
class RegistryManagerInstant:
    """
    Registry Manager - INSTANT 模式
    核心特性：
    - 延遲 <500ms (p99)
    - 多層緩存 (<50ms)
    - 自動驗證
    - 事件驅動
    - 完全自治
    """
    def __init__(self):
        # 核心組件
        self.validator = RegistryValidator()
        self.cache = MultiLayerCache()
        self.schema_validator = SchemaValidator()
        # Registry 數據
        self.namespaces: Dict[str, NamespaceEntry] = {}
        # 統計
        self.stats = {
            "total_operations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "validation_passes": 0,
            "validation_failures": 0,
        }
        # 事件回調
        self.event_handlers = {
            "on_create": [],
            "on_update": [],
            "on_delete": [],
            "on_validate": [],
        }
    async def create_namespace(self, namespace: str, data: Dict[str, Any]) -> bool:
        """
        創建 Namespace
        延遲目標：<500ms (p99)
        - 驗證: <100ms
        - 緩存: <50ms
        - 存儲: <350ms
        """
        start_time = time.time()
        self.stats["total_operations"] += 1
        print(f"\n🚀 創建 Namespace: {namespace}")
        # 1. 驗證
        validation_result = await self.validator.validate_namespace(namespace, data)
        if validation_result.status != ValidationStatus.PASSED:
            self.stats["validation_failures"] += 1
            print(f"❌ 驗證失敗: {validation_result.errors}")
            return False
        self.stats["validation_passes"] += 1
        # 2. 驗證 Schema
        if "schema" in data:
            schema_result = await self.schema_validator.validate_schema(
                f"{namespace}-schema", data["schema"]
            )
            if schema_result.status.value != "realized":
                print(f"❌ Schema 驗證失敗: {schema_result.errors}")
                return False
        # 3. 創建條目
        entry = NamespaceEntry(
            namespace=namespace,
            data=data,
            status="active",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        # 4. 存儲
        self.namespaces[namespace] = entry
        # 5. 緩存
        await self.cache.set(f"namespace:{namespace}", entry.to_dict(), ttl=3600)
        # 6. 觸發事件
        await self._trigger_event("on_create", namespace, entry)
        latency = (time.time() - start_time) * 1000
        print(f"✅ 創建成功，延遲: {latency:.2f}ms")
        return True
    async def get_namespace(self, namespace: str) -> Optional[Dict[str, Any]]:
        """
        獲取 Namespace
        延遲目標：<50ms (p99) - 使用緩存
        """
        start_time = time.time()
        self.stats["total_operations"] += 1
        # 1. 嘗試從緩存獲取
        cached = await self.cache.get(f"namespace:{namespace}")
        if cached:
            self.stats["cache_hits"] += 1
            latency = (time.time() - start_time) * 1000
            print(f"✅ 從緩存獲取 {namespace}，延遲: {latency:.2f}ms")
            return cached
        # 2. 從存儲獲取
        self.stats["cache_misses"] += 1
        if namespace in self.namespaces:
            entry = self.namespaces[namespace]
            # 回填緩存
            await self.cache.set(f"namespace:{namespace}", entry.to_dict(), ttl=3600)
            latency = (time.time() - start_time) * 1000
            print(f"✅ 從存儲獲取 {namespace}，延遲: {latency:.2f}ms")
            return entry.to_dict()
        print(f"❌ Namespace 不存在: {namespace}")
        return None
    async def update_namespace(self, namespace: str, data: Dict[str, Any]) -> bool:
        """
        更新 Namespace
        延遲目標：<500ms (p99)
        """
        start_time = time.time()
        self.stats["total_operations"] += 1
        print(f"\n🔄 更新 Namespace: {namespace}")
        # 1. 檢查是否存在
        if namespace not in self.namespaces:
            print(f"❌ Namespace 不存在: {namespace}")
            return False
        # 2. 驗證
        validation_result = await self.validator.validate_namespace(namespace, data)
        if validation_result.status != ValidationStatus.PASSED:
            self.stats["validation_failures"] += 1
            print(f"❌ 驗證失敗: {validation_result.errors}")
            return False
        self.stats["validation_passes"] += 1
        # 3. 更新條目
        entry = self.namespaces[namespace]
        entry.data = data
        entry.updated_at = datetime.now()
        # 4. 失效緩存
        await self.cache.delete(f"namespace:{namespace}")
        # 5. 重新緩存
        await self.cache.set(f"namespace:{namespace}", entry.to_dict(), ttl=3600)
        # 6. 觸發事件
        await self._trigger_event("on_update", namespace, entry)
        latency = (time.time() - start_time) * 1000
        print(f"✅ 更新成功，延遲: {latency:.2f}ms")
        return True
    async def delete_namespace(self, namespace: str) -> bool:
        """
        刪除 Namespace
        延遲目標：<100ms (p99)
        """
        start_time = time.time()
        self.stats["total_operations"] += 1
        print(f"\n🗑️ 刪除 Namespace: {namespace}")
        # 1. 檢查是否存在
        if namespace not in self.namespaces:
            print(f"❌ Namespace 不存在: {namespace}")
            return False
        # 2. 刪除條目
        del self.namespaces[namespace]
        # 3. 失效緩存
        await self.cache.delete(f"namespace:{namespace}")
        # 4. 觸發事件
        await self._trigger_event("on_delete", namespace, None)
        latency = (time.time() - start_time) * 1000
        print(f"✅ 刪除成功，延遲: {latency:.2f}ms")
        return True
    async def list_namespaces(self, pattern: str = "*") -> List[str]:
        """
        列出 Namespaces
        延遲目標：<100ms (p99)
        """
        start_time = time.time()
        # 簡單的過濾邏輯
        if pattern == "*":
            namespaces = list(self.namespaces.keys())
        else:
            namespaces = [ns for ns in self.namespaces.keys() if pattern in ns]
        latency = (time.time() - start_time) * 1000
        print(f"✅ 列出 {len(namespaces)} 個 namespaces，延遲: {latency:.2f}ms")
        return namespaces
    async def search_namespaces(
        self, query: str, fields: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索 Namespaces
        延遲目標：<200ms (p99)
        """
        start_time = time.time()
        results = []
        for namespace, entry in self.namespaces.items():
            # 搜索邏輯
            if query.lower() in namespace.lower():
                results.append(entry.to_dict())
            else:
                # 搜索數據中的指定欄位
                if fields:
                    for field in fields:
                        if field in entry.data:
                            if query.lower() in str(entry.data[field]).lower():
                                results.append(entry.to_dict())
                                break
        latency = (time.time() - start_time) * 1000
        print(f"✅ 搜索找到 {len(results)} 個結果，延遲: {latency:.2f}ms")
        return results
    async def validate_all(self) -> Dict[str, Any]:
        """
        驗證所有 Namespaces
        延遲目標：<500ms (p99) - 並行驗證
        """
        start_time = time.time()
        registry_data = {
            namespace: entry.data for namespace, entry in self.namespaces.items()
        }
        # 並行驗證
        validation_results = await self.validator.validate_all(registry_data)
        # 統計
        passed = sum(
            1
            for r in validation_results.values()
            if r.status == ValidationStatus.PASSED
        )
        failed = len(validation_results) - passed
        latency = (time.time() - start_time) * 1000
        result = {
            "total": len(validation_results),
            "passed": passed,
            "failed": failed,
            "results": validation_results,
            "latency_ms": latency,
        }
        print(
            f"✅ 驗證完成: {passed}/{len(validation_results)} 通過，延遲: {latency:.2f}ms"
        )
        return result
    async def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        cache_stats = self.cache.get_stats()
        return {
            "operations": self.stats,
            "cache": cache_stats,
            "total_namespaces": len(self.namespaces),
        }
    async def _trigger_event(
        self, event_type: str, namespace: str, entry: Optional[NamespaceEntry]
    ):
        """觸發事件"""
        handlers = self.event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                await handler(namespace, entry)
            except Exception as e:
                print(f"⚠️ 事件處理器錯誤: {e}")
    def on_event(self, event_type: str):
        """註冊事件處理器"""
        def decorator(func):
            if event_type not in self.event_handlers:
                self.event_handlers[event_type] = []
            self.event_handlers[event_type].append(func)
            return func
        return decorator
# 輔助方法
def to_dict(self) -> Dict[str, Any]:
    """轉換為字典"""
    return {
        "namespace": self.namespace,
        "data": self.data,
        "status": self.status,
        "created_at": self.created_at.isoformat(),
        "updated_at": self.updated_at.isoformat(),
        "version": self.version,
    }
# 添加到 NamespaceEntry 類
NamespaceEntry.to_dict = to_dict
# 使用範例
async def main():
    """測試 Registry Manager - INSTANT 模式"""
    registry = RegistryManagerInstant()
    print("\n=== 測試 Registry Manager - INSTANT 模式 ===\n")
    # 1. 創建 Namespaces
    test_data_1 = {
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
    await registry.create_namespace("platform-registry-service-v1", test_data_1)
    await registry.create_namespace("platform-agent-service-v1", test_data_1)
    await registry.create_namespace("platform-gateway-service-v1", test_data_1)
    # 2. 獲取 Namespace（測試緩存）
    await registry.get_namespace("platform-registry-service-v1")
    await registry.get_namespace("platform-registry-service-v1")  # 第二次，應該命中緩存
    # 3. 列出 Namespaces
    namespaces = await registry.list_namespaces()
    print(f"\n📋 Namespaces: {namespaces}")
    # 4. 搜索 Namespaces
    results = await registry.search_namespaces("registry")
    print(f"\n🔍 搜索結果: {len(results)} 個")
    # 5. 驗證所有
    validation = await registry.validate_all()
    print(f"\n✅ 驗證結果: {validation['passed']}/{validation['total']} 通過")
    # 6. 獲取統計
    stats = await registry.get_stats()
    print("\n📊 統計信息:")
    print(f"  總操作數: {stats['operations']['total_operations']}")
    print(f"  總 Namespaces: {stats['total_namespaces']}")
    print(f"  緩存命中率: {stats['cache']['hit_rate']}")
if __name__ == "__main__":
    asyncio.run(main())
