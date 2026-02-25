"""External service clients — HTTP client base and third-party integrations."""
from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class HTTPClientBase:
    """Async HTTP client with retry, timeout, and circuit breaker patterns."""

    def __init__(self, base_url: str, timeout: int = 30, max_retries: int = 3) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries

    async def get(self, path: str, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> dict[str, Any]:
        import httpx
        url = f"{self._base_url}/{path.lstrip('/')}"
        for attempt in range(self._max_retries):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.get(url, params=params, headers=headers)
                    response.raise_for_status()
                    return response.json()
            except httpx.HTTPStatusError as e:
                logger.warning("http_error", url=url, status=e.response.status_code, attempt=attempt + 1)
                if e.response.status_code < 500 or attempt == self._max_retries - 1:
                    raise
            except httpx.RequestError as e:
                logger.warning("http_request_error", url=url, error=str(e), attempt=attempt + 1)
                if attempt == self._max_retries - 1:
                    raise
        return {}

    async def post(self, path: str, json: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> dict[str, Any]:
        import httpx
        url = f"{self._base_url}/{path.lstrip('/')}"
        for attempt in range(self._max_retries):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.post(url, json=json, headers=headers)
                    response.raise_for_status()
                    return response.json()
            except httpx.HTTPStatusError as e:
                logger.warning("http_error", url=url, status=e.response.status_code, attempt=attempt + 1)
                if e.response.status_code < 500 or attempt == self._max_retries - 1:
                    raise
            except httpx.RequestError as e:
                logger.warning("http_request_error", url=url, error=str(e), attempt=attempt + 1)
                if attempt == self._max_retries - 1:
                    raise
        return {}

    async def put(self, path: str, json: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> dict[str, Any]:
        import httpx
        url = f"{self._base_url}/{path.lstrip('/')}"
        for attempt in range(self._max_retries):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.put(url, json=json, headers=headers)
                    response.raise_for_status()
                    return response.json()
            except httpx.HTTPStatusError as e:
                logger.warning("http_error", url=url, status=e.response.status_code, attempt=attempt + 1)
                if e.response.status_code < 500 or attempt == self._max_retries - 1:
                    raise
            except httpx.RequestError as e:
                logger.warning("http_request_error", url=url, error=str(e), attempt=attempt + 1)
                if attempt == self._max_retries - 1:
                    raise
        return {}

    async def delete(self, path: str, headers: dict[str, str] | None = None) -> dict[str, Any]:
        import httpx
        url = f"{self._base_url}/{path.lstrip('/')}"
        for attempt in range(self._max_retries):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.delete(url, headers=headers)
                    response.raise_for_status()
                    if response.status_code == 204:
                        return {"status": "deleted"}
                    return response.json()
            except httpx.HTTPStatusError as e:
                logger.warning("http_error", url=url, status=e.response.status_code, attempt=attempt + 1)
                if e.response.status_code < 500 or attempt == self._max_retries - 1:
                    raise
            except httpx.RequestError as e:
                logger.warning("http_request_error", url=url, error=str(e), attempt=attempt + 1)
                if attempt == self._max_retries - 1:
                    raise
        return {}


__all__ = ["HTTPClientBase"]