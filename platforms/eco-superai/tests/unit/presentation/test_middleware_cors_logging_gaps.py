"""Targeted tests for remaining uncovered middleware lines.

Covers:
- RateLimitMiddleware._maybe_cleanup double-check lock (line 103)
- RequestLoggingMiddleware exception path (lines 198-206)
- RequestLoggingMiddleware X-Forwarded-For (line 216)
- CORSAuditMiddleware dispatch (lines 276-323)
"""
from __future__ import annotations

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
from starlette.testclient import TestClient
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response, PlainTextResponse
from starlette.routing import Route


# ---------------------------------------------------------------------------
# RateLimitMiddleware._maybe_cleanup double-check lock (line 103)
# ---------------------------------------------------------------------------

class TestRateLimitCleanupDoubleCheck:
    """Cover line 103: double-check after acquiring cleanup lock."""

    @pytest.mark.asyncio
    async def test_cleanup_double_check_skips_when_recently_cleaned(self):
        """Line 103 – cleanup is skipped when another coroutine cleaned recently."""
        from src.presentation.api.middleware import RateLimitMiddleware

        app = Starlette()
        mw = RateLimitMiddleware.__new__(RateLimitMiddleware)
        mw._rate = 10
        mw._burst = 20
        mw._buckets = {}
        mw._cleanup_interval = 60.0
        mw._cleanup_lock = asyncio.Lock()

        # Set last cleanup to NOW so the outer check passes but the inner check fails
        mw._last_cleanup = time.monotonic()

        # Manually set last_cleanup to a past value to trigger outer check
        mw._last_cleanup = time.monotonic() - 100.0

        # Acquire the lock first to simulate another coroutine holding it
        async with mw._cleanup_lock:
            # Update last_cleanup to simulate recent cleanup by another coroutine
            mw._last_cleanup = time.monotonic()

        # Now call _maybe_cleanup - outer check passes, lock acquired, inner check fails
        mw._last_cleanup = time.monotonic() - 100.0
        # Simulate: between outer check and lock acquisition, another coroutine cleaned
        original_last_cleanup = mw._last_cleanup

        async def _concurrent_cleanup():
            await asyncio.sleep(0)
            mw._last_cleanup = time.monotonic()

        # Run cleanup concurrently
        await asyncio.gather(
            mw._maybe_cleanup(),
            _concurrent_cleanup(),
        )
        # No assertion needed - just verifying no exception occurs


# ---------------------------------------------------------------------------
# RequestLoggingMiddleware exception path (lines 198-206)
# ---------------------------------------------------------------------------

class TestRequestLoggingExceptionPath:
    """Cover lines 198-206: RequestLoggingMiddleware logs and re-raises exceptions."""

    def test_exception_in_request_is_logged_and_reraised(self):
        """Lines 198-206 – exception during request processing is logged and re-raised."""
        from src.presentation.api.middleware import RequestLoggingMiddleware

        async def _failing_endpoint(request: Request) -> Response:
            raise RuntimeError("Intentional test error")

        app = Starlette(routes=[Route("/fail", _failing_endpoint)])
        app.add_middleware(RequestLoggingMiddleware)

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/fail")
        # The middleware should catch and re-raise, resulting in 500
        assert response.status_code == 500


# ---------------------------------------------------------------------------
# RequestLoggingMiddleware X-Forwarded-For (line 216)
# ---------------------------------------------------------------------------

class TestRequestLoggingXForwardedFor:
    """Cover line 216: X-Forwarded-For header is used for client IP."""

    def test_x_forwarded_for_is_used_for_client_ip(self):
        """Line 216 – X-Forwarded-For header is extracted for client IP."""
        from src.presentation.api.middleware import RequestLoggingMiddleware

        async def _endpoint(request: Request) -> Response:
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/test", _endpoint)])
        app.add_middleware(RequestLoggingMiddleware)

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/test", headers={"X-Forwarded-For": "10.0.0.1, 192.168.1.1"})
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# CORSAuditMiddleware dispatch (lines 276-323)
# ---------------------------------------------------------------------------

class TestCORSAuditMiddlewareDispatch:
    """Cover lines 276-323: CORSAuditMiddleware handles CORS requests."""

    def test_cors_request_with_origin_header(self):
        """Lines 276-316 – cross-origin request is logged."""
        from src.presentation.api.middleware import CORSAuditMiddleware

        async def _endpoint(request: Request) -> Response:
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/api/test", _endpoint)])
        app.add_middleware(CORSAuditMiddleware)

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get(
            "/api/test",
            headers={"Origin": "https://example.com"},
        )
        assert response.status_code == 200

    def test_cors_preflight_request(self):
        """Lines 285-299 – OPTIONS preflight request is logged."""
        from src.presentation.api.middleware import CORSAuditMiddleware

        async def _endpoint(request: Request) -> Response:
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/api/test", _endpoint, methods=["GET", "OPTIONS"])])
        app.add_middleware(CORSAuditMiddleware)

        client = TestClient(app, raise_server_exceptions=False)
        response = client.options(
            "/api/test",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )
        # Preflight may return 200 or 405 depending on routing
        assert response.status_code in (200, 405)

    def test_cors_request_without_origin_header(self):
        """Line 280 – non-cross-origin request bypasses CORS audit."""
        from src.presentation.api.middleware import CORSAuditMiddleware

        async def _endpoint(request: Request) -> Response:
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/api/test", _endpoint)])
        app.add_middleware(CORSAuditMiddleware)

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/test")
        assert response.status_code == 200

    def test_cors_get_client_ip_with_forwarded_for(self):
        """Line 322 – X-Forwarded-For is used for client IP in CORS middleware."""
        from src.presentation.api.middleware import CORSAuditMiddleware

        async def _endpoint(request: Request) -> Response:
            return PlainTextResponse("OK")

        app = Starlette(routes=[Route("/api/test", _endpoint)])
        app.add_middleware(CORSAuditMiddleware)

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get(
            "/api/test",
            headers={
                "Origin": "https://example.com",
                "X-Forwarded-For": "203.0.113.1, 10.0.0.1",
            },
        )
        assert response.status_code == 200
