"""Tests for infrastructure platform engines."""

import pytest

from infrastructure_platform.engines.deployment_engine import DeploymentEngine
from infrastructure_platform.engines.service_engine import ServiceEngine
from infrastructure_platform.engines.provisioner import Provisioner
from infrastructure_platform.domain.value_objects import (
    DeploymentStrategy,
    ServiceType,
)
from infrastructure_platform.domain.exceptions import (
    DeploymentNotFoundError,
    NamespaceExistsError,
    RollbackError,
    ServiceNotFoundError,
)
from platform_shared.sandbox.resource import ResourceLimits


# -- DeploymentEngine -------------------------------------------------------


class TestDeploymentEngine:
    def test_create_deployment(self, deployment_engine):
        dep = deployment_engine.create_deployment(
            name="web", image="nginx:1.25", replicas=3
        )
        assert dep.name == "web"
        assert dep.image == "nginx:1.25"
        assert dep.replicas == 3
        assert dep.strategy == DeploymentStrategy.ROLLING
        assert dep.version == 1

    def test_create_deployment_with_strategy(self, deployment_engine):
        dep = deployment_engine.create_deployment(
            name="api",
            image="app.kubernetes.io/name: v1",
            replicas=2,
            strategy=DeploymentStrategy.BLUE_GREEN,
        )
        assert dep.strategy == DeploymentStrategy.BLUE_GREEN
        assert dep.active_color == "blue"

    def test_get_deployment(self, deployment_engine):
        dep = deployment_engine.create_deployment(name="web", image="nginx:latest")
        fetched = deployment_engine.get_deployment(dep.id)
        assert fetched.id == dep.id
        assert fetched.name == "web"

    def test_get_deployment_not_found(self, deployment_engine):
        with pytest.raises(DeploymentNotFoundError):
            deployment_engine.get_deployment("nonexistent")

    def test_list_deployments(self, deployment_engine):
        deployment_engine.create_deployment(name="web", image="nginx:latest", namespace="prod")
        deployment_engine.create_deployment(name="api", image="app.kubernetes.io/name: v1", namespace="staging")
        deployment_engine.create_deployment(name="worker", image="worker:v1", namespace="prod")

        all_deps = deployment_engine.list_deployments()
        assert len(all_deps) == 3

        prod_deps = deployment_engine.list_deployments(namespace="prod")
        assert len(prod_deps) == 2

    def test_update_deployment(self, deployment_engine):
        dep = deployment_engine.create_deployment(
            name="web", image="nginx:1.24", replicas=2
        )
        updated = deployment_engine.update_deployment(dep.id, image="nginx:1.25", replicas=4)
        assert updated.image == "nginx:1.25"
        assert updated.replicas == 4
        assert updated.version == 2
        assert updated.previous_image == "nginx:1.24"
        assert updated.previous_replicas == 2

    def test_rollback(self, deployment_engine):
        dep = deployment_engine.create_deployment(
            name="web", image="nginx:1.24", replicas=2
        )
        deployment_engine.update_deployment(dep.id, image="nginx:1.25", replicas=4)
        rolled_back = deployment_engine.rollback(dep.id)
        assert rolled_back.image == "nginx:1.24"
        assert rolled_back.replicas == 2
        assert rolled_back.status == "rolled_back"
        assert rolled_back.version == 3

    def test_rollback_no_history(self, deployment_engine):
        dep = deployment_engine.create_deployment(name="web", image="nginx:latest")
        with pytest.raises(RollbackError, match="No previous version"):
            deployment_engine.rollback(dep.id)

    def test_blue_green_swap(self, deployment_engine):
        dep = deployment_engine.create_deployment(
            name="api",
            image="app.kubernetes.io/name: v1",
            strategy=DeploymentStrategy.BLUE_GREEN,
        )
        assert dep.active_color == "blue"
        swapped = deployment_engine.blue_green_swap(dep.id)
        assert swapped.active_color == "green"
        swapped_back = deployment_engine.blue_green_swap(dep.id)
        assert swapped_back.active_color == "blue"

    def test_blue_green_swap_wrong_strategy(self, deployment_engine):
        dep = deployment_engine.create_deployment(
            name="web", image="nginx:latest", strategy=DeploymentStrategy.ROLLING
        )
        with pytest.raises(RollbackError, match="BLUE_GREEN"):
            deployment_engine.blue_green_swap(dep.id)

    def test_get_history(self, deployment_engine):
        dep = deployment_engine.create_deployment(
            name="web", image="nginx:1.24", replicas=2
        )
        deployment_engine.update_deployment(dep.id, image="nginx:1.25")
        deployment_engine.update_deployment(dep.id, image="nginx:1.26")

        history = deployment_engine.get_history(dep.id)
        assert len(history) == 3
        assert history[0]["image"] == "nginx:1.24"
        assert history[1]["image"] == "nginx:1.25"
        assert history[2]["image"] == "nginx:1.26"

    def test_delete_deployment(self, deployment_engine):
        dep = deployment_engine.create_deployment(name="web", image="nginx:latest")
        deployment_engine.delete_deployment(dep.id)
        with pytest.raises(DeploymentNotFoundError):
            deployment_engine.get_deployment(dep.id)

    def test_delete_nonexistent(self, deployment_engine):
        with pytest.raises(DeploymentNotFoundError):
            deployment_engine.delete_deployment("nonexistent")

    def test_engine_properties(self, deployment_engine):
        assert deployment_engine.name == "deployment-engine"
        assert deployment_engine.status.value == "running"


# -- ServiceEngine ----------------------------------------------------------


class TestServiceEngine:
    def test_create_service(self, service_engine):
        svc = service_engine.create_service(
            name="web-svc",
            service_type=ServiceType.LOAD_BALANCER,
            port=80,
            target_port=8080,
        )
        assert svc.name == "web-svc"
        assert svc.service_type == ServiceType.LOAD_BALANCER
        assert svc.port == 80
        assert svc.target_port == 8080

    def test_expose_deployment(self, deployment_engine, service_engine):
        dep = deployment_engine.create_deployment(
            name="web", image="nginx:latest", replicas=3
        )
        svc = service_engine.expose(dep.id, port=80, target_port=8080)
        assert svc.name == "web-svc"
        assert svc.deployment_id == dep.id
        assert len(svc.endpoints) == 3  # one per replica

    def test_expose_nonexistent_deployment(self, service_engine):
        with pytest.raises(DeploymentNotFoundError):
            service_engine.expose("nonexistent")

    def test_get_service(self, service_engine):
        svc = service_engine.create_service(name="api-svc")
        fetched = service_engine.get_service(svc.id)
        assert fetched.id == svc.id

    def test_get_service_not_found(self, service_engine):
        with pytest.raises(ServiceNotFoundError):
            service_engine.get_service("nonexistent")

    def test_list_services(self, service_engine):
        service_engine.create_service(name="web-svc", namespace="prod")
        service_engine.create_service(name="api-svc", namespace="staging")
        service_engine.create_service(name="db-svc", namespace="prod")

        all_svcs = service_engine.list_services()
        assert len(all_svcs) == 3

        prod_svcs = service_engine.list_services(namespace="prod")
        assert len(prod_svcs) == 2

    def test_list_endpoints(self, deployment_engine, service_engine):
        dep = deployment_engine.create_deployment(
            name="web", image="nginx:latest", replicas=2
        )
        svc = service_engine.expose(dep.id)
        endpoints = service_engine.list_endpoints(svc.id)
        assert len(endpoints) == 2
        assert all("web" in ep for ep in endpoints)

    def test_delete_service(self, service_engine):
        svc = service_engine.create_service(name="web-svc")
        service_engine.delete_service(svc.id)
        with pytest.raises(ServiceNotFoundError):
            service_engine.get_service(svc.id)

    def test_delete_nonexistent_service(self, service_engine):
        with pytest.raises(ServiceNotFoundError):
            service_engine.delete_service("nonexistent")

    def test_engine_properties(self, service_engine):
        assert service_engine.name == "service-engine"
        assert service_engine.status.value == "running"

    def test_create_service_with_selector(self, deployment_engine, service_engine):
        dep = deployment_engine.create_deployment(
            name="web", image="nginx:latest", replicas=2, labels={"app": "web"}
        )
        svc = service_engine.create_service(
            name="web-svc", selector={"app": "web"}
        )
        assert len(svc.endpoints) == 2


# -- Provisioner ------------------------------------------------------------


class TestProvisioner:
    def test_create_namespace(self, provisioner):
        ns = provisioner.create_namespace(
            name="production",
            quotas=ResourceLimits(cpu_cores=8.0, memory_mb=16384),
        )
        assert ns.name == "production"
        assert ns.quotas.cpu_cores == 8.0
        assert ns.quotas.memory_mb == 16384

    def test_create_duplicate_namespace(self, provisioner):
        provisioner.create_namespace(name="production")
        with pytest.raises(NamespaceExistsError):
            provisioner.create_namespace(name="production")

    def test_list_namespaces(self, provisioner):
        provisioner.create_namespace(name="prod")
        provisioner.create_namespace(name="staging")
        provisioner.create_namespace(name="dev")
        nss = provisioner.list_namespaces()
        assert len(nss) == 3
        names = {ns.name for ns in nss}
        assert names == {"prod", "staging", "dev"}

    def test_get_namespace(self, provisioner):
        ns = provisioner.create_namespace(name="prod")
        fetched = provisioner.get_namespace(ns.id)
        assert fetched.name == "prod"

    def test_get_namespace_by_name(self, provisioner):
        provisioner.create_namespace(name="staging")
        ns = provisioner.get_namespace_by_name("staging")
        assert ns.name == "staging"

    def test_delete_namespace(self, provisioner):
        ns = provisioner.create_namespace(name="temp")
        provisioner.delete_namespace(ns.id)
        assert len(provisioner.list_namespaces()) == 0

    def test_apply_network_policy(self, provisioner):
        ns = provisioner.create_namespace(name="secure")
        provisioner.apply_network_policy(ns.id, "deny-all-ingress")
        policies = provisioner.list_network_policies(ns.id)
        assert "deny-all-ingress" in policies

    def test_apply_duplicate_network_policy(self, provisioner):
        ns = provisioner.create_namespace(name="secure")
        provisioner.apply_network_policy(ns.id, "deny-all")
        provisioner.apply_network_policy(ns.id, "deny-all")
        policies = provisioner.list_network_policies(ns.id)
        assert policies.count("deny-all") == 1

    def test_remove_network_policy(self, provisioner):
        ns = provisioner.create_namespace(name="secure")
        provisioner.apply_network_policy(ns.id, "deny-all")
        provisioner.remove_network_policy(ns.id, "deny-all")
        policies = provisioner.list_network_policies(ns.id)
        assert "deny-all" not in policies

    def test_engine_properties(self, provisioner):
        assert provisioner.name == "provisioner"
        assert provisioner.status.value == "running"
