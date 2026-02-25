"""Domain events for infrastructure platform."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from platform_shared.protocols.event_bus import Event


def _make_infra_event(topic: str, payload: dict[str, Any], source: str = "infrastructure-platform") -> Event:
    """Helper to create infrastructure events."""
    return Event(topic=topic, payload=payload, source=source)


@dataclass(frozen=True, slots=True)
class DeploymentCreated:
    deployment_id: str
    name: str
    image: str
    replicas: int

    def to_event(self) -> Event:
        return _make_infra_event(
            "infrastructure.deployment.created",
            {
                "deployment_id": self.deployment_id,
                "name": self.name,
                "image": self.image,
                "replicas": self.replicas,
            },
        )


@dataclass(frozen=True, slots=True)
class ServiceExposed:
    service_id: str
    name: str
    port: int
    deployment_id: str = ""

    def to_event(self) -> Event:
        return _make_infra_event(
            "infrastructure.service.exposed",
            {
                "service_id": self.service_id,
                "name": self.name,
                "port": self.port,
                "deployment_id": self.deployment_id,
            },
        )


@dataclass(frozen=True, slots=True)
class NodeJoined:
    node_id: str
    name: str
    ip_address: str

    def to_event(self) -> Event:
        return _make_infra_event(
            "infrastructure.node.joined",
            {
                "node_id": self.node_id,
                "name": self.name,
                "ip_address": self.ip_address,
            },
        )


@dataclass(frozen=True, slots=True)
class RollbackTriggered:
    deployment_id: str
    from_version: int
    to_version: int
    reason: str = ""

    def to_event(self) -> Event:
        return _make_infra_event(
            "infrastructure.deployment.rollback",
            {
                "deployment_id": self.deployment_id,
                "from_version": self.from_version,
                "to_version": self.to_version,
                "reason": self.reason,
            },
        )
