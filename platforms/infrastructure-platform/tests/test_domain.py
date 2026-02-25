"""Tests for infrastructure platform domain layer."""

import pytest

from infrastructure_platform.domain.entities import (
    Deployment,
    HelmRelease,
    Namespace,
    Node,
    Service,
)
from infrastructure_platform.domain.value_objects import (
    DeploymentStrategy,
    NodeStatus,
    ServiceType,
)
from infrastructure_platform.domain.events import (
    DeploymentCreated,
    NodeJoined,
    RollbackTriggered,
    ServiceExposed,
)
from infrastructure_platform.domain.exceptions import (
    DeploymentNotFoundError,
    InfrastructureError,
    NamespaceExistsError,
    NodeNotFoundError,
    RollbackError,
    ServiceNotFoundError,
)
from platform_shared.sandbox.resource import ResourceLimits


# -- Value Objects ----------------------------------------------------------


class TestDeploymentStrategy:
    def test_rolling_value(self):
        assert DeploymentStrategy.ROLLING.value == "rolling"

    def test_blue_green_value(self):
        assert DeploymentStrategy.BLUE_GREEN.value == "blue_green"

    def test_canary_value(self):
        assert DeploymentStrategy.CANARY.value == "canary"

    def test_from_string(self):
        assert DeploymentStrategy("rolling") == DeploymentStrategy.ROLLING


class TestServiceType:
    def test_cluster_ip(self):
        assert ServiceType.CLUSTER_IP.value == "cluster_ip"

    def test_node_port(self):
        assert ServiceType.NODE_PORT.value == "node_port"

    def test_load_balancer(self):
        assert ServiceType.LOAD_BALANCER.value == "load_balancer"


class TestNodeStatus:
    def test_all_statuses_exist(self):
        statuses = [s.value for s in NodeStatus]
        assert "pending" in statuses
        assert "ready" in statuses
        assert "not_ready" in statuses
        assert "cordoned" in statuses
        assert "draining" in statuses
        assert "terminated" in statuses


# -- Entities ---------------------------------------------------------------


class TestDeployment:
    def test_default_values(self):
        dep = Deployment(name="web", image="nginx:latest")
        assert dep.name == "web"
        assert dep.image == "nginx:latest"
        assert dep.replicas == 1
        assert dep.strategy == DeploymentStrategy.ROLLING
        assert dep.namespace == "default"
        assert dep.version == 1
        assert dep.active_color == "blue"
        assert dep.id.startswith("deploy-")

    def test_to_dict(self):
        dep = Deployment(name="api", image="app.kubernetes.io/name: v1", replicas=3)
        d = dep.to_dict()
        assert d["name"] == "api"
        assert d["image"] == "app.kubernetes.io/name: v1"
        assert d["replicas"] == 3
        assert d["strategy"] == "rolling"
        assert "id" in d
        assert "created_at" in d


class TestService:
    def test_default_values(self):
        svc = Service(name="web-svc", port=80, target_port=8080)
        assert svc.name == "web-svc"
        assert svc.service_type == ServiceType.CLUSTER_IP
        assert svc.port == 80
        assert svc.target_port == 8080
        assert svc.id.startswith("svc-")

    def test_to_dict(self):
        svc = Service(name="api-svc", service_type=ServiceType.LOAD_BALANCER)
        d = svc.to_dict()
        assert d["name"] == "api-svc"
        assert d["service_type"] == "load_balancer"


class TestNode:
    def test_default_values(self):
        node = Node(name="worker-1", ip_address="10.0.0.1")
        assert node.name == "worker-1"
        assert node.status == NodeStatus.PENDING
        assert node.id.startswith("node-")

    def test_to_dict(self):
        node = Node(name="worker-2", ip_address="10.0.0.2", status=NodeStatus.READY)
        d = node.to_dict()
        assert d["name"] == "worker-2"
        assert d["status"] == "ready"


class TestNamespace:
    def test_default_values(self):
        ns = Namespace(name="production")
        assert ns.name == "production"
        assert ns.id.startswith("ns-")
        assert isinstance(ns.quotas, ResourceLimits)

    def test_to_dict(self):
        ns = Namespace(name="staging", quotas=ResourceLimits(cpu_cores=4.0, memory_mb=2048))
        d = ns.to_dict()
        assert d["name"] == "staging"
        assert d["quotas"]["cpu_cores"] == 4.0
        assert d["quotas"]["memory_mb"] == 2048


class TestHelmRelease:
    def test_default_values(self):
        release = HelmRelease(name="prometheus", chart="prometheus-community/prometheus")
        assert release.name == "prometheus"
        assert release.chart == "prometheus-community/prometheus"
        assert release.status == "deployed"
        assert release.revision == 1
        assert release.id.startswith("helm-")

    def test_to_dict(self):
        release = HelmRelease(name="grafana", chart="grafana/grafana", version="6.50.0")
        d = release.to_dict()
        assert d["name"] == "grafana"
        assert d["version"] == "6.50.0"


# -- Events -----------------------------------------------------------------


class TestEvents:
    def test_deployment_created_event(self):
        evt = DeploymentCreated(
            deployment_id="deploy-abc123",
            name="web",
            image="nginx:latest",
            replicas=3,
        )
        event = evt.to_event()
        assert event.topic == "infrastructure.deployment.created"
        assert event.payload["deployment_id"] == "deploy-abc123"
        assert event.payload["name"] == "web"
        assert event.source == "infrastructure-platform"

    def test_service_exposed_event(self):
        evt = ServiceExposed(
            service_id="svc-abc123",
            name="web-svc",
            port=80,
            deployment_id="deploy-xyz",
        )
        event = evt.to_event()
        assert event.topic == "infrastructure.service.exposed"
        assert event.payload["service_id"] == "svc-abc123"

    def test_node_joined_event(self):
        evt = NodeJoined(node_id="node-abc", name="worker-1", ip_address="10.0.0.5")
        event = evt.to_event()
        assert event.topic == "infrastructure.node.joined"
        assert event.payload["ip_address"] == "10.0.0.5"

    def test_rollback_triggered_event(self):
        evt = RollbackTriggered(
            deployment_id="deploy-abc",
            from_version=3,
            to_version=2,
            reason="health check failed",
        )
        event = evt.to_event()
        assert event.topic == "infrastructure.deployment.rollback"
        assert event.payload["from_version"] == 3
        assert event.payload["reason"] == "health check failed"


# -- Exceptions -------------------------------------------------------------


class TestExceptions:
    def test_infrastructure_error(self):
        err = InfrastructureError("something broke")
        assert str(err) == "something broke"
        assert err.code == "INFRASTRUCTURE_ERROR"

    def test_deployment_not_found(self):
        err = DeploymentNotFoundError("deploy-xyz")
        assert "deploy-xyz" in str(err)
        assert err.deployment_id == "deploy-xyz"

    def test_service_not_found(self):
        err = ServiceNotFoundError("svc-xyz")
        assert "svc-xyz" in str(err)
        assert err.service_id == "svc-xyz"

    def test_node_not_found(self):
        err = NodeNotFoundError("node-xyz")
        assert "node-xyz" in str(err)
        assert err.node_id == "node-xyz"

    def test_rollback_error(self):
        err = RollbackError("deploy-abc", "no history")
        assert "deploy-abc" in str(err)
        assert "no history" in str(err)

    def test_namespace_exists(self):
        err = NamespaceExistsError("prod")
        assert "prod" in str(err)
        assert err.namespace_name == "prod"
