"""FastAPI middleware implementations — rate limiting, logging, security headers, CORS audit."""
from __future__ import annotations

import asyncio
import time
import uuid
from collections import defaultdict
from typing import Any, Callable

import structlog
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Token-bucket rate limiter
# ---------------------------------------------------------------------------

class _TokenBucket:
    """Thread-safe token bucket for a single client."""

    __slots__ = ("_rate", "_burst", "_tokens", "_last_refill", "_lock")

    def __init__(self, rate: float, burst: int) -> None:
        self._rate = rate          # tokens added per second
        self._burst = burst        # maximum bucket capacity
        self._tokens = float(burst)
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def consume(self) -> bool:
        """Try to consume one token.  Returns *True* if allowed."""
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_refill
            self._tokens = min(self._burst, self._tokens + elapsed * self._rate)
            self._last_refill = now

            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return True
            return False

    @property
    def retry_after(self) -> float:
        """Seconds until the next token becomes available."""
        if self._tokens >= 1.0:
            return 0.0
        return (1.0 - self._tokens) / self._rate


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-IP token-bucket rate limiter.

    Parameters
    ----------
    app:
        The ASGI application.
    rate:
        Tokens refilled per second (sustained request rate).  Default 10/s.
    burst:
        Maximum bucket size — peak burst capacity.  Default 20.
    """

    def __init__(
        self,
        app: ASGIApp,
        rate: float = 10.0,
        burst: int = 20,
    ) -> None:
        super().__init__(app)
        self._rate = rate
        self._burst = burst
        self._buckets: dict[str, _TokenBucket] = defaultdict(
            lambda: _TokenBucket(self._rate, self._burst)
        )
        # Periodic cleanup tracking
        self._last_cleanup = time.monotonic()
        self._cleanup_interval = 300.0  # seconds
        self._cleanup_lock = asyncio.Lock()

    def _get_client_ip(self, request: Request) -> str:
        """Extract the real client IP, respecting reverse-proxy headers."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        x_real_ip = request.headers.get("X-Real-IP")
        if x_real_ip:
            return x_real_ip.strip()
        return request.client.host if request.client else "unknown"

    async def _maybe_cleanup(self) -> None:
        """Remove stale buckets to prevent unbounded memory growth."""
        now = time.monotonic()
        if now - self._last_cleanup < self._cleanup_interval:
            return
        async with self._cleanup_lock:
            if now - self._last_cleanup < self._cleanup_interval:
                return  # pragma: no cover  # double-check after acquiring lock
            stale_keys: list[str] = []
            for ip, bucket in self._buckets.items():
                # If the bucket is full (no recent activity), it can be evicted
                if bucket._tokens >= self._burst:  # noqa: SLF001
                    stale_keys.append(ip)
            for key in stale_keys:
                del self._buckets[key]
            self._last_cleanup = now
            if stale_keys:
                logger.debug("rate_limit_cleanup", evicted=len(stale_keys))

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health/metrics endpoints
        if request.url.path in ("/api/v1/health", "/metrics", "/api/v1/healthz"):
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        bucket = self._buckets[client_ip]

        if not await bucket.consume():
            retry_after = max(1, int(bucket.retry_after) + 1)
            logger.warning(
                "rate_limit_exceeded",
                client_ip=client_ip,
                path=request.url.path,
                method=request.method,
                retry_after=retry_after,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMITED",
                        "message": f"Rate limit exceeded. Max {self._burst} burst / {self._rate:.0f} per second sustained.",
                    }
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self._burst),
                    "X-RateLimit-Remaining": "0",
                },
            )

        # Background cleanup
        await self._maybe_cleanup()

        response = await call_next(request)

        # Attach rate-limit headers
        remaining = max(0, int(bucket._tokens))  # noqa: SLF001
        response.headers["X-RateLimit-Limit"] = str(self._burst)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response


# ---------------------------------------------------------------------------
# Request logging
# ---------------------------------------------------------------------------

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every HTTP request with method, path, status code, and duration.

    Uses *structlog* context variables so downstream loggers automatically
    include the correlation ``request_id``.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        client_ip = self._get_client_ip(request)
        start = time.perf_counter()

        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=client_ip,
        )

        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - start) * 1000, 2)

            log_fn = logger.info if response.status_code < 400 else logger.warning
            log_fn(
                "request_completed",
                status=response.status_code,
                duration_ms=duration_ms,
                content_length=response.headers.get("content-length"),
            )

            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{duration_ms / 1000:.4f}"
            return response

        except Exception as exc:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.error(
                "request_failed",
                error=str(exc),
                error_type=type(exc).__name__,
                duration_ms=duration_ms,
            )
            raise
        finally:
            structlog.contextvars.unbind_contextvars(
                "request_id", "method", "path", "client_ip"
            )

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"


# ---------------------------------------------------------------------------
# Security headers
# ---------------------------------------------------------------------------

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Inject best-practice security headers on every response.

    Headers applied:
    - ``X-Content-Type-Options: nosniff``
    - ``X-Frame-Options: DENY``
    - ``X-XSS-Protection: 1; mode=block``
    - ``Strict-Transport-Security: max-age=63072000; includeSubDomains; preload``
    - ``Content-Security-Policy: default-src 'self'``
    - ``Referrer-Policy: strict-origin-when-cross-origin``
    - ``Permissions-Policy: geolocation=(), camera=(), microphone=()``
    - ``Cache-Control: no-store`` (for API responses)
    """

    # Configurable defaults — callers can override via constructor kwargs.
    _DEFAULT_HEADERS: dict[str, str] = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
        "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), camera=(), microphone=()",
        "Cache-Control": "no-store",
    }

    def __init__(self, app: ASGIApp, **overrides: str) -> None:
        super().__init__(app)
        self._headers = {**self._DEFAULT_HEADERS, **overrides}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        for name, value in self._headers.items():
            response.headers[name] = value
        return response


# ---------------------------------------------------------------------------
# CORS audit logging
# ---------------------------------------------------------------------------

class CORSAuditMiddleware(BaseHTTPMiddleware):
    """Log CORS-related requests for audit and compliance.

    Records:
    - All preflight (OPTIONS) requests with their ``Origin`` and
      ``Access-Control-Request-Method`` headers.
    - All cross-origin requests (where ``Origin`` is present) along with
      the response's CORS allow headers.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        origin = request.headers.get("origin")

        # Fast path — not a cross-origin request
        if not origin:
            return await call_next(request)

        client_ip = self._get_client_ip(request)

        # Preflight
        if request.method == "OPTIONS":
            requested_method = request.headers.get(
                "Access-Control-Request-Method", ""
            )
            requested_headers = request.headers.get(
                "Access-Control-Request-Headers", ""
            )
            logger.info(
                "cors_preflight",
                origin=origin,
                requested_method=requested_method,
                requested_headers=requested_headers,
                path=request.url.path,
                client_ip=client_ip,
            )

        response = await call_next(request)

        # Audit log for every cross-origin request
        allow_origin = response.headers.get("Access-Control-Allow-Origin", "")
        logger.info(
            "cors_request",
            origin=origin,
            allow_origin=allow_origin,
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            client_ip=client_ip,
            is_preflight=request.method == "OPTIONS",
        )

        return response

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"


__all__ = [
    "RateLimitMiddleware",
    "RequestLoggingMiddleware",
    "SecurityHeadersMiddleware",
    "CORSAuditMiddleware",
]
