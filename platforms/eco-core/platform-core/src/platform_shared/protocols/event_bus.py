"""Event bus protocol — decentralized, async event communication between platforms."""

from __future__ import annotations

import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class Event:
    topic: str
    payload: dict[str, Any]
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    source: str = ""
    timestamp: float = field(default_factory=time.time)

EventHandler = Callable[[Event], Awaitable[None]]


@runtime_checkable
class EventBus(Protocol):
    async def publish(self, event: Event) -> None: ...
    def subscribe(self, topic: str, handler: EventHandler) -> None: ...
    def unsubscribe(self, topic: str, handler: EventHandler) -> None: ...


class LocalEventBus:
    """In-process event bus (single-node, for dev/test)."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._history: list[Event] = []

    async def publish(self, event: Event) -> None:
        self._history.append(event)
        for handler in self._handlers.get(event.topic, []):
            await handler(event)

    def subscribe(self, topic: str, handler: EventHandler) -> None:
        self._handlers[topic].append(handler)

    def unsubscribe(self, topic: str, handler: EventHandler) -> None:
        handlers = self._handlers.get(topic, [])
        if handler in handlers:
            handlers.remove(handler)

    @property
    def history(self) -> list[Event]:
        return list(self._history)
