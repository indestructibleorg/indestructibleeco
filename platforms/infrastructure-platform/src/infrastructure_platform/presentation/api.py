"""Infrastructure Platform API.

Provides the following endpoints (in-memory, framework-agnostic):
  POST /deployments
  POST /deployments/{id}/rollback
  POST /services
  POST /namespaces
  GET  /health
"""

from __future__ import annotations

from typing import Any

from platform_shared.protocols.health import HealthReport, HealthStatus
from platform_shared.sandbox.resource import ResourceLimits

from infrastructure_platform.domain.value_objects import DeploymentStrategy, ServiceType
from infrastructure_platform.engines.deployment_engine import DeploymentEngine
from infrastructure_platform.engines.service_engine import ServiceEngine
from infrastructure_platform.engines.provisioner import Provisioner


class InfrastructureAPI:
    """Framework-agnostic API facade for infrastructure operations.

    Each method corresponds to an HTTP endpoint and returns a dict
    representing the JSON response body along with an HTTP status code.
    """

    def __init__(
        self,
        deployment_engine: DeploymentEngine | None = None,
        service_engine: ServiceEngine | None = None,
        provisioner: Provisioner | None = None,
    ) -> None:
        self._dep_engine = deployment_engine or DeploymentEngine()
        self._svc_engine = service_engine or ServiceEngine(
            deployments=self._dep_engine._deployments
        )
        self._provisioner = provisioner or Provisioner()

    # POST /deployments
    def post_deployment(self, body: dict[str, Any]) -> tuple[dict[str, Any], int]:
        """Create a new deployment."""
        try:
            name = body["name"]
            image = body["image"]
            replicas = body.get("replicas", 1)
            strategy_str = body.get("strategy", "rolling")
            strategy = DeploymentStrategy(strategy_str)
            namespace = body.get("namespace", "default")
            labels = body.get("labels", {})

            dep = self._dep_engine.create_deployment(
                name=name,
                image=image,
                replicas=replicas,
                strategy=strategy,
                namespace=namespace,
                labels=labels,
            )
            return dep.to_dict(), 201
        except KeyError as exc:
            return {"error": f"Missing required field: {exc}"}, 400
        except ValueError as exc:
            return {"error": str(exc)}, 400

    # POST /deployments/{id}/rollback
    def post_rollback(self, deployment_id: str) -> tuple[dict[str, Any], int]:
        """Rollback a deployment."""
        try:
            dep = self._dep_engine.rollback(deployment_id)
            return dep.to_dict(), 200
        except Exception as exc:
            return {"error": str(exc)}, 404

    # POST /services
    def post_service(self, body: dict[str, Any]) -> tuple[dict[str, Any], int]:
        """Create a new service."""
        try:
            name = body["name"]
            svc_type_str = body.get("service_type", "cluster_ip")
            svc_type = ServiceType(svc_type_str)
            port = body.get("port", 80)
            target_port = body.get("target_port", 8080)
            selector = body.get("selector", {})
            namespace = body.get("namespace", "default")

            svc = self._svc_engine.create_service(
                name=name,
                service_type=svc_type,
                port=port,
                target_port=target_port,
                selector=selector,
                namespace=namespace,
            )
            return svc.to_dict(), 201
        except KeyError as exc:
            return {"error": f"Missing required field: {exc}"}, 400
        except ValueError as exc:
            return {"error": str(exc)}, 400

    # POST /namespaces
    def post_namespace(self, body: dict[str, Any]) -> tuple[dict[str, Any], int]:
        """Create a new namespace."""
        try:
            name = body["name"]
            quotas_data = body.get("quotas", {})
            quotas = ResourceLimits(
                cpu_cores=quotas_data.get("cpu_cores", 1.0),
                memory_mb=quotas_data.get("memory_mb", 512),
            )
            labels = body.get("labels", {})

            ns = self._provisioner.create_namespace(
                name=name, quotas=quotas, labels=labels
            )
            return ns.to_dict(), 201
        except KeyError as exc:
            return {"error": f"Missing required field: {exc}"}, 400
        except Exception as exc:
            return {"error": str(exc)}, 409

    # GET /health
    def get_health(self) -> tuple[dict[str, Any], int]:
        """Return platform health status."""
        report = HealthReport(
            component="infrastructure-platform",
            status=HealthStatus.HEALTHY,
            message="All engines operational",
            details={
                "deployment_engine": self._dep_engine.status.value,
                "service_engine": self._svc_engine.status.value,
                "provisioner": self._provisioner.status.value,
                "deployments_count": len(self._dep_engine._deployments),
                "services_count": len(self._svc_engine._services),
                "namespaces_count": len(self._provisioner._namespaces),
            },
        )
        return {
            "component": report.component,
            "status": report.status.value,
            "message": report.message,
            "details": report.details,
            "is_healthy": report.is_healthy,
        }, 200
