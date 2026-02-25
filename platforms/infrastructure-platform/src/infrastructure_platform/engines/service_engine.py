"""ServiceEngine -- expose services, manage endpoints, load balancing."""

from __future__ import annotations

from typing import Any

from platform_shared.protocols.engine import EngineStatus
from platform_shared.protocols.event_bus import LocalEventBus

from infrastructure_platform.domain.entities import Deployment, Service
from infrastructure_platform.domain.exceptions import (
    DeploymentNotFoundError,
    ServiceNotFoundError,
)
from infrastructure_platform.domain.value_objects import ServiceType


class ServiceEngine:
    """Manages service resources -- create, expose, and track endpoints.

    Works in tandem with the DeploymentEngine to automatically
    create services for deployments.
    """

    def __init__(
        self,
        deployments: dict[str, Deployment] | None = None,
        event_bus: LocalEventBus | None = None,
    ) -> None:
        self._services: dict[str, Service] = {}
        self._deployments = deployments if deployments is not None else {}
        self._event_bus = event_bus or LocalEventBus()
        self._status = EngineStatus.RUNNING

    @property
    def name(self) -> str:
        return "service-engine"

    @property
    def status(self) -> EngineStatus:
        return self._status

    # -- Core operations ------------------------------------------------------

    def create_service(
        self,
        name: str,
        service_type: ServiceType = ServiceType.CLUSTER_IP,
        port: int = 80,
        target_port: int = 8080,
        selector: dict[str, str] | None = None,
        namespace: str = "default",
    ) -> Service:
        """Create a new service."""
        svc = Service(
            name=name,
            service_type=service_type,
            port=port,
            target_port=target_port,
            selector=selector or {},
            namespace=namespace,
        )
        # Generate synthetic endpoints based on selector matches
        svc.endpoints = self._resolve_endpoints(svc.selector)
        self._services[svc.id] = svc
        return svc

    def expose(self, deployment_id: str, port: int = 80, target_port: int = 8080) -> Service:
        """Create a service that fronts a specific deployment."""
        if deployment_id not in self._deployments:
            raise DeploymentNotFoundError(deployment_id)

        dep = self._deployments[deployment_id]
        svc = Service(
            name=f"{dep.name}-svc",
            service_type=ServiceType.CLUSTER_IP,
            port=port,
            target_port=target_port,
            selector={"app": dep.name},
            namespace=dep.namespace,
            deployment_id=deployment_id,
        )
        # Generate endpoints -- one per replica
        svc.endpoints = [
            f"{dep.name}-{i}.{dep.namespace}.svc.cluster.local:{target_port}"
            for i in range(dep.replicas)
        ]
        self._services[svc.id] = svc
        return svc

    def get_service(self, service_id: str) -> Service:
        """Retrieve a service by id."""
        try:
            return self._services[service_id]
        except KeyError:
            raise ServiceNotFoundError(service_id)

    def list_services(self, namespace: str | None = None) -> list[Service]:
        """List all services, optionally filtered by namespace."""
        results = list(self._services.values())
        if namespace is not None:
            results = [s for s in results if s.namespace == namespace]
        return results

    def list_endpoints(self, service_id: str) -> list[str]:
        """Return the endpoint list for a service."""
        svc = self.get_service(service_id)
        return list(svc.endpoints)

    def delete_service(self, service_id: str) -> None:
        """Remove a service."""
        if service_id not in self._services:
            raise ServiceNotFoundError(service_id)
        del self._services[service_id]

    # -- Internals ------------------------------------------------------------

    def _resolve_endpoints(self, selector: dict[str, str]) -> list[str]:
        """Resolve endpoints from deployments matching the selector.

        This is a simplified in-memory lookup that matches deployment labels.
        """
        endpoints: list[str] = []
        if not selector:
            return endpoints

        for dep in self._deployments.values():
            if all(dep.labels.get(k) == v for k, v in selector.items()):
                for i in range(dep.replicas):
                    endpoints.append(
                        f"{dep.name}-{i}.{dep.namespace}.svc.cluster.local:8080"
                    )
        return endpoints
