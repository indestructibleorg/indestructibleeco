"""Base error hierarchy for the platform ecosystem."""

from __future__ import annotations


class PlatformError(Exception):
    """Root of all platform errors."""

    def __init__(self, message: str, *, code: str = "PLATFORM_ERROR", context: dict | None = None):
        super().__init__(message)
        self.code = code
        self.context = context or {}


class SandboxError(PlatformError):
    """Sandbox lifecycle or execution failure."""

    def __init__(self, message: str, *, sandbox_id: str = "", **kw):
        super().__init__(message, code="SANDBOX_ERROR", **kw)
        self.sandbox_id = sandbox_id


class ContainerError(PlatformError):
    """Container runtime failure."""

    def __init__(self, message: str, *, container_id: str = "", **kw):
        super().__init__(message, code="CONTAINER_ERROR", **kw)
        self.container_id = container_id


class EnvironmentError(PlatformError):  # noqa: A001 — intentional shadow
    """Environment management failure."""

    def __init__(self, message: str, *, env_id: str = "", **kw):
        super().__init__(message, code="ENVIRONMENT_ERROR", **kw)
        self.env_id = env_id


class ResourceExhaustedError(SandboxError):
    """CPU, memory, or fd limit exceeded inside a sandbox."""

    def __init__(self, resource: str, limit: float, actual: float, **kw):
        super().__init__(
            f"{resource} exhausted: limit={limit}, actual={actual}", code="RESOURCE_EXHAUSTED", **kw
        )
        self.resource = resource
        self.limit = limit
        self.actual = actual


class TimeoutExpiredError(SandboxError):
    """Execution exceeded its time budget."""

    def __init__(self, timeout_seconds: float, **kw):
        super().__init__(
            f"Execution timed out after {timeout_seconds}s", code="TIMEOUT_EXPIRED", **kw
        )
        self.timeout_seconds = timeout_seconds


class IsolationViolationError(SandboxError):
    """An operation attempted to escape its isolation boundary."""

    def __init__(self, violation: str, **kw):
        super().__init__(
            f"Isolation violation: {violation}", code="ISOLATION_VIOLATION", **kw
        )
        self.violation = violation
