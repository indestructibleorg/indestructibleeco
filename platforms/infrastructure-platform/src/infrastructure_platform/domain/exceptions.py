"""Domain exceptions for infrastructure platform."""

from __future__ import annotations

from platform_shared.domain.errors import PlatformError


class InfrastructureError(PlatformError):
    """Base error for all infrastructure platform operations."""

    def __init__(self, message: str, **kw):
        super().__init__(message, code="INFRASTRUCTURE_ERROR", **kw)


class DeploymentNotFoundError(InfrastructureError):
    """Raised when a deployment cannot be found."""

    def __init__(self, deployment_id: str):
        super().__init__(f"Deployment not found: {deployment_id}")
        self.deployment_id = deployment_id


class ServiceNotFoundError(InfrastructureError):
    """Raised when a service cannot be found."""

    def __init__(self, service_id: str):
        super().__init__(f"Service not found: {service_id}")
        self.service_id = service_id


class NodeNotFoundError(InfrastructureError):
    """Raised when a node cannot be found."""

    def __init__(self, node_id: str):
        super().__init__(f"Node not found: {node_id}")
        self.node_id = node_id


class RollbackError(InfrastructureError):
    """Raised when a rollback operation fails."""

    def __init__(self, deployment_id: str, reason: str = ""):
        msg = f"Rollback failed for deployment {deployment_id}"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)
        self.deployment_id = deployment_id


class NamespaceExistsError(InfrastructureError):
    """Raised when attempting to create a namespace that already exists."""

    def __init__(self, name: str):
        super().__init__(f"Namespace already exists: {name}")
        self.namespace_name = name
