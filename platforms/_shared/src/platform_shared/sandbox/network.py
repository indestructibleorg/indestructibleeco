"""Network isolation primitives — policies, rules, namespaces."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum


class NetworkAction(str, Enum):
    ALLOW = "allow"
    DENY = "deny"


class NetworkDirection(str, Enum):
    INGRESS = "ingress"
    EGRESS = "egress"
    BOTH = "both"


@dataclass(frozen=True, slots=True)
class NetworkRule:
    """Single network rule (firewall-style)."""

    direction: NetworkDirection
    action: NetworkAction
    port: int | None = None
    protocol: str = "tcp"
    cidr: str = "0.0.0.0/0"
    description: str = ""


@dataclass(frozen=True, slots=True)
class NetworkPolicy:
    """Ordered set of rules with a default action."""

    name: str
    default_action: NetworkAction = NetworkAction.DENY
    rules: tuple[NetworkRule, ...] = ()

    def allows(self, direction: NetworkDirection, port: int) -> bool:
        for rule in self.rules:
            if rule.direction in (direction, NetworkDirection.BOTH):
                if rule.port is None or rule.port == port:
                    return rule.action == NetworkAction.ALLOW
        return self.default_action == NetworkAction.ALLOW


# -- Pre-built policies -------------------------------------------------------

POLICY_NO_NETWORK = NetworkPolicy(name="no-network", default_action=NetworkAction.DENY)

POLICY_ALLOW_ALL = NetworkPolicy(name="allow-all", default_action=NetworkAction.ALLOW)

POLICY_EGRESS_ONLY = NetworkPolicy(
    name="egress-only",
    default_action=NetworkAction.DENY,
    rules=(
        NetworkRule(
            direction=NetworkDirection.EGRESS,
            action=NetworkAction.ALLOW,
            description="Allow all outbound",
        ),
    ),
)

POLICY_HTTP_ONLY = NetworkPolicy(
    name="http-only",
    default_action=NetworkAction.DENY,
    rules=(
        NetworkRule(direction=NetworkDirection.BOTH, action=NetworkAction.ALLOW, port=80),
        NetworkRule(direction=NetworkDirection.BOTH, action=NetworkAction.ALLOW, port=443),
    ),
)


@dataclass(slots=True)
class NetworkNamespace:
    """Represents an isolated network namespace for a sandbox."""

    ns_id: str = field(default_factory=lambda: f"ns-{uuid.uuid4().hex[:12]}")
    policy: NetworkPolicy = field(default_factory=lambda: POLICY_NO_NETWORK)
    veth_pair: tuple[str, str] = ("", "")
    bridge: str = ""
    dns_servers: list[str] = field(default_factory=lambda: ["127.0.0.1"])

    @property
    def is_isolated(self) -> bool:
        return self.policy.default_action == NetworkAction.DENY

    def apply_policy(self, policy: NetworkPolicy) -> None:
        object.__setattr__(self, "policy", policy) if hasattr(self, "__dataclass_fields__") else None
        self.policy = policy
