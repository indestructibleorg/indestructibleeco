"""Unit tests for shared decorators."""
from __future__ import annotations

import pytest

from src.shared.decorators import retry, timed, cached


class TestRetryDecorator:
    @pytest.mark.asyncio
    async def test_retry_succeeds_first_try(self):
        call_count = 0

        @retry(max_attempts=3, delay=0.01)
        async def succeed():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = await succeed()
        assert result == "ok"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_succeeds_after_failures(self):
        call_count = 0

        @retry(max_attempts=3, delay=0.01)
        async def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("not yet")
            return "ok"

        result = await fail_then_succeed()
        assert result == "ok"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_exhausted_raises(self):
        @retry(max_attempts=2, delay=0.01)
        async def always_fail():
            raise RuntimeError("fail")

        with pytest.raises(RuntimeError, match="fail"):
            await always_fail()


class TestTimedDecorator:
    @pytest.mark.asyncio
    async def test_timed_returns_result(self):
        @timed
        async def compute():
            return 42

        assert await compute() == 42

    @pytest.mark.asyncio
    async def test_timed_propagates_error(self):
        @timed
        async def fail():
            raise ValueError("err")

        with pytest.raises(ValueError):
            await fail()


class TestCachedDecorator:
    @pytest.mark.asyncio
    async def test_cached_returns_same_result(self):
        call_count = 0

        @cached(ttl_seconds=60)
        async def expensive(x: int):
            nonlocal call_count
            call_count += 1
            return x * 2

        r1 = await expensive(5)
        r2 = await expensive(5)
        assert r1 == r2 == 10
        assert call_count == 1  # second call was cached

    @pytest.mark.asyncio
    async def test_cached_different_args(self):
        call_count = 0

        @cached(ttl_seconds=60)
        async def compute(x: int):
            nonlocal call_count
            call_count += 1
            return x

        await compute(1)
        await compute(2)
        assert call_count == 2  # different args = different cache keys