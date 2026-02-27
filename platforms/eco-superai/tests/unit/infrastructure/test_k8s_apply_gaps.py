"""Targeted tests for remaining uncovered lines in k8s_client.py apply_manifest.

Covers:
- Service kind: create (lines 440-450) and patch on 409 (lines 451-464)
- ConfigMap kind: patch on 409 (lines 478-491)
- Namespace kind: create (lines 493-501) and patch on 409 (lines 502-512)
- Pod kind: create (lines 514-525) and conflict (lines 526-536)
- Other uncovered lines: 43-45, 82-83, 86-90, 171-173, 277-279, 336-338, 348, 376-378, 398-401, 404, 418
"""
from __future__ import annotations

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


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
# Service kind – create (lines 440-450)
# ---------------------------------------------------------------------------

class TestApplyManifestService:
    """Cover lines 440-464: apply_manifest with Service kind."""

    @pytest.mark.asyncio
    async def test_apply_manifest_service_create(self):
        """Lines 440-450 – Service is created successfully."""
        client = _make_client(available=True)
        mock_result = MagicMock()
        mock_result.metadata.name = "my-service"
        mock_result.metadata.namespace = "default"
        client._client.CoreV1Api.return_value.create_namespaced_service.return_value = mock_result

        manifest = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {"name": "my-service", "namespace": "default"},
            "spec": {"selector": {"app": "my-app"}, "ports": [{"port": 80}]},
        }
        with patch("asyncio.to_thread", side_effect=_run_to_thread):
            result = await client.apply_manifest(manifest)

        assert result.get("action") == "created"
        assert result.get("kind") == "Service"
        assert result.get("name") == "my-service"

    @pytest.mark.asyncio
    async def test_apply_manifest_service_patch_on_409(self):
        """Lines 451-464 – Service is patched when 409 conflict occurs."""
        from src.infrastructure.external.k8s_client import ApiException

        client = _make_client(available=True)
        mock_result = MagicMock()
        mock_result.metadata.name = "my-service"
        mock_result.metadata.namespace = "default"

        # create raises 409, patch succeeds
        client._client.CoreV1Api.return_value.create_namespaced_service.side_effect = ApiException(
            status=409, reason="Conflict"
        )
        client._client.CoreV1Api.return_value.patch_namespaced_service.return_value = mock_result

        manifest = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {"name": "my-service", "namespace": "default"},
        }
        with patch("asyncio.to_thread", side_effect=_run_to_thread):
            result = await client.apply_manifest(manifest)

        assert result.get("action") == "patched"
        assert result.get("kind") == "Service"


# ---------------------------------------------------------------------------
# ConfigMap kind – patch on 409 (lines 478-491)
# ---------------------------------------------------------------------------

class TestApplyManifestConfigMapPatch:
    """Cover lines 478-491: apply_manifest ConfigMap patch on 409."""

    @pytest.mark.asyncio
    async def test_apply_manifest_configmap_patch_on_409(self):
        """Lines 478-491 – ConfigMap is patched when 409 conflict occurs."""
        from src.infrastructure.external.k8s_client import ApiException

        client = _make_client(available=True)
        mock_result = MagicMock()
        mock_result.metadata.name = "my-config"
        mock_result.metadata.namespace = "default"

        # create raises 409, patch succeeds
        client._client.CoreV1Api.return_value.create_namespaced_config_map.side_effect = ApiException(
            status=409, reason="Conflict"
        )
        client._client.CoreV1Api.return_value.patch_namespaced_config_map.return_value = mock_result

        manifest = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {"name": "my-config", "namespace": "default"},
            "data": {"key": "value"},
        }
        with patch("asyncio.to_thread", side_effect=_run_to_thread):
            result = await client.apply_manifest(manifest)

        assert result.get("action") == "patched"
        assert result.get("kind") == "ConfigMap"


# ---------------------------------------------------------------------------
# Namespace kind – create and patch on 409 (lines 493-512)
# ---------------------------------------------------------------------------

class TestApplyManifestNamespace:
    """Cover lines 493-512: apply_manifest with Namespace kind."""

    @pytest.mark.asyncio
    async def test_apply_manifest_namespace_create(self):
        """Lines 493-501 – Namespace is created successfully."""
        client = _make_client(available=True)
        mock_result = MagicMock()
        mock_result.metadata.name = "my-namespace"

        client._client.CoreV1Api.return_value.create_namespace.return_value = mock_result

        manifest = {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {"name": "my-namespace"},
        }
        with patch("asyncio.to_thread", side_effect=_run_to_thread):
            result = await client.apply_manifest(manifest)

        assert result.get("action") == "created"
        assert result.get("kind") == "Namespace"
        assert result.get("name") == "my-namespace"

    @pytest.mark.asyncio
    async def test_apply_manifest_namespace_patch_on_409(self):
        """Lines 502-512 – Namespace is patched when 409 conflict occurs."""
        from src.infrastructure.external.k8s_client import ApiException

        client = _make_client(available=True)
        mock_result = MagicMock()
        mock_result.metadata.name = "my-namespace"

        # create raises 409, patch succeeds
        client._client.CoreV1Api.return_value.create_namespace.side_effect = ApiException(
            status=409, reason="Conflict"
        )
        client._client.CoreV1Api.return_value.patch_namespace.return_value = mock_result

        manifest = {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {"name": "my-namespace"},
        }
        with patch("asyncio.to_thread", side_effect=_run_to_thread):
            result = await client.apply_manifest(manifest)

        assert result.get("action") == "patched"
        assert result.get("kind") == "Namespace"


# ---------------------------------------------------------------------------
# Pod kind – create and conflict (lines 514-536)
# ---------------------------------------------------------------------------

class TestApplyManifestPod:
    """Cover lines 514-536: apply_manifest with Pod kind."""

    @pytest.mark.asyncio
    async def test_apply_manifest_pod_create(self):
        """Lines 514-525 – Pod is created successfully."""
        client = _make_client(available=True)
        mock_result = MagicMock()
        mock_result.metadata.name = "my-pod"
        mock_result.metadata.namespace = "default"

        client._client.CoreV1Api.return_value.create_namespaced_pod.return_value = mock_result

        manifest = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {"name": "my-pod", "namespace": "default"},
            "spec": {"containers": [{"name": "app", "image": "nginx"}]},
        }
        with patch("asyncio.to_thread", side_effect=_run_to_thread):
            result = await client.apply_manifest(manifest)

        assert result.get("action") == "created"
        assert result.get("kind") == "Pod"
        assert result.get("name") == "my-pod"

    @pytest.mark.asyncio
    async def test_apply_manifest_pod_conflict_409(self):
        """Lines 526-536 – Pod returns conflict dict when 409 occurs."""
        from src.infrastructure.external.k8s_client import ApiException

        client = _make_client(available=True)

        # create raises 409 - Pods cannot be patched
        client._client.CoreV1Api.return_value.create_namespaced_pod.side_effect = ApiException(
            status=409, reason="Conflict"
        )

        manifest = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {"name": "my-pod", "namespace": "default"},
        }
        with patch("asyncio.to_thread", side_effect=_run_to_thread):
            result = await client.apply_manifest(manifest)

        assert result.get("action") == "conflict"
        assert result.get("kind") == "Pod"
        assert "Delete first" in result.get("message", "")
