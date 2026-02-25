"""Metric entity for ObservOps platform."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional


@dataclass(frozen=True)
class MetricPoint:
    """A single metric data point."""
    name: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    platform_id: str = "eco-observops"

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "value": self.value,
            "labels": self.labels,
            "timestamp": self.timestamp.isoformat(),
            "platform_id": self.platform_id,
        }


@dataclass(frozen=True)
class Alert:
    """An alert triggered by metric threshold breach."""
    alert_id: str
    name: str
    severity: str  # critical, warning, info
    message: str
    source_metric: str
    threshold: float
    current_value: float
    labels: Dict[str, str] = field(default_factory=dict)
    fired_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None
    platform_id: str = "eco-observops"

    @property
    def is_resolved(self) -> bool:
        return self.resolved_at is not None

    def to_dict(self) -> Dict:
        return {
            "alert_id": self.alert_id,
            "name": self.name,
            "severity": self.severity,
            "message": self.message,
            "source_metric": self.source_metric,
            "threshold": self.threshold,
            "current_value": self.current_value,
            "labels": self.labels,
            "fired_at": self.fired_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "platform_id": self.platform_id,
        }


@dataclass(frozen=True)
class TraceSpan:
    """A single span in a distributed trace."""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation_name: str
    service_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "ok"
    attributes: Dict[str, str] = field(default_factory=dict)
    platform_id: str = "eco-observops"

    @property
    def duration_ms(self) -> Optional[float]:
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return None

    def to_dict(self) -> Dict:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "operation_name": self.operation_name,
            "service_name": self.service_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "attributes": self.attributes,
            "platform_id": self.platform_id,
        }


@dataclass(frozen=True)
class HealthStatus:
    """Health status of a monitored service."""
    service_name: str
    namespace: str
    status: str  # healthy, degraded, unhealthy
    latency_ms: float
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    details: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "service_name": self.service_name,
            "namespace": self.namespace,
            "status": self.status,
            "latency_ms": self.latency_ms,
            "checked_at": self.checked_at.isoformat(),
            "details": self.details,
        }
