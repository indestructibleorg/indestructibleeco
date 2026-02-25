"""Health check protocol — liveness / readiness for every component."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, runtime_checkable


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class HealthReport:
    app.kubernetes.io/component: str
    status: HealthStatus
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    checked_at: float = field(default_factory=time.time)
    latency_ms: float = 0.0

    @property
    def is_healthy(self) -> bool:
        return self.status in (HealthStatus.HEALTHY, HealthStatus.DEGRADED)


@runtime_checkable
class HealthCheck(Protocol):
    async def check_health(self) -> HealthReport: ...
    async def check_readiness(self) -> bool: ...
    async def check_liveness(self) -> bool: ...
