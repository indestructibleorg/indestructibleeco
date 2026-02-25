"""Violation entity — core domain object for governance violations."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ViolationSeverity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ViolationStatus(Enum):
    DETECTED = "DETECTED"
    ANALYZING = "ANALYZING"
    REMEDIATED = "REMEDIATED"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    ACCEPTED_RISK = "ACCEPTED_RISK"
    DEFERRED = "DEFERRED"


class DetectionMethod(Enum):
    STATIC = "STATIC"
    RUNTIME = "RUNTIME"
    SEMANTIC = "SEMANTIC"


@dataclass
class Violation:
    """Immutable violation record with cryptographic binding."""

    violation_type: str
    severity: ViolationSeverity
    description: str
    affected_system: str
    detection_method: DetectionMethod
    confidence_score: float

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: ViolationStatus = ViolationStatus.DETECTED
    affected_code: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)

    @property
    def evidence_hash(self) -> str:
        """Compute SHA-256 hash of violation evidence."""
        data = f"{self.id}:{self.violation_type}:{self.severity.value}:{self.description}"
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    @property
    def is_blocking(self) -> bool:
        """Whether this violation blocks execution."""
        return self.severity in (ViolationSeverity.CRITICAL, ViolationSeverity.HIGH)
