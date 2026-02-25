"""InfraSandbox -- run infrastructure operations in sandbox (dry-run mode).

Provides a sandboxed environment where infrastructure changes can be
validated without applying them to the real cluster.  All operations
are executed against an ephemeral in-memory state that is discarded
when the sandbox is torn down.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from platform_shared.sandbox.resource import ResourceLimits

from infrastructure_platform.domain.entities import Deployment, Namespace, Service
from infrastructure_platform.domain.value_objects import DeploymentStrategy, ServiceType
from infrastructure_platform.engines.deployment_engine import DeploymentEngine
from infrastructure_platform.engines.service_engine import ServiceEngine
from infrastructure_platform.engines.provisioner import Provisioner


@dataclass(slots=True)
class SandboxResult:
    """Result of a sandbox dry-run operation."""

    sandbox_id: str
    operation: str
    success: bool
    result: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class InfraSandbox:
    """Run infrastructure operations in an isolated sandbox for dry-run validation.

    Creates isolated engine instances whose state does not affect the
    real infrastructure.  Useful for plan/preview workflows.
    """

    def __init__(self) -> None:
        self._sandbox_id = f"infra-sb-{uuid.uuid4().hex[:12]}"
        self._deployment_engine = DeploymentEngine()
        self._service_engine = ServiceEngine(
            deployments=self._deployment_engine._deployments
        )
        self._provisioner = Provisioner()
        self._operations_log: list[SandboxResult] = []
        self._active = True

    @property
    def sandbox_id(self) -> str:
        return self._sandbox_id

    @property
    def is_active(self) -> bool:
        return self._active

    def dry_run_deployment(
        self,
        name: str,
        image: str,
        replicas: int = 1,
        strategy: DeploymentStrategy = DeploymentStrategy.ROLLING,
    ) -> SandboxResult:
        """Simulate creating a deployment without applying it."""
        self._check_active()
        errors: list[str] = []
        warnings: list[str] = []
        result_data: dict[str, Any] = {}

        # Validate inputs
        if not name:
            errors.append("Deployment name is required")
        if not image:
            errors.append("Image is required")
        if replicas < 1:
            errors.append("Replicas must be at least 1")
        if replicas > 100:
            warnings.append(f"High replica count ({replicas}) may exhaust resources")

        if not errors:
            dep = self._deployment_engine.create_deployment(
                name=name, image=image, replicas=replicas, strategy=strategy
            )
            result_data = dep.to_dict()

        result = SandboxResult(
            sandbox_id=self._sandbox_id,
            operation="create_deployment",
            success=len(errors) == 0,
            result=result_data,
            errors=errors,
            warnings=warnings,
        )
        self._operations_log.append(result)
        return result

    def dry_run_service(
        self,
        name: str,
        service_type: ServiceType = ServiceType.CLUSTER_IP,
        port: int = 80,
        target_port: int = 8080,
    ) -> SandboxResult:
        """Simulate creating a service without applying it."""
        self._check_active()
        errors: list[str] = []
        warnings: list[str] = []
        result_data: dict[str, Any] = {}

        if not name:
            errors.append("Service name is required")
        if port < 1 or port > 65535:
            errors.append(f"Invalid port: {port}")
        if target_port < 1 or target_port > 65535:
            errors.append(f"Invalid target port: {target_port}")

        if not errors:
            svc = self._service_engine.create_service(
                name=name,
                service_type=service_type,
                port=port,
                target_port=target_port,
            )
            result_data = svc.to_dict()

        result = SandboxResult(
            sandbox_id=self._sandbox_id,
            operation="create_service",
            success=len(errors) == 0,
            result=result_data,
            errors=errors,
            warnings=warnings,
        )
        self._operations_log.append(result)
        return result

    def dry_run_namespace(
        self,
        name: str,
        quotas: ResourceLimits | None = None,
    ) -> SandboxResult:
        """Simulate creating a namespace without applying it."""
        self._check_active()
        errors: list[str] = []
        warnings: list[str] = []
        result_data: dict[str, Any] = {}

        if not name:
            errors.append("Namespace name is required")

        if not errors:
            try:
                ns = self._provisioner.create_namespace(name=name, quotas=quotas)
                result_data = ns.to_dict()
            except Exception as exc:
                errors.append(str(exc))

        result = SandboxResult(
            sandbox_id=self._sandbox_id,
            operation="create_namespace",
            success=len(errors) == 0,
            result=result_data,
            errors=errors,
            warnings=warnings,
        )
        self._operations_log.append(result)
        return result

    def get_operations_log(self) -> list[SandboxResult]:
        """Return a log of all operations performed in this sandbox."""
        return list(self._operations_log)

    def destroy(self) -> None:
        """Tear down the sandbox -- discards all state."""
        self._active = False
        self._operations_log.clear()

    def _check_active(self) -> None:
        if not self._active:
            raise RuntimeError("Sandbox has been destroyed")
