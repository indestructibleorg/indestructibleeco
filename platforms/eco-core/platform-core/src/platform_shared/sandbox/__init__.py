"""Sandbox / Container / Environment — the three isolation pillars."""

from platform_shared.sandbox.runtime import (
    SandboxConfig,
    SandboxStatus,
    ExecutionResult,
    SandboxRuntime,
    ProcessSandbox,
)
from platform_shared.sandbox.container import (
    ContainerConfig,
    ContainerStatus,
    ContainerInfo,
    ExecResult,
    HealthCheckConfig,
    ContainerRuntime,
    LocalContainerRuntime,
)
from platform_shared.sandbox.environment import (
    EnvironmentProfile,
    EnvironmentStatus,
    ServiceEndpoint,
    EnvironmentManager,
    LocalEnvironmentManager,
)
from platform_shared.sandbox.resource import ResourceLimits, ResourceSnapshot, ResourceMonitor
from platform_shared.sandbox.network import NetworkPolicy, NetworkRule, NetworkNamespace
from platform_shared.sandbox.storage import VolumeMount, VolumeType, VolumeManager

__all__ = [
    # Runtime / Sandbox
    "SandboxConfig",
    "SandboxStatus",
    "ExecutionResult",
    "SandboxRuntime",
    "ProcessSandbox",
    # Container
    "ContainerConfig",
    "ContainerStatus",
    "ContainerInfo",
    "ExecResult",
    "HealthCheckConfig",
    "ContainerRuntime",
    "LocalContainerRuntime",
    # Environment
    "EnvironmentProfile",
    "EnvironmentStatus",
    "ServiceEndpoint",
    "EnvironmentManager",
    "LocalEnvironmentManager",
    # Resource
    "ResourceLimits",
    "ResourceSnapshot",
    "ResourceMonitor",
    # Network
    "NetworkPolicy",
    "NetworkRule",
    "NetworkNamespace",
    # Storage
    "VolumeMount",
    "VolumeType",
    "VolumeManager",
]
