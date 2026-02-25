"""Tests for infrastructure platform sandbox and API layers."""

import pytest

from infrastructure_platform.sandbox.infra_sandbox import InfraSandbox, SandboxResult
from infrastructure_platform.domain.value_objects import DeploymentStrategy, ServiceType
from infrastructure_platform.presentation.api import InfrastructureAPI
from platform_shared.sandbox.resource import ResourceLimits


# -- InfraSandbox -----------------------------------------------------------


class TestInfraSandbox:
    def test_sandbox_id(self, infra_sandbox):
        assert infra_sandbox.sandbox_id.startswith("infra-sb-")

    def test_is_active(self, infra_sandbox):
        assert infra_sandbox.is_active is True

    def test_dry_run_deployment_success(self, infra_sandbox):
        result = infra_sandbox.dry_run_deployment(
            name="web", image="nginx:latest", replicas=3
        )
        assert result.success is True
        assert result.operation == "create_deployment"
        assert result.result["name"] == "web"
        assert result.result["replicas"] == 3
        assert len(result.errors) == 0

    def test_dry_run_deployment_missing_name(self, infra_sandbox):
        result = infra_sandbox.dry_run_deployment(name="", image="nginx:latest")
        assert result.success is False
        assert any("name" in e.lower() for e in result.errors)

    def test_dry_run_deployment_missing_image(self, infra_sandbox):
        result = infra_sandbox.dry_run_deployment(name="web", image="")
        assert result.success is False
        assert any("image" in e.lower() for e in result.errors)

    def test_dry_run_deployment_invalid_replicas(self, infra_sandbox):
        result = infra_sandbox.dry_run_deployment(
            name="web", image="nginx:latest", replicas=0
        )
        assert result.success is False

    def test_dry_run_deployment_high_replicas_warning(self, infra_sandbox):
        result = infra_sandbox.dry_run_deployment(
            name="web", image="nginx:latest", replicas=200
        )
        assert result.success is True
        assert len(result.warnings) > 0

    def test_dry_run_service_success(self, infra_sandbox):
        result = infra_sandbox.dry_run_service(
            name="web-svc", port=80, target_port=8080
        )
        assert result.success is True
        assert result.operation == "create_service"
        assert result.result["name"] == "web-svc"

    def test_dry_run_service_missing_name(self, infra_sandbox):
        result = infra_sandbox.dry_run_service(name="")
        assert result.success is False

    def test_dry_run_service_invalid_port(self, infra_sandbox):
        result = infra_sandbox.dry_run_service(name="svc", port=0)
        assert result.success is False

    def test_dry_run_namespace_success(self, infra_sandbox):
        result = infra_sandbox.dry_run_namespace(
            name="production",
            quotas=ResourceLimits(cpu_cores=4.0, memory_mb=4096),
        )
        assert result.success is True
        assert result.operation == "create_namespace"
        assert result.result["name"] == "production"

    def test_dry_run_namespace_missing_name(self, infra_sandbox):
        result = infra_sandbox.dry_run_namespace(name="")
        assert result.success is False

    def test_dry_run_namespace_duplicate(self, infra_sandbox):
        infra_sandbox.dry_run_namespace(name="prod")
        result = infra_sandbox.dry_run_namespace(name="prod")
        assert result.success is False

    def test_operations_log(self, infra_sandbox):
        infra_sandbox.dry_run_deployment(name="web", image="nginx:latest")
        infra_sandbox.dry_run_service(name="web-svc")
        log = infra_sandbox.get_operations_log()
        assert len(log) == 2
        assert log[0].operation == "create_deployment"
        assert log[1].operation == "create_service"

    def test_destroy(self, infra_sandbox):
        infra_sandbox.dry_run_deployment(name="web", image="nginx:latest")
        infra_sandbox.destroy()
        assert infra_sandbox.is_active is False
        with pytest.raises(RuntimeError, match="destroyed"):
            infra_sandbox.dry_run_deployment(name="web2", image="nginx:latest")


# -- InfrastructureAPI -------------------------------------------------------


class TestInfrastructureAPI:
    def test_post_deployment(self, api):
        body = {"name": "web", "image": "nginx:latest", "replicas": 3}
        resp, status = api.post_deployment(body)
        assert status == 201
        assert resp["name"] == "web"
        assert resp["replicas"] == 3

    def test_post_deployment_missing_field(self, api):
        body = {"name": "web"}
        resp, status = api.post_deployment(body)
        assert status == 400
        assert "error" in resp

    def test_post_deployment_invalid_strategy(self, api):
        body = {"name": "web", "image": "nginx:latest", "strategy": "invalid_strategy"}
        resp, status = api.post_deployment(body)
        assert status == 400
        assert "error" in resp

    def test_post_rollback(self, api):
        body = {"name": "web", "image": "nginx:1.24", "replicas": 2}
        dep_resp, _ = api.post_deployment(body)
        dep_id = dep_resp["id"]

        # Update to have history
        api._dep_engine.update_deployment(dep_id, image="nginx:1.25")

        resp, status = api.post_rollback(dep_id)
        assert status == 200
        assert resp["image"] == "nginx:1.24"

    def test_post_rollback_not_found(self, api):
        resp, status = api.post_rollback("nonexistent")
        assert status == 404

    def test_post_service(self, api):
        body = {
            "name": "web-svc",
            "service_type": "load_balancer",
            "port": 80,
            "target_port": 8080,
        }
        resp, status = api.post_service(body)
        assert status == 201
        assert resp["name"] == "web-svc"
        assert resp["service_type"] == "load_balancer"

    def test_post_service_missing_name(self, api):
        body = {"port": 80}
        resp, status = api.post_service(body)
        assert status == 400

    def test_post_namespace(self, api):
        body = {"name": "production", "quotas": {"cpu_cores": 8.0, "memory_mb": 16384}}
        resp, status = api.post_namespace(body)
        assert status == 201
        assert resp["name"] == "production"

    def test_post_namespace_duplicate(self, api):
        body = {"name": "production"}
        api.post_namespace(body)
        resp, status = api.post_namespace(body)
        assert status == 409

    def test_post_namespace_missing_name(self, api):
        body = {}
        resp, status = api.post_namespace(body)
        assert status == 400

    def test_get_health(self, api):
        resp, status = api.get_health()
        assert status == 200
        assert resp["status"] == "healthy"
        assert resp["is_healthy"] is True
        assert "deployment_engine" in resp["details"]
        assert "service_engine" in resp["details"]
        assert "provisioner" in resp["details"]
