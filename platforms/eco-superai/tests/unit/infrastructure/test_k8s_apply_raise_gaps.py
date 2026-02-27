"""Targeted tests for k8s_client apply_manifest 'raise' lines.

Covers:
- Line 437: Deployment ApiException non-409 re-raises
- Line 464: Service ApiException non-409 re-raises
- Line 491: ConfigMap ApiException non-409 re-raises
- Line 512: Namespace ApiException non-409 re-raises
- Line 536: Pod ApiException non-409 re-raises
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


def _make_client(available: bool = True):
    """Create a K8sClient with mocked kubernetes API."""
    from src.infrastructure.external.k8s_client import K8sClient
    client = K8sClient.__new__(K8sClient)
    client._available = available
    client._in_cluster = False
    if available:
        client._client = MagicMock()
    else:
        client._client = None
    return client


async def _run_to_thread(func, *args, **kwargs):
    """Execute to_thread calls synchronously in tests."""
    return func()


# ---------------------------------------------------------------------------
# Line 437: Deployment ApiException non-409 re-raises
# ---------------------------------------------------------------------------

class TestApplyManifestDeploymentNon409Raises:
    """Cover line 437: apply_manifest Deployment re-raises non-409 ApiException."""

    @pytest.mark.asyncio
    async def test_apply_manifest_deployment_non409_raises(self):
        """Line 437 – Deployment ApiException with non-409 status is re-raised."""
        from src.infrastructure.external.k8s_client import ApiException
        client = _make_client(available=True)
        client._client.AppsV1Api.return_value.create_namespaced_deployment.side_effect = ApiException(
            status=403, reason="Forbidden"
        )

        manifest = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {"name": "my-deploy", "namespace": "default"},
        }
        with patch("asyncio.to_thread", side_effect=_run_to_thread):
            result = await client.apply_manifest(manifest)

        # Should return error dict (from the outer except ApiException handler)
        assert "error" in result


# ---------------------------------------------------------------------------
# Line 464: Service ApiException non-409 re-raises
# ---------------------------------------------------------------------------

class TestApplyManifestServiceNon409Raises:
    """Cover line 464: apply_manifest Service re-raises non-409 ApiException."""

    @pytest.mark.asyncio
    async def test_apply_manifest_service_non409_raises(self):
        """Line 464 – Service ApiException with non-409 status is re-raised."""
        from src.infrastructure.external.k8s_client import ApiException
        client = _make_client(available=True)
        client._client.CoreV1Api.return_value.create_namespaced_service.side_effect = ApiException(
            status=403, reason="Forbidden"
        )

        manifest = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {"name": "my-service", "namespace": "default"},
        }
        with patch("asyncio.to_thread", side_effect=_run_to_thread):
            result = await client.apply_manifest(manifest)

        assert "error" in result


# ---------------------------------------------------------------------------
# Line 491: ConfigMap ApiException non-409 re-raises
# ---------------------------------------------------------------------------

class TestApplyManifestConfigMapNon409Raises:
    """Cover line 491: apply_manifest ConfigMap re-raises non-409 ApiException."""

    @pytest.mark.asyncio
    async def test_apply_manifest_configmap_non409_raises(self):
        """Line 491 – ConfigMap ApiException with non-409 status is re-raised."""
        from src.infrastructure.external.k8s_client import ApiException
        client = _make_client(available=True)
        client._client.CoreV1Api.return_value.create_namespaced_config_map.side_effect = ApiException(
            status=403, reason="Forbidden"
        )

        manifest = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {"name": "my-config", "namespace": "default"},
        }
        with patch("asyncio.to_thread", side_effect=_run_to_thread):
            result = await client.apply_manifest(manifest)

        assert "error" in result


# ---------------------------------------------------------------------------
# Line 512: Namespace ApiException non-409 re-raises
# ---------------------------------------------------------------------------

class TestApplyManifestNamespaceNon409Raises:
    """Cover line 512: apply_manifest Namespace re-raises non-409 ApiException."""

    @pytest.mark.asyncio
    async def test_apply_manifest_namespace_non409_raises(self):
        """Line 512 – Namespace ApiException with non-409 status is re-raised."""
        from src.infrastructure.external.k8s_client import ApiException
        client = _make_client(available=True)
        client._client.CoreV1Api.return_value.create_namespace.side_effect = ApiException(
            status=403, reason="Forbidden"
        )

        manifest = {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {"name": "my-namespace"},
        }
        with patch("asyncio.to_thread", side_effect=_run_to_thread):
            result = await client.apply_manifest(manifest)

        assert "error" in result


# ---------------------------------------------------------------------------
# Line 536: Pod ApiException non-409 re-raises
# ---------------------------------------------------------------------------

class TestApplyManifestPodNon409Raises:
    """Cover line 536: apply_manifest Pod re-raises non-409 ApiException."""

    @pytest.mark.asyncio
    async def test_apply_manifest_pod_non409_raises(self):
        """Line 536 – Pod ApiException with non-409 status is re-raised."""
        from src.infrastructure.external.k8s_client import ApiException
        client = _make_client(available=True)
        client._client.CoreV1Api.return_value.create_namespaced_pod.side_effect = ApiException(
            status=403, reason="Forbidden"
        )

        manifest = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {"name": "my-pod", "namespace": "default"},
        }
        with patch("asyncio.to_thread", side_effect=_run_to_thread):
            result = await client.apply_manifest(manifest)

        assert "error" in result
