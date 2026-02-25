"""Application event bus — dispatches domain events to handlers."""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Coroutine

import structlog

from src.domain.entities.base import DomainEvent

logger = structlog.get_logger(__name__)

EventHandler = Callable[[DomainEvent], Coroutine[Any, Any, None]]


class EventBus:
    """In-process async event bus for domain event dispatching."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        self._handlers[event_type].append(handler)
        logger.debug("event_handler_registered", event_type=event_type, handler=handler.__name__)

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        if event_type in self._handlers:
            self._handlers[event_type] = [h for h in self._handlers[event_type] if h != handler]

    async def publish(self, event: DomainEvent) -> None:
        event_type = event.event_type
        handlers = self._handlers.get(event_type, [])
        logger.info("event_published", event_type=event_type, event_id=event.event_id, handler_count=len(handlers))

        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(
                    "event_handler_failed",
                    event_type=event_type,
                    event_id=event.event_id,
                    handler=handler.__name__,
                    error=str(e),
                )

    async def publish_all(self, events: list[DomainEvent]) -> None:
        for event in events:
            await self.publish(event)


# --- Singleton ---
_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
        _register_default_handlers(_event_bus)
    return _event_bus


def _register_default_handlers(bus: EventBus) -> None:
    """Register built-in event handlers."""

    async def log_user_created(event: DomainEvent) -> None:
        logger.info("user_created", user_id=event.aggregate_id, payload=event.payload)

    async def log_user_authenticated(event: DomainEvent) -> None:
        logger.info("user_authenticated", user_id=event.aggregate_id)

    async def log_user_auth_failed(event: DomainEvent) -> None:
        logger.warning("user_auth_failed", payload=event.payload)

    async def log_quantum_job(event: DomainEvent) -> None:
        logger.info("quantum_job_event", event_type=event.event_type, job_id=event.aggregate_id)

    bus.subscribe("user.created", log_user_created)
    bus.subscribe("user.authenticated", log_user_authenticated)
    bus.subscribe("user.auth_failed", log_user_auth_failed)
    bus.subscribe("quantum.job_submitted", log_quantum_job)
    bus.subscribe("quantum.job_completed", log_quantum_job)


__all__ = ["EventBus", "get_event_bus"]