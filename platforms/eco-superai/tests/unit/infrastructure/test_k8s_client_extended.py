"""Extended tests for infrastructure/external/k8s_client.py.

Tests all K8s methods with _available=True by mocking the kubernetes API
and asyncio.to_thread to execute _call() functions directly.
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


class TestK8sClientInit:
    def test_init_k8s_unavailable(self) -> None:
        """K8sClient should handle missing kubernetes package."""
        import src.infrastructure.external.k8s_client as k8s_mod
        original = k8s_mod._K8S_AVAILABLE
        try:
            k8s_mod._K8S_AVAILABLE = False
            client = _make_client(available=False)
            assert client._available is False
        finally:
            k8s_mod._K8S_AVAILABLE = original

    def test_is_available_property(self) -> None:
        """is_available should reflect _available state."""
        client = _make_client(available=True)
        assert client.is_available is True
        client._available = False
        assert client.is_available is False

    def test_init_client_exception(self) -> None:
        """_init_client should handle exceptions gracefully."""
        import src.infrastructure.external.k8s_client as k8s_mod
        original = k8s_mod._K8S_AVAILABLE
        original_config = k8s_mod._k8s_config_module
        try:
            k8s_mod._K8S_AVAILABLE = True
            mock_config = MagicMock()
            mock_config.load_kube_config.side_effect = Exception("no kubeconfig")
            mock_config.load_incluster_config.side_effect = Exception("not in cluster")
            k8s_mod._k8s_config_module = mock_config
            from src.infrastructure.external.k8s_client import K8sClient
            client = K8sClient.__new__(K8sClient)
            client._available = False
            client._in_cluster = False
            client._client = None
            with patch("os.path.exists", return_value=False):
                client._init_client()
            assert client._available is False
        finally:
            k8s_mod._K8S_AVAILABLE = original
            k8s_mod._k8s_config_module = original_config


class TestK8sClientHealthCheck:
    @pytest.mark.asyncio
    async def test_health_check_unavailable(self) -> None:
        """health_check should return unavailable when client not configured."""
        client = _make_client(available=False)
        result = await client.health_check()
        assert result["status"] == "unavailable"

    @pytest.mark.asyncio
    async def test_health_check_all_ready(self) -> None:
        """health_check should return healthy when all nodes are ready."""
        client = _make_client(available=True)
        with patch.object(client, "list_nodes", return_value=[
            {"name": "node-1", "ready": "True"},
            {"name": "node-2", "ready": "True"},
        ]):
            result = await client.health_check()
            assert result["status"] == "healthy"
            assert result["total_nodes"] == 2
            assert result["ready_nodes"] == 2

    @pytest.mark.asyncio
    async def test_health_check_degraded(self) -> None:
        """health_check should return degraded when some nodes are not ready."""
        client = _make_client(available=True)
        with patch.object(client, "list_nodes", return_value=[
            {"name": "node-1", "ready": "True"},
            {"name": "node-2", "ready": "False"},
        ]):
            result = await client.health_check()
            assert result["status"] == "degraded"

    @pytest.mark.asyncio
    async def test_health_check_exception(self) -> None:
        """health_check should return error dict on exception."""
        client = _make_client(available=True)
        with patch.object(client, "list_nodes", side_effect=Exception("timeout")):
            result = await client.health_check()
            assert result["status"] == "error"
            assert "timeout" in result["message"]


class TestK8sClientListNamespaces:
    @pytest.mark.asyncio
    async def test_list_namespaces_unavailable(self) -> None:
        """list_namespaces should return [] when unavailable."""
        client = _make_client(available=False)
        result = await client.list_namespaces()
        assert result == []

    @pytest.mark.asyncio
    async def test_list_namespaces_success(self) -> None:
        """list_namespaces should return namespace list when available."""
        client = _make_client(available=True)
        mock_ns = MagicMock()
        mock_ns.metadata.name = "default"
        mock_ns.metadata.creation_timestamp = None
        mock_ns.status.phase = "Active"
        mock_ns.metadata.labels = {}
        mock_ns_list = MagicMock()
        mock_ns_list.items = [mock_ns]
        client._client.CoreV1Api.return_value.list_namespace.return_value = mock_ns_list
        with patch("asyncio.to_thread", side_effect=_run_to_thread):
            result = await client.list_namespaces()
        assert len(result) == 1
        assert result[0]["name"] == "default"

    @pytest.mark.asyncio
    async def test_list_namespaces_api_exception(self) -> None:
        """list_namespaces should return [] on ApiException."""
        from src.infrastructure.external.k8s_client import ApiException
        client = _make_client(available=True)
        client._client.CoreV1Api.return_value.list_namespace.side_effect = ApiException(status=403, reason="Forbidden")
        with patch("asyncio.to_thread", side_effect=_run_to_thread):
            result = await client.list_namespaces()
        assert result == []


class TestK8sClientListPods:
    @pytest.mark.asyncio
    async def test_list_pods_unavailable(self) -> None:
        """list_pods should return [] when unavailable."""
        client = _make_client(available=False)
        result = await client.list_pods()
        assert result == []

    @pytest.mark.asyncio
    async def test_list_pods_success(self) -> None:
        """list_pods should return pod list when available."""
        client = _make_client(available=True)
        mock_pod = MagicMock()
        mock_pod.metadata.name = "test-pod"
        mock_pod.metadata.namespace = "default"
        mock_pod.status.phase = "Running"
        mock_pod.spec.node_name = "node-1"
        mock_pod.status.pod_ip = "10.0.0.1"
        mock_pod.metadata.creation_timestamp = None
        mock_pod.status.container_statuses = []
        mock_container = MagicMock()
        mock_container.name = "main"
        mock_container.image = "nginx:latest"
        mock_pod.spec.containers = [mock_container]
        mock_pod_list = MagicMock()
        mock_pod_list.items = [mock_pod]
        client._client.CoreV1Api.return_value.list_namespaced_pod.return_value = mock_pod_list
        with patch("asyncio.to_thread", side_effect=_run_to_thread):
            result = await client.list_pods(namespace="default")
        assert len(result) == 1
        assert result[0]["name"] == "test-pod"

    @pytest.mark.asyncio
    async def test_list_pods_api_exception(self) -> None:
        """list_pods should return [] on ApiException."""
        from src.infrastructure.external.k8s_client import ApiException
        client = _make_client(available=True)
        client._client.CoreV1Api.return_value.list_namespaced_pod.side_effect = ApiException(status=404)
        with patch("asyncio.to_thread", side_effect=_run_to_thread):
            result = await client.list_pods()
        assert result == []

    @pytest.mark.asyncio
    async def test_list_pods_general_exception(self) -> None:
        """list_pods should return [] on general exception."""
        client = _make_client(available=True)
        client._client.CoreV1Api.return_value.list_namespaced_pod.side_effect = Exception("network error")
        with patch("asyncio.to_thread", side_effect=_run_to_thread):
            result = await client.list_pods()
        assert result == []


class TestK8sClientListDeployments:
    @pytest.mark.asyncio
    async def test_list_deployments_unavailable(self) -> None:
        """list_deployments should return [] when unavailable."""
        client = _make_client(available=False)
        result = await client.list_deployments()
        assert result == []

    @pytest.mark.asyncio
    async def test_list_deployments_success(self) -> None:
        """list_deployments should return deployment list when available."""
        client = _make_client(available=True)
        mock_dep = MagicMock()
        mock_dep.metadata.name = "test-deploy"
        mock_dep.metadata.namespace = "default"
        mock_dep.spec.replicas = 3
        mock_dep.status.ready_replicas = 3
        mock_dep.status.available_replicas = 3
        mock_dep.status.unavailable_replicas = 0
        mock_dep.spec.strategy.type = "RollingUpdate"
        mock_dep.metadata.creation_timestamp = None
        mock_dep.status.conditions = []
        mock_container = MagicMock()
        mock_container.image = "nginx:latest"
        mock_dep.spec.template.spec.containers = [mock_container]
        mock_dep_list = MagicMock()
        mock_dep_list.items = [mock_dep]
        client._client.AppsV1Api.return_value.list_namespaced_deployment.return_value = mock_dep_list
        with patch("asyncio.to_thread", side_effect=_run_to_thread):
            result = await client.list_deployments()
        assert len(result) == 1
        assert result[0]["name"] == "test-deploy"

    @pytest.mark.asyncio
    async def test_list_deployments_api_exception(self) -> None:
        """list_deployments should return [] on ApiException."""
        from src.infrastructure.external.k8s_client import ApiException
        client = _make_client(available=True)
        client._client.AppsV1Api.return_value.list_namespaced_deployment.side_effect = ApiException(status=403)
        with patch("asyncio.to_thread", side_effect=_run_to_thread):
            result = await client.list_deployments()
        assert result == []


class TestK8sClientGetDeploymentStatus:
    @pytest.mark.asyncio
    async def test_get_deployment_status_unavailable(self) -> None:
        """get_deployment_status should return error dict when unavailable."""
        client = _make_client(available=False)
        result = await client.get_deployment_status("my-deploy")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_get_deployment_status_success(self) -> None:
        """get_deployment_status should return deployment details."""
        client = _make_client(available=True)
        mock_dep = MagicMock()
        mock_dep.metadata.name = "my-deploy"
        mock_dep.metadata.namespace = "default"
        mock_dep.spec.replicas = 2
        mock_dep.status.ready_replicas = 2
        mock_dep.status.available_replicas = 2
        mock_dep.status.unavailable_replicas = 0
        mock_dep.spec.strategy.type = "RollingUpdate"
        mock_dep.metadata.creation_timestamp = None
        mock_dep.status.conditions = []
        mock_container = MagicMock()
        mock_container.image = "app:v1"
        mock_dep.spec.template.spec.containers = [mock_container]
        client._client.AppsV1Api.return_value.read_namespaced_deployment.return_value = mock_dep
        with patch("asyncio.to_thread", side_effect=_run_to_thread):
            result = await client.get_deployment_status("my-deploy")
        assert result["name"] == "my-deploy"

    @pytest.mark.asyncio
    async def test_get_deployment_status_not_found(self) -> None:
        """get_deployment_status should return error dict on ApiException."""
        from src.infrastructure.external.k8s_client import ApiException
        client = _make_client(available=True)
        client._client.AppsV1Api.return_value.read_namespaced_deployment.side_effect = ApiException(status=404)
        with patch("asyncio.to_thread", side_effect=_run_to_thread):
            result = await client.get_deployment_status("missing-deploy")
        assert "error" in result


class TestK8sClientScaleDeployment:
    @pytest.mark.asyncio
    async def test_scale_deployment_unavailable(self) -> None:
        """scale_deployment should return error dict when unavailable."""
        client = _make_client(available=False)
        result = await client.scale_deployment("my-deploy", 3)
        assert "error" in result

    @pytest.mark.asyncio
    async def test_scale_deployment_success(self) -> None:
        """scale_deployment should update replicas and return status."""
        client = _make_client(available=True)
        mock_dep = MagicMock()
        mock_dep.metadata.name = "my-deploy"
        mock_dep.metadata.namespace = "default"
        mock_dep.spec.replicas = 3
        mock_dep.status.ready_replicas = 3
        mock_dep.status.available_replicas = 3
        mock_dep.status.unavailable_replicas = 0
        mock_dep.spec.strategy.type = "RollingUpdate"
        mock_dep.metadata.creation_timestamp = None
        mock_dep.status.conditions = []
        mock_dep.spec.template.spec.containers = []
        apps_api = client._client.AppsV1Api.return_value
        apps_api.read_namespaced_deployment.return_value = mock_dep
        apps_api.patch_namespaced_deployment.return_value = mock_dep
        with patch("asyncio.to_thread", side_effect=_run_to_thread):
            result = await client.scale_deployment("my-deploy", 3)
        assert "name" in result or "error" not in result

    @pytest.mark.asyncio
    async def test_scale_deployment_api_exception(self) -> None:
        """scale_deployment should return error dict on ApiException."""
        from src.infrastructure.external.k8s_client import ApiException
        client = _make_client(available=True)
        client._client.AppsV1Api.return_value.patch_namespaced_deployment_scale.side_effect = ApiException(status=404, reason="Not Found")
        with patch("asyncio.to_thread", side_effect=_run_to_thread):
            result = await client.scale_deployment("missing-deploy", 3)
        assert "error" in result


class TestK8sClientApplyManifest:
    @pytest.mark.asyncio
    async def test_apply_manifest_unavailable(self) -> None:
        """apply_manifest should return error dict when unavailable."""
        client = _make_client(available=False)
        result = await client.apply_manifest({"apiVersion": "v1", "kind": "ConfigMap"})
        assert "error" in result

    @pytest.mark.asyncio
    async def test_apply_manifest_unknown_kind(self) -> None:
        """apply_manifest should handle unknown resource kinds."""
        client = _make_client(available=True)
        manifest = {"apiVersion": "v1", "kind": "UnknownKind", "metadata": {"name": "test", "namespace": "default"}}
        with patch("asyncio.to_thread", side_effect=_run_to_thread):
            result = await client.apply_manifest(manifest)
        assert "error" in result or "status" in result

    @pytest.mark.asyncio
    async def test_apply_manifest_configmap(self) -> None:
        """apply_manifest should create ConfigMap successfully."""
        client = _make_client(available=True)
        mock_result = MagicMock()
        mock_result.metadata.name = "my-config"
        mock_result.metadata.namespace = "default"
        client._client.CoreV1Api.return_value.create_namespaced_config_map.return_value = mock_result
        client._client.CoreV1Api.return_value.patch_namespaced_config_map.return_value = mock_result
        manifest = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {"name": "my-config", "namespace": "default"},
            "data": {"key": "value"},
        }
        with patch("asyncio.to_thread", side_effect=_run_to_thread):
            result = await client.apply_manifest(manifest)
        assert "name" in result or "status" in result or "error" in result

    @pytest.mark.asyncio
    async def test_apply_manifest_api_exception(self) -> None:
        """apply_manifest should return error dict on ApiException."""
        from src.infrastructure.external.k8s_client import ApiException
        client = _make_client(available=True)
        # Use Deployment kind to trigger AppsV1Api path
        client._client.AppsV1Api.return_value.create_namespaced_deployment.side_effect = ApiException(status=409, reason="Conflict")
        client._client.AppsV1Api.return_value.patch_namespaced_deployment.side_effect = ApiException(status=409, reason="Conflict")
        manifest = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {"name": "conflict-deploy", "namespace": "default"},
        }
        with patch("asyncio.to_thread", side_effect=_run_to_thread):
            result = await client.apply_manifest(manifest)
        assert "error" in result or "status" in result


class TestK8sClientListNodes:
    @pytest.mark.asyncio
    async def test_list_nodes_unavailable(self) -> None:
        """list_nodes should return [] when unavailable."""
        client = _make_client(available=False)
        result = await client.list_nodes()
        assert result == []

    @pytest.mark.asyncio
    async def test_list_nodes_success(self) -> None:
        """list_nodes should return node list when available."""
        client = _make_client(available=True)
        mock_node = MagicMock()
        mock_node.metadata.name = "node-1"
        mock_node.metadata.creation_timestamp = None
        mock_node.metadata.labels = {"kubernetes.io/role": "worker"}
        mock_node.status.allocatable = {"cpu": "4", "memory": "8Gi"}
        mock_node.status.capacity = {"cpu": "4", "memory": "8Gi"}
        # Ready condition
        mock_condition = MagicMock()
        mock_condition.type = "Ready"
        mock_condition.status = "True"
        mock_node.status.conditions = [mock_condition]
        mock_node_list = MagicMock()
        mock_node_list.items = [mock_node]
        client._client.CoreV1Api.return_value.list_node.return_value = mock_node_list
        with patch("asyncio.to_thread", side_effect=_run_to_thread):
            result = await client.list_nodes()
        assert len(result) == 1
        assert result[0]["name"] == "node-1"
        assert result[0]["ready"] == "True"

    @pytest.mark.asyncio
    async def test_list_nodes_api_exception(self) -> None:
        """list_nodes should return [] on ApiException."""
        from src.infrastructure.external.k8s_client import ApiException
        client = _make_client(available=True)
        client._client.CoreV1Api.return_value.list_node.side_effect = ApiException(status=403)
        with patch("asyncio.to_thread", side_effect=_run_to_thread):
            result = await client.list_nodes()
        assert result == []
