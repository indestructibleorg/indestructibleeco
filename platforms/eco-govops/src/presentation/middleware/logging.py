"""Structured logging middleware for the GovOps Platform API.

Emits a structured log event for every HTTP request containing the method,
path, response status code, and wall-clock duration in milliseconds.  The
log is bound with the request ID produced by :class:`RequestIdMiddleware`
when available.
"""
from __future__ import annotations

import time
from typing import Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger("govops.access")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Logs every request/response pair with timing and context.

    Fields emitted per event:

    * ``method`` -- HTTP verb (GET, POST, ...).
    * ``path`` -- Request path (without query string).
    * ``status_code`` -- HTTP response status code.
    * ``duration_ms`` -- Wall-clock time in milliseconds (2 decimal places).
    * ``request_id`` -- Correlation ID (if present on ``request.state``).
    * ``query`` -- Raw query string (omitted when empty).
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Response],  # type: ignore[override]
    ) -> Response:
        start = time.perf_counter()

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        request_id: str = getattr(request.state, "request_id", "")

        log_kwargs: dict[str, object] = {
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        }
        if request_id:
            log_kwargs["request_id"] = request_id
        if request.url.query:
            log_kwargs["query"] = str(request.url.query)

        if response.status_code >= 500:
            logger.error("http_request", **log_kwargs)
        elif response.status_code >= 400:
            logger.warning("http_request", **log_kwargs)
        else:
            logger.info("http_request", **log_kwargs)

        return response
