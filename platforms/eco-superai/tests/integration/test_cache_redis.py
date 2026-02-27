"""Integration tests for RedisClient — requires a live Redis instance.

Tests cover:
- Basic CRUD: set / get / delete / exists
- TTL expiry behaviour
- Bulk operations: get_many / set_many
- Pattern flush
- Atomic increment (race-condition safety)
- get_or_set (cache-aside pattern)
- Ping health check
- Error path: CacheConnectionError on broken connection
"""
from __future__ import annotations

import asyncio
import time

import pytest
import pytest_asyncio

pytestmark = [pytest.mark.asyncio, pytest.mark.integration]


class TestRedisClientBasicCRUD:
    """Fundamental set / get / delete / exists operations."""

    async def test_set_and_get_string(self, redis_client) -> None:
        await redis_client.set("key:str", "hello world")
        result = await redis_client.get("key:str")
        assert result == "hello world"

    async def test_set_and_get_dict(self, redis_client) -> None:
        payload = {"user_id": "u-123", "role": "admin", "nested": {"x": 1}}
        await redis_client.set("key:dict", payload)
        result = await redis_client.get("key:dict")
        assert result == payload

    async def test_set_and_get_list(self, redis_client) -> None:
        payload = [1, "two", {"three": 3}]
        await redis_client.set("key:list", payload)
        result = await redis_client.get("key:list")
        assert result == payload

    async def test_get_missing_key_returns_none(self, redis_client) -> None:
        result = await redis_client.get("key:nonexistent:xyz")
        assert result is None

    async def test_delete_existing_key(self, redis_client) -> None:
        await redis_client.set("key:del", "to be deleted")
        await redis_client.delete("key:del")
        assert await redis_client.get("key:del") is None

    async def test_delete_nonexistent_key_does_not_raise(self, redis_client) -> None:
        # Must not raise — idempotent delete
        await redis_client.delete("key:never:existed")

    async def test_exists_true(self, redis_client) -> None:
        await redis_client.set("key:exists:yes", 42)
        assert await redis_client.exists("key:exists:yes") is True

    async def test_exists_false(self, redis_client) -> None:
        assert await redis_client.exists("key:exists:no") is False

    async def test_overwrite_existing_key(self, redis_client) -> None:
        await redis_client.set("key:overwrite", "original")
        await redis_client.set("key:overwrite", "updated")
        result = await redis_client.get("key:overwrite")
        assert result == "updated"


class TestRedisClientTTL:
    """TTL expiry behaviour."""

    async def test_key_expires_after_ttl(self, redis_client) -> None:
        await redis_client.set("key:ttl:short", "ephemeral", ttl=1)
        assert await redis_client.exists("key:ttl:short") is True
        await asyncio.sleep(1.2)
        assert await redis_client.exists("key:ttl:short") is False

    async def test_key_persists_within_ttl(self, redis_client) -> None:
        await redis_client.set("key:ttl:long", "persistent", ttl=60)
        await asyncio.sleep(0.1)
        result = await redis_client.get("key:ttl:long")
        assert result == "persistent"


class TestRedisClientBulkOperations:
    """get_many / set_many pipeline operations."""

    async def test_set_many_and_get_many(self, redis_client) -> None:
        mapping = {
            "bulk:a": {"value": 1},
            "bulk:b": {"value": 2},
            "bulk:c": {"value": 3},
        }
        await redis_client.set_many(mapping, ttl=60)
        results = await redis_client.get_many(list(mapping.keys()))
        assert results["bulk:a"] == {"value": 1}
        assert results["bulk:b"] == {"value": 2}
        assert results["bulk:c"] == {"value": 3}

    async def test_get_many_with_missing_keys(self, redis_client) -> None:
        await redis_client.set("bulk:exists", "yes")
        results = await redis_client.get_many(["bulk:exists", "bulk:missing"])
        assert results["bulk:exists"] == "yes"
        assert results["bulk:missing"] is None

    async def test_set_many_empty_mapping_is_noop(self, redis_client) -> None:
        # Must not raise
        await redis_client.set_many({})

    async def test_get_many_empty_keys_returns_empty_dict(self, redis_client) -> None:
        result = await redis_client.get_many([])
        assert result == {}


class TestRedisClientFlushPattern:
    """Pattern-based key deletion."""

    async def test_flush_pattern_deletes_matching_keys(self, redis_client) -> None:
        await redis_client.set("session:user:1", "data1")
        await redis_client.set("session:user:2", "data2")
        await redis_client.set("session:user:3", "data3")
        await redis_client.set("other:key", "keep me")

        deleted = await redis_client.flush_pattern("session:user:*")
        assert deleted == 3
        assert await redis_client.exists("other:key") is True
        assert await redis_client.exists("session:user:1") is False

    async def test_flush_pattern_no_match_returns_zero(self, redis_client) -> None:
        deleted = await redis_client.flush_pattern("no:match:pattern:*")
        assert deleted == 0


class TestRedisClientIncrement:
    """Atomic increment — verifies counter correctness under concurrency."""

    async def test_increment_from_zero(self, redis_client) -> None:
        result = await redis_client.increment("counter:zero")
        assert result == 1

    async def test_increment_multiple_times(self, redis_client) -> None:
        for i in range(1, 6):
            result = await redis_client.increment("counter:multi")
            assert result == i

    async def test_increment_by_custom_amount(self, redis_client) -> None:
        await redis_client.increment("counter:by5", amount=5)
        result = await redis_client.increment("counter:by5", amount=5)
        assert result == 10

    async def test_concurrent_increments_are_atomic(self, redis_client) -> None:
        """10 concurrent coroutines each increment the same counter once.
        The final value MUST be exactly 10 — no lost updates.
        """
        tasks = [redis_client.increment("counter:concurrent") for _ in range(10)]
        results = await asyncio.gather(*tasks)
        # All returned values must be unique (no two coroutines got the same value)
        assert len(set(results)) == 10
        assert max(results) == 10


class TestRedisClientGetOrSet:
    """Cache-aside pattern: get_or_set."""

    async def test_get_or_set_on_miss_calls_factory(self, redis_client) -> None:
        call_count = 0

        async def factory():
            nonlocal call_count
            call_count += 1
            return {"computed": True}

        result = await redis_client.get_or_set("gos:miss", factory, ttl=60)
        assert result == {"computed": True}
        assert call_count == 1

    async def test_get_or_set_on_hit_skips_factory(self, redis_client) -> None:
        await redis_client.set("gos:hit", {"cached": True})
        call_count = 0

        async def factory():
            nonlocal call_count
            call_count += 1
            return {"should": "not be called"}

        result = await redis_client.get_or_set("gos:hit", factory, ttl=60)
        assert result == {"cached": True}
        assert call_count == 0

    async def test_get_or_set_with_plain_value(self, redis_client) -> None:
        result = await redis_client.get_or_set("gos:plain", "static_value", ttl=60)
        assert result == "static_value"
        # Second call must return cached value
        result2 = await redis_client.get_or_set("gos:plain", "different_value", ttl=60)
        assert result2 == "static_value"


class TestRedisClientPing:
    """Health check."""

    async def test_ping_returns_true(self, redis_client) -> None:
        result = await redis_client.ping()
        assert result is True


class TestRedisClientErrorPaths:
    """Error path: CacheConnectionError on broken connection."""

    async def test_broken_connection_raises_cache_connection_error(self) -> None:
        """A RedisClient pointing at a non-existent server must raise
        CacheConnectionError, not a raw redis exception.
        """
        import redis.asyncio as aioredis
        from src.infrastructure.cache.redis_client import RedisClient
        from src.shared.exceptions import CacheConnectionError

        # Temporarily override the module-level singleton
        import src.infrastructure.cache.redis_client as _mod
        original_pool = _mod._redis_pool

        broken_redis = aioredis.from_url(
            "redis://localhost:19999",  # Nothing listening here
            socket_connect_timeout=1,
            socket_timeout=1,
        )
        _mod._redis_pool = broken_redis

        client = RedisClient(prefix="broken:")
        try:
            with pytest.raises(CacheConnectionError):
                await client.ping()
        finally:
            _mod._redis_pool = original_pool
            await broken_redis.aclose()
