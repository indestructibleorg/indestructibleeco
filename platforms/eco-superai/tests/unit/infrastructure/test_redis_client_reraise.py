"""Tests for CacheConnectionError re-raise paths in redis_client.py.

Covers lines: 167, 177, 187, 209, 233, 255, 284, 302.
These are all 'except CacheConnectionError: raise' branches where the
underlying redis call itself raises a CacheConnectionError.
Also covers line 284: get_or_set with a plain (non-callable) factory value.
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.shared.exceptions import CacheConnectionError


# ---------------------------------------------------------------------------
# delete – CacheConnectionError re-raise (line 167)
# ---------------------------------------------------------------------------

class TestDeleteReraiseCacheError:
    @pytest.mark.asyncio
    async def test_delete_reraises_cache_connection_error(self):
        """Line 167 – CacheConnectionError from get_redis is re-raised."""
        from src.infrastructure.cache.redis_client import RedisClient

        with patch(
            "src.infrastructure.cache.redis_client.get_redis",
            side_effect=CacheConnectionError("pool error"),
        ):
            client = RedisClient()
            with pytest.raises(CacheConnectionError, match="pool error"):
                await client.delete("key")


# ---------------------------------------------------------------------------
# exists – CacheConnectionError re-raise (line 177)
# ---------------------------------------------------------------------------

class TestExistsReraiseCacheError:
    @pytest.mark.asyncio
    async def test_exists_reraises_cache_connection_error(self):
        """Line 177 – CacheConnectionError from get_redis is re-raised."""
        from src.infrastructure.cache.redis_client import RedisClient

        with patch(
            "src.infrastructure.cache.redis_client.get_redis",
            side_effect=CacheConnectionError("pool error"),
        ):
            client = RedisClient()
            with pytest.raises(CacheConnectionError, match="pool error"):
                await client.exists("key")


# ---------------------------------------------------------------------------
# increment – CacheConnectionError re-raise (line 187)
# ---------------------------------------------------------------------------

class TestIncrementReraiseCacheError:
    @pytest.mark.asyncio
    async def test_increment_reraises_cache_connection_error(self):
        """Line 187 – CacheConnectionError from get_redis is re-raised."""
        from src.infrastructure.cache.redis_client import RedisClient

        with patch(
            "src.infrastructure.cache.redis_client.get_redis",
            side_effect=CacheConnectionError("pool error"),
        ):
            client = RedisClient()
            with pytest.raises(CacheConnectionError, match="pool error"):
                await client.increment("counter")


# ---------------------------------------------------------------------------
# get_many – CacheConnectionError re-raise (line 209)
# ---------------------------------------------------------------------------

class TestGetManyReraiseCacheError:
    @pytest.mark.asyncio
    async def test_get_many_reraises_cache_connection_error(self):
        """Line 209 – CacheConnectionError from get_redis is re-raised."""
        from src.infrastructure.cache.redis_client import RedisClient

        with patch(
            "src.infrastructure.cache.redis_client.get_redis",
            side_effect=CacheConnectionError("pool error"),
        ):
            client = RedisClient()
            with pytest.raises(CacheConnectionError, match="pool error"):
                await client.get_many(["k1", "k2"])


# ---------------------------------------------------------------------------
# set_many – CacheConnectionError re-raise (line 233)
# ---------------------------------------------------------------------------

class TestSetManyReraiseCacheError:
    @pytest.mark.asyncio
    async def test_set_many_reraises_cache_connection_error(self):
        """Line 233 – CacheConnectionError from get_redis is re-raised."""
        from src.infrastructure.cache.redis_client import RedisClient

        with patch(
            "src.infrastructure.cache.redis_client.get_redis",
            side_effect=CacheConnectionError("pool error"),
        ):
            client = RedisClient()
            with pytest.raises(CacheConnectionError, match="pool error"):
                await client.set_many({"k1": "v1"})


# ---------------------------------------------------------------------------
# flush_pattern – CacheConnectionError re-raise (line 255)
# ---------------------------------------------------------------------------

class TestFlushPatternReraiseCacheError:
    @pytest.mark.asyncio
    async def test_flush_pattern_reraises_cache_connection_error(self):
        """Line 255 – CacheConnectionError from get_redis is re-raised."""
        from src.infrastructure.cache.redis_client import RedisClient

        with patch(
            "src.infrastructure.cache.redis_client.get_redis",
            side_effect=CacheConnectionError("pool error"),
        ):
            client = RedisClient()
            with pytest.raises(CacheConnectionError, match="pool error"):
                await client.flush_pattern("prefix:*")


# ---------------------------------------------------------------------------
# get_or_set – plain value factory (line 284)
# ---------------------------------------------------------------------------

class TestGetOrSetPlainValue:
    @pytest.mark.asyncio
    async def test_get_or_set_plain_value_on_miss(self):
        """Line 284 – plain (non-callable) factory value is stored and returned."""
        from src.infrastructure.cache.redis_client import RedisClient

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)  # cache miss
        mock_redis.set = AsyncMock(return_value=None)
        with patch(
            "src.infrastructure.cache.redis_client.get_redis",
            return_value=mock_redis,
        ):
            client = RedisClient()
            result = await client.get_or_set("key", "plain_value", ttl=60)
            assert result == "plain_value"


# ---------------------------------------------------------------------------
# ping – CacheConnectionError re-raise (line 302)
# ---------------------------------------------------------------------------

class TestPingReraiseCacheError:
    @pytest.mark.asyncio
    async def test_ping_reraises_cache_connection_error(self):
        """Line 302 – CacheConnectionError from get_redis is re-raised."""
        from src.infrastructure.cache.redis_client import RedisClient

        with patch(
            "src.infrastructure.cache.redis_client.get_redis",
            side_effect=CacheConnectionError("pool error"),
        ):
            client = RedisClient()
            with pytest.raises(CacheConnectionError, match="pool error"):
                await client.ping()
