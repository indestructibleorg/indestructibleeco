"""Unit tests for src/infrastructure/cache/redis_client.py.

All Redis I/O is mocked via AsyncMock so no real Redis server is required.
Target coverage: lines 64-65, 98-99, 112, 121-122, 155-158, 162-169,
173-179, 183-189, 200, 208-211, 232-235, 254-257, 282-284, 297-304.
"""
from __future__ import annotations

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_redis(
    *,
    get_return=None,
    set_side_effect=None,
    delete_return=1,
    exists_return=1,
    incrby_return=5,
    mget_return=None,
    pipeline_execute_return=None,
    scan_iter_items=None,
    ping_return=True,
):
    """Build a mock aioredis.Redis object with configurable behaviour."""
    mock = AsyncMock()
    mock.get = AsyncMock(return_value=get_return)
    mock.set = AsyncMock(side_effect=set_side_effect)
    mock.delete = AsyncMock(return_value=delete_return)
    mock.exists = AsyncMock(return_value=exists_return)
    mock.incrby = AsyncMock(return_value=incrby_return)
    mock.mget = AsyncMock(return_value=mget_return or [])
    mock.ping = AsyncMock(return_value=ping_return)

    # Pipeline mock
    pipe = AsyncMock()
    pipe.set = MagicMock(return_value=pipe)
    pipe.execute = AsyncMock(return_value=pipeline_execute_return or [])
    mock.pipeline = MagicMock(return_value=pipe)

    # scan_iter async generator
    async def _scan_iter(match=None):
        for item in (scan_iter_items or []):
            yield item
    mock.scan_iter = _scan_iter

    return mock


# ---------------------------------------------------------------------------
# get_redis – exception path (lines 64-65)
# ---------------------------------------------------------------------------

class TestGetRedisException:
    """Cover lines 64-65: CacheConnectionError raised when pool creation fails."""

    @pytest.mark.asyncio
    async def test_get_redis_raises_cache_connection_error_on_failure(self):
        """Lines 64-65 – aioredis.from_url raises, wrapped in CacheConnectionError."""
        import src.infrastructure.cache.redis_client as module
        from src.shared.exceptions import CacheConnectionError

        original_pool = module._redis_pool
        module._redis_pool = None  # ensure fresh creation path
        try:
            with patch(
                "src.infrastructure.cache.redis_client.aioredis.from_url",
                side_effect=RuntimeError("connection refused"),
            ):
                with pytest.raises(CacheConnectionError, match="connection refused"):
                    await module.get_redis()
        finally:
            module._redis_pool = original_pool


# ---------------------------------------------------------------------------
# RedisClient.__init__ (lines 98-99)
# ---------------------------------------------------------------------------

class TestRedisClientInit:
    """Cover lines 98-99: __init__ stores prefix and default_ttl."""

    def test_custom_prefix_and_ttl(self):
        """Lines 98-99 – custom prefix and ttl are stored."""
        from src.infrastructure.cache.redis_client import RedisClient
        client = RedisClient(prefix="myapp", default_ttl=600)
        assert client._prefix == "myapp"
        assert client._default_ttl == 600


# ---------------------------------------------------------------------------
# _deserialize – fallback path (lines 121-122)
# ---------------------------------------------------------------------------

class TestRedisClientDeserialize:
    """Cover lines 121-122: JSON decode error falls back to raw string."""

    def test_deserialize_invalid_json_returns_raw(self):
        """Lines 121-122 – invalid JSON returns the raw string."""
        from src.infrastructure.cache.redis_client import RedisClient
        raw = "not-valid-json{"
        result = RedisClient._deserialize(raw)
        assert result == raw

    def test_deserialize_none_returns_none(self):
        """Line 117-118 – None input returns None."""
        from src.infrastructure.cache.redis_client import RedisClient
        assert RedisClient._deserialize(None) is None

    def test_deserialize_valid_json(self):
        """Line 120 – valid JSON is parsed."""
        from src.infrastructure.cache.redis_client import RedisClient
        assert RedisClient._deserialize('{"a": 1}') == {"a": 1}


# ---------------------------------------------------------------------------
# set – exception path (lines 155-158)
# ---------------------------------------------------------------------------

class TestRedisClientSet:
    """Cover lines 155-158: non-CacheConnectionError wrapped on set."""

    @pytest.mark.asyncio
    async def test_set_wraps_generic_exception(self):
        """Lines 155-158 – generic exception from redis.set is wrapped."""
        from src.infrastructure.cache.redis_client import RedisClient
        from src.shared.exceptions import CacheConnectionError

        mock_redis = _make_mock_redis(set_side_effect=RuntimeError("timeout"))
        with patch(
            "src.infrastructure.cache.redis_client.get_redis",
            return_value=mock_redis,
        ):
            client = RedisClient()
            with pytest.raises(CacheConnectionError, match="SET"):
                await client.set("key", "value")

    @pytest.mark.asyncio
    async def test_set_reraises_cache_connection_error(self):
        """Lines 155-156 – CacheConnectionError is re-raised directly."""
        from src.infrastructure.cache.redis_client import RedisClient
        from src.shared.exceptions import CacheConnectionError

        mock_redis = _make_mock_redis(
            set_side_effect=CacheConnectionError("already wrapped")
        )
        with patch(
            "src.infrastructure.cache.redis_client.get_redis",
            return_value=mock_redis,
        ):
            client = RedisClient()
            with pytest.raises(CacheConnectionError, match="already wrapped"):
                await client.set("key", "value")


# ---------------------------------------------------------------------------
# delete (lines 162-169)
# ---------------------------------------------------------------------------

class TestRedisClientDelete:
    """Cover lines 162-169: delete success and exception paths."""

    @pytest.mark.asyncio
    async def test_delete_returns_true_when_key_existed(self):
        """Lines 162-165 – delete returns True when key existed."""
        from src.infrastructure.cache.redis_client import RedisClient

        mock_redis = _make_mock_redis(delete_return=1)
        with patch(
            "src.infrastructure.cache.redis_client.get_redis",
            return_value=mock_redis,
        ):
            client = RedisClient()
            result = await client.delete("mykey")
            assert result is True

    @pytest.mark.asyncio
    async def test_delete_returns_false_when_key_missing(self):
        """Lines 162-165 – delete returns False when key was absent."""
        from src.infrastructure.cache.redis_client import RedisClient

        mock_redis = _make_mock_redis(delete_return=0)
        with patch(
            "src.infrastructure.cache.redis_client.get_redis",
            return_value=mock_redis,
        ):
            client = RedisClient()
            result = await client.delete("missing")
            assert result is False

    @pytest.mark.asyncio
    async def test_delete_wraps_generic_exception(self):
        """Lines 168-169 – generic exception is wrapped in CacheConnectionError."""
        from src.infrastructure.cache.redis_client import RedisClient
        from src.shared.exceptions import CacheConnectionError

        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(side_effect=RuntimeError("network error"))
        with patch(
            "src.infrastructure.cache.redis_client.get_redis",
            return_value=mock_redis,
        ):
            client = RedisClient()
            with pytest.raises(CacheConnectionError, match="DELETE"):
                await client.delete("key")


# ---------------------------------------------------------------------------
# exists (lines 173-179)
# ---------------------------------------------------------------------------

class TestRedisClientExists:
    """Cover lines 173-179: exists success and exception paths."""

    @pytest.mark.asyncio
    async def test_exists_returns_true(self):
        """Lines 173-175 – exists returns True when key present."""
        from src.infrastructure.cache.redis_client import RedisClient

        mock_redis = _make_mock_redis(exists_return=1)
        with patch(
            "src.infrastructure.cache.redis_client.get_redis",
            return_value=mock_redis,
        ):
            client = RedisClient()
            assert await client.exists("k") is True

    @pytest.mark.asyncio
    async def test_exists_wraps_generic_exception(self):
        """Lines 178-179 – generic exception is wrapped."""
        from src.infrastructure.cache.redis_client import RedisClient
        from src.shared.exceptions import CacheConnectionError

        mock_redis = AsyncMock()
        mock_redis.exists = AsyncMock(side_effect=OSError("broken pipe"))
        with patch(
            "src.infrastructure.cache.redis_client.get_redis",
            return_value=mock_redis,
        ):
            client = RedisClient()
            with pytest.raises(CacheConnectionError, match="EXISTS"):
                await client.exists("k")


# ---------------------------------------------------------------------------
# incr (lines 183-189)
# ---------------------------------------------------------------------------

class TestRedisClientIncr:
    """Cover lines 183-189: incr success and exception paths."""

    @pytest.mark.asyncio
    async def test_incr_returns_new_value(self):
        """Lines 183-185 – increment returns the new counter value."""
        from src.infrastructure.cache.redis_client import RedisClient

        mock_redis = _make_mock_redis(incrby_return=7)
        with patch(
            "src.infrastructure.cache.redis_client.get_redis",
            return_value=mock_redis,
        ):
            client = RedisClient()
            result = await client.increment("counter", amount=3)
            assert result == 7

    @pytest.mark.asyncio
    async def test_incr_wraps_generic_exception(self):
        """Lines 188-189 – generic exception is wrapped."""
        from src.infrastructure.cache.redis_client import RedisClient
        from src.shared.exceptions import CacheConnectionError

        mock_redis = AsyncMock()
        mock_redis.incrby = AsyncMock(side_effect=RuntimeError("overflow"))
        with patch(
            "src.infrastructure.cache.redis_client.get_redis",
            return_value=mock_redis,
        ):
            client = RedisClient()
            with pytest.raises(CacheConnectionError, match="INCR"):
                await client.increment("counter")


# ---------------------------------------------------------------------------
# get_many – empty keys (line 200) and exception path (lines 208-211)
# ---------------------------------------------------------------------------

class TestRedisClientGetMany:
    """Cover lines 200, 208-211: get_many edge cases."""

    @pytest.mark.asyncio
    async def test_get_many_empty_keys_returns_empty_dict(self):
        """Line 200 – empty keys list returns empty dict immediately."""
        from src.infrastructure.cache.redis_client import RedisClient

        client = RedisClient()
        result = await client.get_many([])
        assert result == {}

    @pytest.mark.asyncio
    async def test_get_many_wraps_generic_exception(self):
        """Lines 208-211 – generic exception is wrapped."""
        from src.infrastructure.cache.redis_client import RedisClient
        from src.shared.exceptions import CacheConnectionError

        mock_redis = AsyncMock()
        mock_redis.mget = AsyncMock(side_effect=RuntimeError("mget failed"))
        with patch(
            "src.infrastructure.cache.redis_client.get_redis",
            return_value=mock_redis,
        ):
            client = RedisClient()
            with pytest.raises(CacheConnectionError, match="MGET"):
                await client.get_many(["k1", "k2"])


# ---------------------------------------------------------------------------
# set_many – exception path (lines 232-235)
# ---------------------------------------------------------------------------

class TestRedisClientSetMany:
    """Cover lines 232-235: set_many exception path."""

    @pytest.mark.asyncio
    async def test_set_many_wraps_generic_exception(self):
        """Lines 232-235 – generic exception from pipeline is wrapped."""
        from src.infrastructure.cache.redis_client import RedisClient
        from src.shared.exceptions import CacheConnectionError

        mock_redis = AsyncMock()
        pipe = AsyncMock()
        pipe.set = MagicMock(return_value=pipe)
        pipe.execute = AsyncMock(side_effect=RuntimeError("pipeline error"))
        mock_redis.pipeline = MagicMock(return_value=pipe)
        with patch(
            "src.infrastructure.cache.redis_client.get_redis",
            return_value=mock_redis,
        ):
            client = RedisClient()
            with pytest.raises(CacheConnectionError, match="MSET"):
                await client.set_many({"k1": "v1", "k2": "v2"})


# ---------------------------------------------------------------------------
# flush_pattern – exception path (lines 254-257)
# ---------------------------------------------------------------------------

class TestRedisClientFlushPattern:
    """Cover lines 254-257: flush_pattern exception path."""

    @pytest.mark.asyncio
    async def test_flush_pattern_wraps_generic_exception(self):
        """Lines 254-257 – generic exception is wrapped."""
        from src.infrastructure.cache.redis_client import RedisClient
        from src.shared.exceptions import CacheConnectionError

        mock_redis = AsyncMock()

        async def _bad_scan_iter(match=None):
            raise RuntimeError("scan failed")
            yield  # make it an async generator

        mock_redis.scan_iter = _bad_scan_iter
        with patch(
            "src.infrastructure.cache.redis_client.get_redis",
            return_value=mock_redis,
        ):
            client = RedisClient()
            with pytest.raises(CacheConnectionError, match="FLUSH_PATTERN"):
                await client.flush_pattern("prefix:*")


# ---------------------------------------------------------------------------
# get_or_set – sync factory path (lines 282-284)
# ---------------------------------------------------------------------------

class TestRedisClientGetOrSet:
    """Cover lines 282-284: get_or_set with sync callable factory."""

    @pytest.mark.asyncio
    async def test_get_or_set_sync_factory_called_on_miss(self):
        """Lines 282-284 – sync factory is called when cache misses."""
        from src.infrastructure.cache.redis_client import RedisClient

        mock_redis = _make_mock_redis(get_return=None)
        with patch(
            "src.infrastructure.cache.redis_client.get_redis",
            return_value=mock_redis,
        ):
            client = RedisClient()
            call_count = 0

            def sync_factory():
                nonlocal call_count
                call_count += 1
                return {"computed": True}

            result = await client.get_or_set("key", sync_factory, ttl=60)
            assert result == {"computed": True}
            assert call_count == 1


# ---------------------------------------------------------------------------
# ping (lines 297-304)
# ---------------------------------------------------------------------------

class TestRedisClientPing:
    """Cover lines 297-304: ping success and exception paths."""

    @pytest.mark.asyncio
    async def test_ping_returns_true_on_success(self):
        """Lines 297-300 – ping returns True when Redis responds."""
        from src.infrastructure.cache.redis_client import RedisClient

        mock_redis = _make_mock_redis(ping_return=True)
        with patch(
            "src.infrastructure.cache.redis_client.get_redis",
            return_value=mock_redis,
        ):
            client = RedisClient()
            assert await client.ping() is True

    @pytest.mark.asyncio
    async def test_ping_wraps_generic_exception(self):
        """Lines 303-304 – generic exception is wrapped in CacheConnectionError."""
        from src.infrastructure.cache.redis_client import RedisClient
        from src.shared.exceptions import CacheConnectionError

        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(side_effect=OSError("connection reset"))
        with patch(
            "src.infrastructure.cache.redis_client.get_redis",
            return_value=mock_redis,
        ):
            client = RedisClient()
            with pytest.raises(CacheConnectionError, match="PING failed"):
                await client.ping()
