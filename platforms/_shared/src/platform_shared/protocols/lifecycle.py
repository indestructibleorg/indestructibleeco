"""Lifecycle protocol — startup / shutdown ordering for platform components."""

from __future__ import annotations

from enum import Enum
from typing import Protocol, runtime_checkable


class LifecycleState(str, Enum):
    NEW = "new"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    SHUTTING_DOWN = "shutting_down"
    TERMINATED = "terminated"


@runtime_checkable
class Lifecycle(Protocol):
    @property
    def state(self) -> LifecycleState: ...

    async def initialize(self) -> None:
        """One-time setup (connections, caches, warmup)."""
        ...

    async def start(self) -> None:
        """Begin processing work."""
        ...

    async def stop(self) -> None:
        """Graceful shutdown — drain in-flight work, close connections."""
        ...

    async def terminate(self) -> None:
        """Force stop — called when graceful shutdown times out."""
        ...
