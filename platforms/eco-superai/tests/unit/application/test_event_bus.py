"""Unit tests for application event bus."""
from __future__ import annotations

import pytest

from src.application.events import EventBus
from src.domain.entities.base import DomainEvent


class TestEventBus:
    @pytest.mark.asyncio
    async def test_publish_calls_handler(self):
        bus = EventBus()
        received = []

        async def handler(event: DomainEvent) -> None:
            received.append(event)

        bus.subscribe("test.event", handler)
        event = DomainEvent(event_type="test.event", aggregate_id="agg-1")
        await bus.publish(event)

        assert len(received) == 1
        assert received[0].aggregate_id == "agg-1"

    @pytest.mark.asyncio
    async def test_multiple_handlers(self):
        bus = EventBus()
        results = []

        async def handler_a(event: DomainEvent) -> None:
            results.append("a")

        async def handler_b(event: DomainEvent) -> None:
            results.append("b")

        bus.subscribe("test.multi", handler_a)
        bus.subscribe("test.multi", handler_b)
        await bus.publish(DomainEvent(event_type="test.multi"))

        assert results == ["a", "b"]

    @pytest.mark.asyncio
    async def test_unsubscribe(self):
        bus = EventBus()
        received = []

        async def handler(event: DomainEvent) -> None:
            received.append(event)

        bus.subscribe("test.unsub", handler)
        bus.unsubscribe("test.unsub", handler)
        await bus.publish(DomainEvent(event_type="test.unsub"))

        assert len(received) == 0

    @pytest.mark.asyncio
    async def test_no_handler_does_not_raise(self):
        bus = EventBus()
        await bus.publish(DomainEvent(event_type="no.handler"))

    @pytest.mark.asyncio
    async def test_handler_error_does_not_propagate(self):
        bus = EventBus()

        async def bad_handler(event: DomainEvent) -> None:
            raise ValueError("handler error")

        bus.subscribe("test.error", bad_handler)
        # Should not raise
        await bus.publish(DomainEvent(event_type="test.error"))

    @pytest.mark.asyncio
    async def test_publish_all(self):
        bus = EventBus()
        received = []

        async def handler(event: DomainEvent) -> None:
            received.append(event.event_type)

        bus.subscribe("a", handler)
        bus.subscribe("b", handler)

        events = [
            DomainEvent(event_type="a"),
            DomainEvent(event_type="b"),
            DomainEvent(event_type="c"),  # no handler
        ]
        await bus.publish_all(events)

        assert received == ["a", "b"]