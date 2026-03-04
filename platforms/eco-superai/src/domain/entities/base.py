from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import uuid

@dataclass(frozen=True)
class ValueObject:
    pass

@dataclass
class Entity:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1

@dataclass
class DomainEvent:
    occurred_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class AggregateRoot(Entity):
    _domain_events: List[DomainEvent] = field(default_factory=list, repr=False)

    def add_domain_event(self, event: DomainEvent) -> None:
        self._domain_events.append(event)

    def clear_domain_events(self) -> None:
        self._domain_events.clear()

    def get_domain_events(self) -> List[DomainEvent]:
        return self._domain_events.copy()

@dataclass
class BaseEntity(Entity):
    pass
