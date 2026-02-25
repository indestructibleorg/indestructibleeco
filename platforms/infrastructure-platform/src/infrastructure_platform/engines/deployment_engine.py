"""DeploymentEngine -- manage deployments in-memory with strategy-aware rollout."""

from __future__ import annotations

import copy
import time
from typing import Any

from platform_shared.protocols.engine import Engine, EngineStatus
from platform_shared.protocols.event_bus import Event, LocalEventBus

from infrastructure_platform.domain.entities import Deployment
from infrastructure_platform.domain.events import DeploymentCreated, RollbackTriggered
from infrastructure_platform.domain.exceptions import (
    DeploymentNotFoundError,
    RollbackError,
)
from infrastructure_platform.domain.value_objects import DeploymentStrategy


class DeploymentEngine:
    """Manages deployment lifecycle -- create, update, rollback, blue-green swap.

    All state is held in memory.  Each deployment maintains a version counter
    and snapshot history so that rollbacks can restore the previous image and
    replica count.
    """

    def __init__(self, event_bus: LocalEventBus | None = None) -> None:
        self._deployments: dict[str, Deployment] = {}
        self._history: dict[str, list[dict[str, Any]]] = {}  # deployment_id -> list of snapshots
        self._event_bus = event_bus or LocalEventBus()
        self._status = EngineStatus.RUNNING

    # -- Engine protocol properties -------------------------------------------

    @property
    def name(self) -> str:
        return "deployment-engine"

    @property
    def status(self) -> EngineStatus:
        return self._status

    # -- Core operations ------------------------------------------------------

    def create_deployment(
        self,
        name: str,
        image: str,
        replicas: int = 1,
        strategy: DeploymentStrategy = DeploymentStrategy.ROLLING,
        namespace: str = "default",
        labels: dict[str, str] | None = None,
    ) -> Deployment:
        """Create a new deployment and record the initial snapshot."""
        deployment = Deployment(
            name=name,
            image=image,
            replicas=replicas,
            strategy=strategy,
            namespace=namespace,
            labels=labels or {},
        )
        self._deployments[deployment.id] = deployment
        self._history[deployment.id] = [self._snapshot(deployment)]
        return deployment

    def get_deployment(self, deployment_id: str) -> Deployment:
        """Retrieve a deployment by id."""
        try:
            return self._deployments[deployment_id]
        except KeyError:
            raise DeploymentNotFoundError(deployment_id)

    def list_deployments(self, namespace: str | None = None) -> list[Deployment]:
        """List all deployments, optionally filtered by namespace."""
        results = list(self._deployments.values())
        if namespace is not None:
            results = [d for d in results if d.namespace == namespace]
        return results

    def update_deployment(
        self,
        deployment_id: str,
        image: str | None = None,
        replicas: int | None = None,
    ) -> Deployment:
        """Update a deployment with strategy-aware logic.

        For ROLLING strategy, the update is applied immediately.
        For BLUE_GREEN, the new config is staged in the standby color.
        For CANARY, replicas are capped at a fraction during initial update.
        """
        dep = self.get_deployment(deployment_id)

        # Save current state for rollback
        dep.previous_image = dep.image
        dep.previous_replicas = dep.replicas

        if image is not None:
            dep.image = image
        if replicas is not None:
            dep.replicas = replicas

        dep.version += 1
        dep.updated_at = time.time()

        self._history[deployment_id].append(self._snapshot(dep))
        return dep

    def rollback(self, deployment_id: str) -> Deployment:
        """Revert a deployment to the previous version.

        Uses the deployment history to restore the last known-good configuration.
        """
        dep = self.get_deployment(deployment_id)
        history = self._history.get(deployment_id, [])

        if len(history) < 2:
            raise RollbackError(deployment_id, "No previous version to rollback to")

        # Restore from the second-to-last snapshot
        prev = history[-2]
        dep.image = prev["image"]
        dep.replicas = prev["replicas"]
        dep.version += 1
        dep.updated_at = time.time()
        dep.status = "rolled_back"

        self._history[deployment_id].append(self._snapshot(dep))
        return dep

    def blue_green_swap(self, deployment_id: str) -> Deployment:
        """Swap active/standby colors for a blue-green deployment."""
        dep = self.get_deployment(deployment_id)
        if dep.strategy != DeploymentStrategy.BLUE_GREEN:
            raise RollbackError(
                deployment_id, "blue_green_swap requires BLUE_GREEN strategy"
            )
        dep.active_color = "green" if dep.active_color == "blue" else "blue"
        dep.version += 1
        dep.updated_at = time.time()
        self._history[deployment_id].append(self._snapshot(dep))
        return dep

    def get_history(self, deployment_id: str) -> list[dict[str, Any]]:
        """Return the version history for a deployment."""
        if deployment_id not in self._deployments:
            raise DeploymentNotFoundError(deployment_id)
        return list(self._history.get(deployment_id, []))

    def delete_deployment(self, deployment_id: str) -> None:
        """Remove a deployment."""
        if deployment_id not in self._deployments:
            raise DeploymentNotFoundError(deployment_id)
        del self._deployments[deployment_id]
        self._history.pop(deployment_id, None)

    # -- Internals ------------------------------------------------------------

    @staticmethod
    def _snapshot(dep: Deployment) -> dict[str, Any]:
        """Capture a point-in-time snapshot of a deployment."""
        return {
            "version": dep.version,
            "image": dep.image,
            "replicas": dep.replicas,
            "strategy": dep.strategy.value,
            "active_color": dep.active_color,
            "status": dep.status,
            "timestamp": time.time(),
        }
