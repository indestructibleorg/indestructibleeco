"""Engine protocol — the universal contract for all platform engines."""

from __future__ import annotations

from enum import Enum
from typing import Any, Protocol, runtime_checkable


class EngineStatus(str, Enum):
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@runtime_checkable
class Engine(Protocol):
    """Every platform engine implements this interface."""

    @property
    def name(self) -> str: ...

    @property
    def status(self) -> EngineStatus: ...

    async def start(self) -> None: ...

    async def stop(self) -> None: ...

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]: ...
