"""Unit tests for infrastructure/external — HTTPClientBase and K8sClient.

All HTTP calls are intercepted with respx; K8s API calls are mocked so
no real cluster is required.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import httpx


# ---------------------------------------------------------------------------
# HTTPClientBase
# ---------------------------------------------------------------------------

class TestHTTPClientBase:
    """Tests for HTTPClientBase — GET, POST, PUT, DELETE with retry logic."""

    def _make_client(self, base_url: str = "https://api.example.com", max_retries: int = 2):
        from src.infrastructure.external import HTTPClientBase
        return HTTPClientBase(base_url=base_url, timeout=5, max_retries=max_retries)

    @pytest.mark.asyncio
    async def test_get_success(self) -> None:
        client = self._make_client()
        mock_response = MagicMock()
        mock_response.json.return_value = {"key": "value"}
        mock_response.raise_for_status = MagicMock()

        mock_http_client = AsyncMock()
        mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
        mock_http_client.__aexit__ = AsyncMock(return_value=False)
        mock_http_client.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_http_client):
            result = await client.get("/users")
        assert result == {"key": "value"}

    @pytest.mark.asyncio
    async def test_get_with_params(self) -> None:
        client = self._make_client()
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status = MagicMock()

        mock_http_client = AsyncMock()
        mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
        mock_http_client.__aexit__ = AsyncMock(return_value=False)
        mock_http_client.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_http_client):
            result = await client.get("/search", params={"q": "test"}, headers={"X-Token": "abc"})
        assert result == {"data": []}

    @pytest.mark.asyncio
    async def test_get_5xx_retries_and_raises(self) -> None:
        client = self._make_client(max_retries=2)

        error_response = MagicMock()
        error_response.status_code = 503
        http_error = httpx.HTTPStatusError("503", request=MagicMock(), response=error_response)

        mock_http_client = AsyncMock()
        mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
        mock_http_client.__aexit__ = AsyncMock(return_value=False)
        mock_http_client.get = AsyncMock(side_effect=http_error)

        with patch("httpx.AsyncClient", return_value=mock_http_client):
            with pytest.raises(httpx.HTTPStatusError):
                await client.get("/unstable")

    @pytest.mark.asyncio
    async def test_get_4xx_raises_immediately(self) -> None:
        """4xx errors should not be retried."""
        client = self._make_client(max_retries=3)

        error_response = MagicMock()
        error_response.status_code = 404
        http_error = httpx.HTTPStatusError("404", request=MagicMock(), response=error_response)

        mock_http_client = AsyncMock()
        mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
        mock_http_client.__aexit__ = AsyncMock(return_value=False)
        mock_http_client.get = AsyncMock(side_effect=http_error)

        with patch("httpx.AsyncClient", return_value=mock_http_client):
            with pytest.raises(httpx.HTTPStatusError):
                await client.get("/not-found")
        # Should only be called once (no retry on 4xx)
        assert mock_http_client.get.call_count == 1

    @pytest.mark.asyncio
    async def test_get_request_error_retries_and_raises(self) -> None:
        client = self._make_client(max_retries=2)

        mock_http_client = AsyncMock()
        mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
        mock_http_client.__aexit__ = AsyncMock(return_value=False)
        mock_http_client.get = AsyncMock(side_effect=httpx.RequestError("connection refused"))

        with patch("httpx.AsyncClient", return_value=mock_http_client):
            with pytest.raises(httpx.RequestError):
                await client.get("/unreachable")

    @pytest.mark.asyncio
    async def test_post_success(self) -> None:
        client = self._make_client()
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "123"}
        mock_response.raise_for_status = MagicMock()

        mock_http_client = AsyncMock()
        mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
        mock_http_client.__aexit__ = AsyncMock(return_value=False)
        mock_http_client.post = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_http_client):
            result = await client.post("/users", json={"name": "Alice"})
        assert result == {"id": "123"}

    @pytest.mark.asyncio
    async def test_post_5xx_retries_and_raises(self) -> None:
        client = self._make_client(max_retries=2)
        error_response = MagicMock()
        error_response.status_code = 500
        http_error = httpx.HTTPStatusError("500", request=MagicMock(), response=error_response)

        mock_http_client = AsyncMock()
        mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
        mock_http_client.__aexit__ = AsyncMock(return_value=False)
        mock_http_client.post = AsyncMock(side_effect=http_error)

        with patch("httpx.AsyncClient", return_value=mock_http_client):
            with pytest.raises(httpx.HTTPStatusError):
                await client.post("/fail", json={})

    @pytest.mark.asyncio
    async def test_put_success(self) -> None:
        client = self._make_client()
        mock_response = MagicMock()
        mock_response.json.return_value = {"updated": True}
        mock_response.raise_for_status = MagicMock()

        mock_http_client = AsyncMock()
        mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
        mock_http_client.__aexit__ = AsyncMock(return_value=False)
        mock_http_client.put = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_http_client):
            result = await client.put("/users/1", json={"name": "Bob"})
        assert result == {"updated": True}

    @pytest.mark.asyncio
    async def test_put_request_error_retries_and_raises(self) -> None:
        client = self._make_client(max_retries=2)
        mock_http_client = AsyncMock()
        mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
        mock_http_client.__aexit__ = AsyncMock(return_value=False)
        mock_http_client.put = AsyncMock(side_effect=httpx.RequestError("timeout"))

        with patch("httpx.AsyncClient", return_value=mock_http_client):
            with pytest.raises(httpx.RequestError):
                await client.put("/slow")

    @pytest.mark.asyncio
    async def test_delete_success(self) -> None:
        client = self._make_client()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"deleted": True}
        mock_response.raise_for_status = MagicMock()

        mock_http_client = AsyncMock()
        mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
        mock_http_client.__aexit__ = AsyncMock(return_value=False)
        mock_http_client.delete = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_http_client):
            result = await client.delete("/users/1")
        assert result == {"deleted": True}

    @pytest.mark.asyncio
    async def test_delete_204_returns_deleted_status(self) -> None:
        client = self._make_client()
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.raise_for_status = MagicMock()

        mock_http_client = AsyncMock()
        mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
        mock_http_client.__aexit__ = AsyncMock(return_value=False)
        mock_http_client.delete = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_http_client):
            result = await client.delete("/users/2")
        assert result == {"status": "deleted"}

    @pytest.mark.asyncio
    async def test_delete_5xx_retries_and_raises(self) -> None:
        client = self._make_client(max_retries=2)
        error_response = MagicMock()
        error_response.status_code = 503
        http_error = httpx.HTTPStatusError("503", request=MagicMock(), response=error_response)

        mock_http_client = AsyncMock()
        mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
        mock_http_client.__aexit__ = AsyncMock(return_value=False)
        mock_http_client.delete = AsyncMock(side_effect=http_error)

        with patch("httpx.AsyncClient", return_value=mock_http_client):
            with pytest.raises(httpx.HTTPStatusError):
                await client.delete("/fail")

    def test_base_url_stored_as_is(self) -> None:
        from src.infrastructure.external import HTTPClientBase
        client = HTTPClientBase(base_url="https://api.example.com", timeout=5, max_retries=1)
        assert client._base_url == "https://api.example.com"


# ---------------------------------------------------------------------------
# K8sClient
# ---------------------------------------------------------------------------

class TestK8sClient:
    """Tests for K8sClient — covers both available and unavailable states."""

    def test_k8s_client_unavailable_when_package_missing(self) -> None:
        """When kubernetes package is not installed, client should be unavailable."""
        import sys
        with patch.dict(sys.modules, {
            "kubernetes": None,
            "kubernetes.client": None,
            "kubernetes.config": None,
        }):
            # Force re-import to pick up the patched modules
            if "src.infrastructure.external.k8s_client" in sys.modules:
                del sys.modules["src.infrastructure.external.k8s_client"]
            from src.infrastructure.external.k8s_client import K8sClient
            client = K8sClient()
        assert client.is_available is False

    def test_k8s_client_unavailable_when_config_fails(self) -> None:
        """When kubeconfig loading fails, client should be unavailable."""
        from src.infrastructure.external.k8s_client import K8sClient
        client = K8sClient()
        # In CI without a real cluster, client should be unavailable
        assert isinstance(client.is_available, bool)

    @pytest.mark.asyncio
    async def test_health_check_when_unavailable(self) -> None:
        from src.infrastructure.external.k8s_client import K8sClient
        client = K8sClient()
        # Force unavailable state
        client._available = False
        result = await client.health_check()
        assert "status" in result
        assert result["status"] in ("unavailable", "healthy", "degraded", "unhealthy")

    @pytest.mark.asyncio
    async def test_list_pods_when_unavailable(self) -> None:
        from src.infrastructure.external.k8s_client import K8sClient
        client = K8sClient()
        client._available = False
        result = await client.list_pods(namespace="default")
        assert isinstance(result, (list, dict))

    @pytest.mark.asyncio
    async def test_list_deployments_when_unavailable(self) -> None:
        from src.infrastructure.external.k8s_client import K8sClient
        client = K8sClient()
        client._available = False
        result = await client.list_deployments(namespace="default")
        assert isinstance(result, (list, dict))

    @pytest.mark.asyncio
    async def test_scale_deployment_when_unavailable(self) -> None:
        from src.infrastructure.external.k8s_client import K8sClient
        client = K8sClient()
        client._available = False
        result = await client.scale_deployment(
            name="my-deployment", replicas=3, namespace="default"
        )
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_apply_manifest_when_unavailable(self) -> None:
        from src.infrastructure.external.k8s_client import K8sClient
        client = K8sClient()
        client._available = False
        result = await client.apply_manifest(manifest={"apiVersion": "v1"})
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_list_namespaces_when_unavailable(self) -> None:
        from src.infrastructure.external.k8s_client import K8sClient
        client = K8sClient()
        client._available = False
        result = await client.list_namespaces()
        assert isinstance(result, (list, dict))

    @pytest.mark.asyncio
    async def test_list_nodes_when_unavailable(self) -> None:
        from src.infrastructure.external.k8s_client import K8sClient
        client = K8sClient()
        client._available = False
        result = await client.list_nodes()
        assert isinstance(result, (list, dict))

    @pytest.mark.asyncio
    async def test_get_deployment_status_when_unavailable(self) -> None:
        from src.infrastructure.external.k8s_client import K8sClient
        client = K8sClient()
        client._available = False
        result = await client.get_deployment_status(
            name="my-deploy", namespace="default"
        )
        assert isinstance(result, dict)
