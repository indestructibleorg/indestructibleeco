"""Shared domain primitives."""

from platform_shared.domain.errors import (
    PlatformError,
    SandboxError,
    ContainerError,
    EnvironmentError as EnvError,
    ResourceExhaustedError,
    TimeoutExpiredError,
    IsolationViolationError,
)
from platform_shared.domain.platform_id import PlatformId
from platform_shared.domain.version import SemVer

__all__ = [
    "PlatformError",
    "SandboxError",
    "ContainerError",
    "EnvError",
    "ResourceExhaustedError",
    "TimeoutExpiredError",
    "IsolationViolationError",
    "PlatformId",
    "SemVer",
]
