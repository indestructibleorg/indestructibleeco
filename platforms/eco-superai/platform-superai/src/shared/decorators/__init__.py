"""Shared decorators — retry, cache, timing, validation."""
from __future__ import annotations

import asyncio
import functools
import time
from typing import Any, Callable, TypeVar

import structlog

logger = structlog.get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0, exceptions: tuple = (Exception,)):
    """Retry decorator with exponential backoff for async functions."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            current_delay = delay
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(
                            "retry_attempt",
                            func=func.__name__,
                            attempt=attempt,
                            max_attempts=max_attempts,
                            delay=current_delay,
                            error=str(e),
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
            raise last_exception  # type: ignore[misc]

        return wrapper  # type: ignore[return-value]

    return decorator


def timed(func: F) -> F:
    """Log execution time for async functions."""

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            elapsed = (time.perf_counter() - start) * 1000
            logger.info("function_timed", func=func.__name__, elapsed_ms=round(elapsed, 2))
            return result
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error("function_timed_error", func=func.__name__, elapsed_ms=round(elapsed, 2), error=str(e))
            raise

    return wrapper  # type: ignore[return-value]


def timed_sync(func: F) -> F:
    """Log execution time for sync functions."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            elapsed = (time.perf_counter() - start) * 1000
            logger.info("function_timed", func=func.__name__, elapsed_ms=round(elapsed, 2))
            return result
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error("function_timed_error", func=func.__name__, elapsed_ms=round(elapsed, 2), error=str(e))
            raise

    return wrapper  # type: ignore[return-value]


def cached(ttl_seconds: int = 300):
    """Simple in-memory TTL cache for async functions."""

    def decorator(func: F) -> F:
        _cache: dict[str, tuple[float, Any]] = {}

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = f"{func.__name__}:{args}:{sorted(kwargs.items())}"
            now = time.time()

            if key in _cache:
                cached_time, cached_value = _cache[key]
                if now - cached_time < ttl_seconds:
                    logger.debug("cache_hit", func=func.__name__)
                    return cached_value

            result = await func(*args, **kwargs)
            _cache[key] = (now, result)

            # Evict expired entries
            expired = [k for k, (t, _) in _cache.items() if now - t >= ttl_seconds]
            for k in expired:
                del _cache[k]

            return result

        wrapper.cache_clear = lambda: _cache.clear()  # type: ignore[attr-defined]
        return wrapper  # type: ignore[return-value]

    return decorator


def validate_not_none(*param_names: str):
    """Validate that specified parameters are not None."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            import inspect
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            for name in param_names:
                if name in bound.arguments and bound.arguments[name] is None:
                    raise ValueError(f"Parameter '{name}' must not be None")

            return await func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


__all__ = ["retry", "timed", "timed_sync", "cached", "validate_not_none"]