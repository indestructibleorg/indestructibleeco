"""Provisioner -- provision namespaces, resource quotas, network policies."""

from __future__ import annotations

from typing import Any

from platform_shared.protocols.engine import EngineStatus
from platform_shared.sandbox.resource import ResourceLimits

from infrastructure_platform.domain.entities import Namespace
from infrastructure_platform.domain.exceptions import (
    InfrastructureError,
    NamespaceExistsError,
)


class Provisioner:
    """Manages infrastructure provisioning -- namespaces, quotas, and network policies.

    All state is in-memory.
    """

    def __init__(self) -> None:
        self._namespaces: dict[str, Namespace] = {}
        self._status = EngineStatus.RUNNING

    @property
    def name(self) -> str:
        return "provisioner"

    @property
    def status(self) -> EngineStatus:
        return self._status

    # -- Namespace operations -------------------------------------------------

    def create_namespace(
        self,
        name: str,
        quotas: ResourceLimits | None = None,
        labels: dict[str, str] | None = None,
    ) -> Namespace:
        """Create a new namespace with optional resource quotas."""
        # Check for duplicates by name
        for ns in self._namespaces.values():
            if ns.name == name:
                raise NamespaceExistsError(name)

        ns = Namespace(
            name=name,
            quotas=quotas or ResourceLimits(),
            labels=labels or {},
        )
        self._namespaces[ns.id] = ns
        return ns

    def get_namespace(self, namespace_id: str) -> Namespace:
        """Get a namespace by id."""
        try:
            return self._namespaces[namespace_id]
        except KeyError:
            raise InfrastructureError(f"Namespace not found: {namespace_id}")

    def get_namespace_by_name(self, name: str) -> Namespace:
        """Get a namespace by name."""
        for ns in self._namespaces.values():
            if ns.name == name:
                return ns
        raise InfrastructureError(f"Namespace not found: {name}")

    def list_namespaces(self) -> list[Namespace]:
        """List all namespaces."""
        return list(self._namespaces.values())

    def delete_namespace(self, namespace_id: str) -> None:
        """Delete a namespace."""
        if namespace_id not in self._namespaces:
            raise InfrastructureError(f"Namespace not found: {namespace_id}")
        del self._namespaces[namespace_id]

    # -- Network policy operations --------------------------------------------

    def apply_network_policy(self, namespace_id: str, policy: str) -> Namespace:
        """Apply a network policy to a namespace."""
        ns = self.get_namespace(namespace_id)
        if policy not in ns.network_policies:
            ns.network_policies.append(policy)
        return ns

    def remove_network_policy(self, namespace_id: str, policy: str) -> Namespace:
        """Remove a network policy from a namespace."""
        ns = self.get_namespace(namespace_id)
        if policy in ns.network_policies:
            ns.network_policies.remove(policy)
        return ns

    def list_network_policies(self, namespace_id: str) -> list[str]:
        """List all network policies for a namespace."""
        ns = self.get_namespace(namespace_id)
        return list(ns.network_policies)
