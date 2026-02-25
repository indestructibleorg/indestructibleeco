"""AnomalyEvent entity — detected statistical anomaly record."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class AnomalySeverity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class AnomalyAlgorithm(Enum):
    Z_SCORE = "Z_SCORE"
    IQR = "IQR"
    ISOLATION_FOREST = "ISOLATION_FOREST"
    MOVING_AVERAGE = "MOVING_AVERAGE"


@dataclass
class AnomalyEvent:
    """Detected anomaly with scoring and classification."""

    metric_name: str
    metric_value: float
    algorithm: AnomalyAlgorithm
    severity: AnomalySeverity
    score: float
    threshold: float
    description: str

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_actionable(self) -> bool:
        return self.severity in (AnomalySeverity.CRITICAL, AnomalySeverity.HIGH)

    @property
    def exceeds_threshold(self) -> bool:
        return abs(self.score) > self.threshold
