"""Domain entities for infrastructure platform."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from infrastructure_platform.domain.value_objects import (
    DeploymentStrategy,
    NodeStatus,
    ServiceType,
)
from platform_shared.sandbox.resource import ResourceLimits


@dataclass(slots=True)
class Deployment:
    """Represents a workload deployment."""

    id: str = field(default_factory=lambda: f"deploy-{uuid.uuid4().hex[:12]}")
    name: str = ""
    image: str = ""
    replicas: int = 1
    strategy: DeploymentStrategy = DeploymentStrategy.ROLLING
    namespace: str = "default"
    labels: dict[str, str] = field(default_factory=dict)
    version: int = 1
    active_color: str = "blue"  # for blue/green
    previous_image: str = ""
    previous_replicas: int = 0
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    status: str = "running"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "image": self.image,
            "replicas": self.replicas,
            "strategy": self.strategy.value,
            "namespace": self.namespace,
            "labels": self.labels,
            "version": self.version,
            "active_color": self.active_color,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass(slots=True)
class Service:
    """Represents a network service (load balancer, cluster IP, etc.)."""

    id: str = field(default_factory=lambda: f"svc-{uuid.uuid4().hex[:12]}")
    name: str = ""
    service_type: ServiceType = ServiceType.CLUSTER_IP
    port: int = 80
    target_port: int = 8080
    selector: dict[str, str] = field(default_factory=dict)
    namespace: str = "default"
    endpoints: list[str] = field(default_factory=list)
    deployment_id: str = ""
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "service_type": self.service_type.value,
            "port": self.port,
            "target_port": self.target_port,
            "selector": self.selector,
            "namespace": self.namespace,
            "endpoints": self.endpoints,
            "deployment_id": self.deployment_id,
            "created_at": self.created_at,
        }


@dataclass(slots=True)
class Node:
    """Represents a cluster node."""

    id: str = field(default_factory=lambda: f"node-{uuid.uuid4().hex[:12]}")
    name: str = ""
    status: NodeStatus = NodeStatus.PENDING
    ip_address: str = ""
    labels: dict[str, str] = field(default_factory=dict)
    capacity: ResourceLimits = field(default_factory=ResourceLimits)
    joined_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "ip_address": self.ip_address,
            "labels": self.labels,
            "joined_at": self.joined_at,
        }


@dataclass(slots=True)
class Namespace:
    """Represents a Kubernetes-style namespace with resource quotas."""

    id: str = field(default_factory=lambda: f"ns-{uuid.uuid4().hex[:12]}")
    name: str = ""
    quotas: ResourceLimits = field(default_factory=ResourceLimits)
    labels: dict[str, str] = field(default_factory=dict)
    network_policies: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "quotas": {
                "cpu_cores": self.quotas.cpu_cores,
                "memory_mb": self.quotas.memory_mb,
            },
            "labels": self.labels,
            "network_policies": self.network_policies,
            "created_at": self.created_at,
        }


@dataclass(slots=True)
class HelmRelease:
    """Represents a Helm chart release."""

    id: str = field(default_factory=lambda: f"helm-{uuid.uuid4().hex[:12]}")
    name: str = ""
    chart: str = ""
    version: str = "1.0.0"
    namespace: str = "default"
    values: dict[str, Any] = field(default_factory=dict)
    status: str = "deployed"
    revision: int = 1
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "chart": self.chart,
            "version": self.version,
            "namespace": self.namespace,
            "status": self.status,
            "revision": self.revision,
            "created_at": self.created_at,
        }
