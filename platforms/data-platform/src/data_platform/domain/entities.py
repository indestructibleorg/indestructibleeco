"""Domain entities — mutable objects with identity."""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from data_platform.domain.value_objects import (
    EvidenceType,
    PipelinePhase,
    ReplayMode,
)


@dataclass(slots=True)
class EvidenceRecord:
    """A single piece of evidence in an auditable chain.

    Each record has a SHA-256 hash computed from its payload,
    and can optionally reference a parent record to form a chain.
    """

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    type: EvidenceType = EvidenceType.EVENT
    payload: dict[str, Any] = field(default_factory=dict)
    hash: str = ""
    parent_id: str | None = None
    timestamp: float = field(default_factory=time.time)

    def compute_hash(self) -> str:
        """Compute SHA-256 hash from payload + parent_id + type."""
        content = json.dumps(self.payload, sort_keys=True, default=str)
        raw = f"{self.type.value}:{self.parent_id or ''}:{content}"
        self.hash = hashlib.sha256(raw.encode()).hexdigest()
        return self.hash

    def verify_hash(self) -> bool:
        """Verify that the stored hash matches a fresh computation."""
        content = json.dumps(self.payload, sort_keys=True, default=str)
        raw = f"{self.type.value}:{self.parent_id or ''}:{content}"
        expected = hashlib.sha256(raw.encode()).hexdigest()
        return self.hash == expected


@dataclass(slots=True)
class DataPipeline:
    """A data pipeline with ordered phases and lifecycle status."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    name: str = ""
    phases: list[PipelinePhase] = field(default_factory=list)
    status: str = "idle"

    def advance(self) -> PipelinePhase | None:
        """Move to the next phase, returning it (or None if done)."""
        current_idx = -1
        for i, phase in enumerate(self.phases):
            if phase.value == self.status:
                current_idx = i
                break

        if self.status == "idle" and self.phases:
            self.status = self.phases[0].value
            return self.phases[0]

        next_idx = current_idx + 1
        if next_idx < len(self.phases):
            self.status = self.phases[next_idx].value
            return self.phases[next_idx]

        self.status = "completed"
        return None


@dataclass(frozen=True, slots=True)
class QualityRule:
    """A data quality rule that checks a single field."""

    name: str
    field: str
    check_type: str  # not_null, range, regex, unique
    threshold: float = 0.0
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ReplaySession:
    """A replay session that steps through an event sequence."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    events: list[dict[str, Any]] = field(default_factory=list)
    position: int = 0
    mode: ReplayMode = ReplayMode.SEQUENTIAL

    @property
    def current_event(self) -> dict[str, Any] | None:
        """Return the event at the current position, or None if exhausted."""
        if 0 <= self.position < len(self.events):
            return self.events[self.position]
        return None

    @property
    def is_complete(self) -> bool:
        return self.position >= len(self.events)

    @property
    def remaining(self) -> int:
        return max(0, len(self.events) - self.position)
