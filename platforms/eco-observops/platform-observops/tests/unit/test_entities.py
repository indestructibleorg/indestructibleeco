"""Tests for ObservOps domain entities."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from datetime import datetime, timezone
from domain.entities.metric import MetricPoint, Alert, TraceSpan, HealthStatus


def test_metric_point_creation():
    m = MetricPoint(name="cpu_usage", value=0.85, labels={"host": "node-1"})
    assert m.name == "cpu_usage"
    assert m.value == 0.85
    assert m.platform_id == "eco-observops"


def test_metric_point_to_dict():
    m = MetricPoint(name="mem", value=1024.0)
    d = m.to_dict()
    assert d["name"] == "mem"
    assert d["value"] == 1024.0
    assert "timestamp" in d


def test_alert_creation():
    a = Alert(
        alert_id="a1",
        name="HighCPU",
        severity="critical",
        message="CPU > 90%",
        source_metric="cpu_usage",
        threshold=0.9,
        current_value=0.95,
    )
    assert a.severity == "critical"
    assert not a.is_resolved
    assert a.platform_id == "eco-observops"


def test_alert_to_dict():
    a = Alert(
        alert_id="a2", name="Test", severity="info",
        message="test", source_metric="test", threshold=1.0, current_value=0.5,
    )
    d = a.to_dict()
    assert d["alert_id"] == "a2"
    assert d["resolved_at"] is None


def test_trace_span_duration():
    start = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    end = datetime(2025, 1, 1, 0, 0, 0, 500000, tzinfo=timezone.utc)
    s = TraceSpan(
        trace_id="t1", span_id="s1", parent_span_id=None,
        operation_name="GET /api", service_name="web",
        start_time=start, end_time=end,
    )
    assert s.duration_ms == 500.0
    assert s.platform_id == "eco-observops"


def test_trace_span_no_end():
    s = TraceSpan(
        trace_id="t2", span_id="s2", parent_span_id="s1",
        operation_name="DB query", service_name="db",
        start_time=datetime.now(timezone.utc),
    )
    assert s.duration_ms is None


def test_health_status():
    h = HealthStatus(
        service_name="platform-core",
        namespace="eco-core",
        status="healthy",
        latency_ms=12.5,
    )
    d = h.to_dict()
    assert d["service_name"] == "platform-core"
    assert d["status"] == "healthy"
