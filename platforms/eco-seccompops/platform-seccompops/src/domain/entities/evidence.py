"""Evidence entity — immutable evidence record with chain-of-custody."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class Evidence:
    """Immutable evidence record conforming to governance registry spec."""

    violation_type: str
    violation_description: str
    affected_system: str
    detection_method: str
    confidence_score: float
    collected_by: str

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    detection_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    affected_code: str = ""
    additional_context: dict[str, Any] = field(default_factory=dict)

    @property
    def evidence_hash(self) -> str:
        """Compute SHA-256 hash of evidence for chain binding."""
        data = (
            f"{self.id}:{self.violation_type}:{self.violation_description}"
            f":{self.affected_system}:{self.confidence_score}"
        )
        return hashlib.sha256(data.encode("utf-8")).hexdigest()
