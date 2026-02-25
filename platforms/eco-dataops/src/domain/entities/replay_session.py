"""ReplaySession entity — state reconstruction session with timeline binding."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class ReplayMode(Enum):
    FULL = "FULL"
    PARTIAL = "PARTIAL"
    POINT_IN_TIME = "POINT_IN_TIME"
    DIFFERENTIAL = "DIFFERENTIAL"


class ReplayStatus(Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class ReplaySession:
    """Replay session tracking state reconstruction lifecycle."""

    mode: ReplayMode
    start_sequence: int
    end_sequence: Optional[int] = None

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: ReplayStatus = ReplayStatus.ACTIVE
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    events_replayed: int = 0
    reconstructed_state: dict[str, Any] = field(default_factory=dict)

    @property
    def session_hash(self) -> str:
        """Compute session integrity hash."""
        data = f"{self.id}:{self.mode.value}:{self.start_sequence}:{self.end_sequence}"
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    @property
    def is_complete(self) -> bool:
        return self.status == ReplayStatus.COMPLETED
