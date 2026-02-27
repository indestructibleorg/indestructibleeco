"""Targeted tests for remaining uncovered lines in presentation/api/middleware/__init__.py.

Covers:
- TokenBucket.retry_after (lines 48-53): both branches (tokens >= 1.0 and tokens < 1.0)
- RateLimitMiddleware._get_client_ip (lines 87-94): X-Forwarded-For, X-Real-IP, direct client
- RateLimitMiddleware._maybe_cleanup (lines 96-113): stale bucket eviction
- RateLimitMiddleware.dispatch (lines 115-145): health path skip, rate limit exceeded 429
"""
from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_app_with_rate_limit(rate: float = 10.0, burst: int = 5) -> FastAPI:
    """Create a minimal FastAPI app with RateLimitMiddleware attached."""
    from src.presentation.api.middleware import RateLimitMiddleware

    app = FastAPI(default_response_class=ORJSONResponse)

    @app.get("/api/v1/test")
    async def test_endpoint():
        return {"ok": True}

    @app.get("/api/v1/health")
    async def health_endpoint():
        return {"status": "healthy"}

    app.add_middleware(RateLimitMiddleware, rate=rate, burst=burst)
    return app


# ---------------------------------------------------------------------------
# TokenBucket.retry_after (lines 48-53)
# ---------------------------------------------------------------------------

class TestTokenBucketRetryAfter:
    """Cover lines 48-53: retry_after property."""

    def test_retry_after_returns_zero_when_tokens_full(self):
        """Line 52 – retry_after returns 0.0 when tokens >= 1.0."""
        import src.presentation.api.middleware as mw_mod
        TokenBucket = mw_mod._TokenBucket

        bucket = TokenBucket(rate=10.0, burst=5)
        # Bucket starts full (burst=5, tokens=5.0)
        assert bucket.retry_after == 0.0

    def test_retry_after_returns_positive_when_tokens_depleted(self):
        """Line 53 – retry_after returns positive seconds when tokens < 1.0."""
        import src.presentation.api.middleware as mw_mod
        TokenBucket = mw_mod._TokenBucket

        bucket = TokenBucket(rate=1.0, burst=1)
        # Consume the token so bucket is empty
        asyncio.get_event_loop().run_until_complete(bucket.consume())
        # Now tokens < 1.0, retry_after should be positive
        retry = bucket.retry_after
        assert retry > 0.0


# ---------------------------------------------------------------------------
# RateLimitMiddleware._get_client_ip (lines 87-94)
# ---------------------------------------------------------------------------

class TestGetClientIp:
    """Cover lines 87-94: _get_client_ip extracts IP from various headers."""

    def _make_middleware(self):
        from src.presentation.api.middleware import RateLimitMiddleware
        # Create a minimal ASGI app just to instantiate the middleware
        async def dummy_app(scope, receive, send):
            pass
        return RateLimitMiddleware(app=dummy_app, rate=10.0, burst=5)

    def test_get_client_ip_from_x_forwarded_for(self):
        """Line 89-90 – X-Forwarded-For header is used when present."""
        middleware = self._make_middleware()
        request = MagicMock()
        request.headers.get = lambda h, d=None: "1.2.3.4, 5.6.7.8" if h == "X-Forwarded-For" else d
        ip = middleware._get_client_ip(request)
        assert ip == "1.2.3.4"

    def test_get_client_ip_from_x_real_ip(self):
        """Lines 91-93 – X-Real-IP header is used when X-Forwarded-For is absent."""
        middleware = self._make_middleware()
        request = MagicMock()
        request.headers.get = lambda h, d=None: "9.8.7.6" if h == "X-Real-IP" else d
        ip = middleware._get_client_ip(request)
        assert ip == "9.8.7.6"

    def test_get_client_ip_falls_back_to_client_host(self):
        """Line 94 – falls back to request.client.host when no headers."""
        middleware = self._make_middleware()
        request = MagicMock()
        request.headers.get = lambda h, d=None: d  # no headers
        request.client.host = "10.0.0.1"
        ip = middleware._get_client_ip(request)
        assert ip == "10.0.0.1"

    def test_get_client_ip_returns_unknown_when_no_client(self):
        """Line 94 – returns 'unknown' when client is None."""
        middleware = self._make_middleware()
        request = MagicMock()
        request.headers.get = lambda h, d=None: d
        request.client = None
        ip = middleware._get_client_ip(request)
        assert ip == "unknown"


# ---------------------------------------------------------------------------
# RateLimitMiddleware._maybe_cleanup (lines 96-113)
# ---------------------------------------------------------------------------

class TestMaybeCleanup:
    """Cover lines 96-113: stale bucket eviction."""

    @pytest.mark.asyncio
    async def test_maybe_cleanup_evicts_stale_buckets(self):
        """Lines 104-113 – stale buckets (full tokens) are evicted."""
        import src.presentation.api.middleware as mw_mod
        RateLimitMiddleware = mw_mod.RateLimitMiddleware
        TokenBucket = mw_mod._TokenBucket

        async def dummy_app(scope, receive, send):
            pass

        middleware = RateLimitMiddleware(app=dummy_app, rate=10.0, burst=5)

        # Add a stale bucket (full tokens = not recently used)
        stale_bucket = TokenBucket(rate=10.0, burst=5)
        middleware._buckets["stale_ip"] = stale_bucket

        # Force cleanup by setting last_cleanup to far in the past
        middleware._last_cleanup = time.monotonic() - 400.0  # > 300s ago

        await middleware._maybe_cleanup()

        # Stale bucket should have been evicted
        assert "stale_ip" not in middleware._buckets

    @pytest.mark.asyncio
    async def test_maybe_cleanup_skips_when_interval_not_elapsed(self):
        """Line 99-100 – cleanup is skipped when interval has not elapsed."""
        import src.presentation.api.middleware as mw_mod
        RateLimitMiddleware = mw_mod.RateLimitMiddleware
        TokenBucket = mw_mod._TokenBucket

        async def dummy_app(scope, receive, send):
            pass

        middleware = RateLimitMiddleware(app=dummy_app, rate=10.0, burst=5)

        # Add a bucket
        middleware._buckets["some_ip"] = TokenBucket(rate=10.0, burst=5)
        # last_cleanup is recent (default)
        middleware._last_cleanup = time.monotonic()

        await middleware._maybe_cleanup()

        # Bucket should NOT have been evicted (cleanup skipped)
        assert "some_ip" in middleware._buckets


# ---------------------------------------------------------------------------
# RateLimitMiddleware.dispatch – health path skip (line 117-118)
# ---------------------------------------------------------------------------

class TestRateLimitDispatch:
    """Cover lines 117-118: health path is skipped by rate limiter."""

    def test_health_path_bypasses_rate_limit(self):
        """Lines 117-118 – /api/v1/health is not rate limited."""
        app = _make_app_with_rate_limit(rate=0.001, burst=0)  # very restrictive
        with TestClient(app, raise_server_exceptions=False) as client:
            # Health endpoint should always return 200 regardless of rate limit
            resp = client.get("/api/v1/health")
            assert resp.status_code == 200

    def test_rate_limit_exceeded_returns_429(self):
        """Lines 123-145 – rate limit exceeded returns 429 with Retry-After."""
        app = _make_app_with_rate_limit(rate=0.001, burst=1)
        with TestClient(app, raise_server_exceptions=False) as client:
            # First request consumes the burst token
            client.get("/api/v1/test")
            # Second request should be rate limited
            resp = client.get("/api/v1/test")
            assert resp.status_code == 429
            data = resp.json()
            assert data["error"]["code"] == "RATE_LIMITED"
            assert "Retry-After" in resp.headers


# ---------------------------------------------------------------------------
# Health route line 38 – correct patch target
# ---------------------------------------------------------------------------

class TestHealthRouteDetailedCorrectPatch:
    """Cover health.py line 38: successful DB execute."""

    def test_health_detailed_db_execute_success(self):
        """Line 38 – conn.execute is called successfully when DB is healthy."""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI
        from fastapi.responses import ORJSONResponse
        from src.presentation.exceptions.handlers import register_exception_handlers
        from src.presentation.api.routes import health

        app = FastAPI(default_response_class=ORJSONResponse)
        register_exception_handlers(app)
        app.include_router(health.router, prefix="/api/v1")

        conn_mock = AsyncMock()
        conn_mock.execute = AsyncMock(return_value=None)
        conn_mock.__aenter__ = AsyncMock(return_value=conn_mock)
        conn_mock.__aexit__ = AsyncMock(return_value=False)
        mock_engine = MagicMock()
        mock_engine.connect.return_value = conn_mock

        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)

        with (
            patch("src.infrastructure.persistence.database.engine", mock_engine),
            patch("src.infrastructure.cache.redis_client.get_redis", return_value=mock_redis),
        ):
            with TestClient(app) as client:
                resp = client.get("/api/v1/health/detailed")

        assert resp.status_code == 200
        data = resp.json()
        assert data["checks"]["database"]["status"] == "healthy"
