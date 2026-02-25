"""Domain events — things that happened in the data platform."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class EvidenceIngested:
    """Raised when a new evidence record has been ingested and hashed."""

    evidence_id: str
    evidence_type: str
    hash: str
    parent_id: str | None = None
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    timestamp: float = field(default_factory=time.time)


@dataclass(frozen=True, slots=True)
class QualityChecked:
    """Raised when a data quality evaluation has completed."""

    rule_count: int
    overall_score: float
    passed: bool
    details: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    timestamp: float = field(default_factory=time.time)


@dataclass(frozen=True, slots=True)
class ReplayCompleted:
    """Raised when a replay session finishes playing all events."""

    session_id: str
    total_events: int
    final_position: int
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    timestamp: float = field(default_factory=time.time)
