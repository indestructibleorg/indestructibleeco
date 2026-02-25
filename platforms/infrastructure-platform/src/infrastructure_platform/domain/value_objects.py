"""Value objects for infrastructure domain."""

from __future__ import annotations

from enum import Enum


class DeploymentStrategy(str, Enum):
    """Deployment rollout strategy."""

    ROLLING = "rolling"
    BLUE_GREEN = "blue_green"
    CANARY = "canary"


class ServiceType(str, Enum):
    """Kubernetes-style service types."""

    CLUSTER_IP = "cluster_ip"
    NODE_PORT = "node_port"
    LOAD_BALANCER = "load_balancer"


class NodeStatus(str, Enum):
    """Lifecycle status of a cluster node."""

    PENDING = "pending"
    READY = "ready"
    NOT_READY = "not_ready"
    CORDONED = "cordoned"
    DRAINING = "draining"
    TERMINATED = "terminated"
