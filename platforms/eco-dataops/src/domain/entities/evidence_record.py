"""EvidenceRecord entity — immutable evidence record with chain-of-custody binding."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class EvidenceState(Enum):
    INGESTED = "INGESTED"
    VALIDATING = "VALIDATING"
    VERIFIED = "VERIFIED"
    SEALED = "SEALED"
    ARCHIVED = "ARCHIVED"
    REJECTED = "REJECTED"


@dataclass
class EvidenceRecord:
    """Immutable evidence record with hash-chain binding."""

    source: str
    payload: dict[str, Any]

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state: EvidenceState = EvidenceState.INGESTED
    hash_value: str = ""
    chain_parent_hash: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    sealed_at: Optional[datetime] = None

    @property
    def evidence_hash(self) -> str:
        """Compute SHA3-512 hash of record content."""
        import json

        data = f"{self.id}:{json.dumps(self.payload, sort_keys=True, default=str)}"
        return hashlib.sha3_512(data.encode("utf-8")).hexdigest()

    @property
    def is_sealed(self) -> bool:
        return self.state == EvidenceState.SEALED

    @property
    def is_terminal(self) -> bool:
        return self.state in (EvidenceState.SEALED, EvidenceState.ARCHIVED, EvidenceState.REJECTED)
