"""Redis client wrapper with connection pooling, graceful error handling,
and high-level caching utilities.

Usage::

    from src.infrastructure.cache.redis_client import get_redis, RedisClient

    # Low-level: get the raw ``redis.asyncio.Redis`` singleton
    redis = await get_redis()
    await redis.ping()

    # High-level: use the ``RedisClient`` wrapper
    client = RedisClient()
    await client.set("key", {"data": 1}, ttl=300)
    value = await client.get("key")

The module guarantees that only **one** connection pool is created per
process via the module-level singleton managed by :func:`get_redis`.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Sequence

import redis.asyncio as aioredis

from src.infrastructure.config import get_settings
from src.shared.exceptions import CacheConnectionError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_redis_pool: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Return the module-level async Redis singleton.

    On first call the connection pool is created using the application's
    :class:`~src.infrastructure.config.settings.RedisSettings`.  Subsequent
    calls return the same instance.

    Raises:
        CacheConnectionError: If the Redis server is unreachable at pool
            creation time.
    """
    global _redis_pool  # noqa: PLW0603
    if _redis_pool is None:
        try:
            settings = get_settings()
            _redis_pool = aioredis.from_url(
                settings.redis.url,
                password=settings.redis.password or None,
                max_connections=settings.redis.max_connections,
                socket_timeout=settings.redis.socket_timeout,
                socket_connect_timeout=settings.redis.socket_connect_timeout,
                retry_on_timeout=settings.redis.retry_on_timeout,
                decode_responses=settings.redis.decode_responses,
            )
        except Exception as exc:
            raise CacheConnectionError(str(exc)) from exc
    return _redis_pool


async def close_redis() -> None:
    """Gracefully close the Redis connection pool.

    Safe to call even if the pool was never opened.
    """
    global _redis_pool  # noqa: PLW0603
    if _redis_pool is not None:
        await _redis_pool.aclose()  # type: ignore[union-attr]
        _redis_pool = None


# ---------------------------------------------------------------------------
# RedisClient wrapper
# ---------------------------------------------------------------------------

class RedisClient:
    """High-level async Redis client with automatic JSON serialisation,
    key prefixing, and graceful error handling.

    All public methods translate ``redis`` exceptions into
    :class:`~src.shared.exceptions.CacheConnectionError` so that the
    presentation layer can return an appropriate ``503`` response.
    """

    def __init__(
        self,
        prefix: str = "superai",
        default_ttl: int = 3600,
    ) -> None:
        self._prefix = prefix
        self._default_ttl = default_ttl

    # -- helpers ----------------------------------------------------------

    def _key(self, key: str) -> str:
        """Build the full Redis key with the configured prefix."""
        return f"{self._prefix}:{key}"

    @staticmethod
    def _serialize(value: Any) -> str:
        """Serialise *value* to a JSON string (pass-through for ``str``)."""
        if isinstance(value, str):
            return value
        return json.dumps(value, default=str)

    @staticmethod
    def _deserialize(raw: str | None) -> Any:
        """Attempt JSON deserialisation; fall back to the raw string."""
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return raw

    # -- single-key operations --------------------------------------------

    async def get(self, key: str) -> Any | None:
        """Retrieve a value by key. Returns ``None`` on cache miss."""
        try:
            redis = await get_redis()
            raw = await redis.get(self._key(key))
            return self._deserialize(raw)
        except CacheConnectionError:
            raise
        except Exception as exc:
            raise CacheConnectionError(f"GET {key}: {exc}") from exc

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> None:
        """Store a value with an optional TTL (seconds).

        If *ttl* is ``None`` the instance's ``default_ttl`` is used.
        """
        try:
            redis = await get_redis()
            serialised = self._serialize(value)
            await redis.set(
                self._key(key),
                serialised,
                ex=ttl if ttl is not None else self._default_ttl,
            )
        except CacheConnectionError:
            raise
        except Exception as exc:
            raise CacheConnectionError(f"SET {key}: {exc}") from exc

    async def delete(self, key: str) -> bool:
        """Delete a single key. Returns ``True`` if the key existed."""
        try:
            redis = await get_redis()
            removed = await redis.delete(self._key(key))
            return bool(removed)
        except CacheConnectionError:
            raise
        except Exception as exc:
            raise CacheConnectionError(f"DELETE {key}: {exc}") from exc

    async def exists(self, key: str) -> bool:
        """Return ``True`` if *key* is present in the cache."""
        try:
            redis = await get_redis()
            return bool(await redis.exists(self._key(key)))
        except CacheConnectionError:
            raise
        except Exception as exc:
            raise CacheConnectionError(f"EXISTS {key}: {exc}") from exc

    async def increment(self, key: str, amount: int = 1) -> int:
        """Atomically increment a counter and return the new value."""
        try:
            redis = await get_redis()
            return await redis.incrby(self._key(key), amount)
        except CacheConnectionError:
            raise
        except Exception as exc:
            raise CacheConnectionError(f"INCR {key}: {exc}") from exc

    # -- bulk operations --------------------------------------------------

    async def get_many(self, keys: Sequence[str]) -> dict[str, Any]:
        """Retrieve multiple keys in a single round-trip (``MGET``).

        Returns a dict mapping each requested key to its deserialised value
        (or ``None`` for misses).
        """
        if not keys:
            return {}
        try:
            redis = await get_redis()
            prefixed = [self._key(k) for k in keys]
            raw_values = await redis.mget(prefixed)
            return {
                k: self._deserialize(v) for k, v in zip(keys, raw_values)
            }
        except CacheConnectionError:
            raise
        except Exception as exc:
            raise CacheConnectionError(f"MGET: {exc}") from exc

    async def set_many(
        self,
        mapping: dict[str, Any],
        ttl: int | None = None,
    ) -> None:
        """Store multiple key-value pairs.

        Uses a pipeline for atomicity and reduced round-trips.  Each key
        receives the same TTL (defaulting to ``default_ttl``).
        """
        if not mapping:
            return
        effective_ttl = ttl if ttl is not None else self._default_ttl
        try:
            redis = await get_redis()
            pipe = redis.pipeline(transaction=False)
            for key, value in mapping.items():
                pipe.set(self._key(key), self._serialize(value), ex=effective_ttl)
            await pipe.execute()
        except CacheConnectionError:
            raise
        except Exception as exc:
            raise CacheConnectionError(f"MSET: {exc}") from exc

    # -- pattern operations -----------------------------------------------

    async def flush_pattern(self, pattern: str) -> int:
        """Delete all keys matching a glob *pattern*.

        Uses ``SCAN`` internally to avoid blocking the server with a
        ``KEYS`` call on large key-spaces.

        Returns the number of keys deleted.
        """
        try:
            redis = await get_redis()
            count = 0
            async for key in redis.scan_iter(match=self._key(pattern)):
                await redis.delete(key)
                count += 1
            return count
        except CacheConnectionError:
            raise
        except Exception as exc:
            raise CacheConnectionError(f"FLUSH_PATTERN {pattern}: {exc}") from exc

    # -- utility ----------------------------------------------------------

    async def get_or_set(
        self,
        key: str,
        factory: Any,
        ttl: int | None = None,
    ) -> Any:
        """Return the cached value for *key*, or compute and cache it.

        *factory* can be a plain value, a sync callable, or an async
        callable.  The factory is only invoked on cache miss.
        """
        cached = await self.get(key)
        if cached is not None:
            return cached

        if callable(factory):
            import asyncio

            if asyncio.iscoroutinefunction(factory):
                value = await factory()
            else:
                value = factory()
        else:
            value = factory

        await self.set(key, value, ttl)
        return value

    # -- health -----------------------------------------------------------

    async def ping(self) -> bool:
        """Health check: send a ``PING`` to Redis.

        Returns ``True`` on success or raises
        :class:`~src.shared.exceptions.CacheConnectionError` on failure.
        """
        try:
            redis = await get_redis()
            result = await redis.ping()
            return bool(result)
        except CacheConnectionError:
            raise
        except Exception as exc:
            raise CacheConnectionError(f"PING failed: {exc}") from exc


# ---------------------------------------------------------------------------
# Backward-compatible alias
# ---------------------------------------------------------------------------

CacheService = RedisClient

__all__ = ["RedisClient", "CacheService", "get_redis", "close_redis"]
