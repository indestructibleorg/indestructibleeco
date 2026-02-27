"""Cover k8s_client.py line 431: Deployment patch on 409 conflict."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_client():
    """Return a K8sClient with _available=True and a mocked _client."""
    from src.infrastructure.external.k8s_client import K8sClient

    client = K8sClient.__new__(K8sClient)
    client._available = True
    client._in_cluster = False
    mock_k8s = MagicMock()
    client._client = mock_k8s
    return client, mock_k8s


async def _run_to_thread(fn):
    """Execute a sync function in a thread (mirrors asyncio.to_thread)."""
    import concurrent.futures

    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, fn)


class TestK8sDeploymentPatch409:
    """Cover line 431: apply_manifest Deployment patch on 409 conflict."""

    @pytest.mark.asyncio
    async def test_apply_manifest_deployment_patch_on_409(self):
        """Line 431 – Deployment is patched when 409 conflict occurs."""
        from src.infrastructure.external.k8s_client import K8sClient, ApiException

        client, mock_k8s = _make_client()

        apps_api = MagicMock()
        mock_k8s.AppsV1Api.return_value = apps_api

        # create raises 409, patch succeeds
        exc_409 = ApiException(status=409, reason="Conflict")
        patch_result = MagicMock()
        patch_result.metadata.name = "my-deployment"
        patch_result.metadata.namespace = "default"

        apps_api.create_namespaced_deployment.side_effect = exc_409
        apps_api.patch_namespaced_deployment.return_value = patch_result

        manifest = {
            "kind": "Deployment",
            "metadata": {"name": "my-deployment", "namespace": "default"},
        }

        result = await client.apply_manifest(manifest)

        assert result["action"] == "patched"
        assert result["kind"] == "Deployment"
        assert result["name"] == "my-deployment"
        apps_api.patch_namespaced_deployment.assert_called_once()
