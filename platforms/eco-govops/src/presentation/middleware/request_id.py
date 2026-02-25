"""Request ID middleware for the GovOps Platform API.

Ensures every request and response carries an ``X-Request-ID`` header for
end-to-end tracing.  If the incoming request already contains the header its
value is preserved; otherwise a new UUID-4 is generated.
"""
from __future__ import annotations

import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_HEADER = "X-Request-ID"


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Injects a unique request identifier into every HTTP transaction.

    The identifier is:
    1. Read from the incoming ``X-Request-ID`` header if present.
    2. Generated as a UUID-4 string when the header is absent.
    3. Attached to the response headers so callers can correlate logs.
    4. Stored in ``request.state.request_id`` for downstream access.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Response],  # type: ignore[override]
    ) -> Response:
        request_id = request.headers.get(_HEADER) or str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers[_HEADER] = request_id
        return response
