"""Cross-cutting protocols — every platform engine must satisfy these."""

from platform_shared.protocols.engine import Engine, EngineStatus
from platform_shared.protocols.event_bus import EventBus, Event, EventHandler
from platform_shared.protocols.health import HealthCheck, HealthStatus, HealthReport
from platform_shared.protocols.lifecycle import Lifecycle, LifecycleState

__all__ = [
    "Engine",
    "EngineStatus",
    "EventBus",
    "Event",
    "EventHandler",
    "HealthCheck",
    "HealthStatus",
    "HealthReport",
    "Lifecycle",
    "LifecycleState",
]
