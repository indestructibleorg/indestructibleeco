"""Test anomaly event domain entity."""

from domain.entities.anomaly_event import (
    AnomalyAlgorithm,
    AnomalyEvent,
    AnomalySeverity,
)


def test_anomaly_event_creation():
    e = AnomalyEvent(
        metric_name="cpu_usage",
        metric_value=95.5,
        algorithm=AnomalyAlgorithm.Z_SCORE,
        severity=AnomalySeverity.CRITICAL,
        score=3.2,
        threshold=2.5,
        description="CPU usage spike detected",
    )
    assert e.metric_name == "cpu_usage"
    assert e.metric_value == 95.5
    assert e.algorithm == AnomalyAlgorithm.Z_SCORE
    assert e.severity == AnomalySeverity.CRITICAL
    assert e.score == 3.2
    assert e.threshold == 2.5


def test_anomaly_is_actionable():
    critical = AnomalyEvent(
        metric_name="m",
        metric_value=1.0,
        algorithm=AnomalyAlgorithm.IQR,
        severity=AnomalySeverity.CRITICAL,
        score=5.0,
        threshold=2.0,
        description="test",
    )
    assert critical.is_actionable is True

    high = AnomalyEvent(
        metric_name="m",
        metric_value=1.0,
        algorithm=AnomalyAlgorithm.IQR,
        severity=AnomalySeverity.HIGH,
        score=3.0,
        threshold=2.0,
        description="test",
    )
    assert high.is_actionable is True

    medium = AnomalyEvent(
        metric_name="m",
        metric_value=1.0,
        algorithm=AnomalyAlgorithm.IQR,
        severity=AnomalySeverity.MEDIUM,
        score=2.0,
        threshold=2.0,
        description="test",
    )
    assert medium.is_actionable is False


def test_anomaly_exceeds_threshold():
    e = AnomalyEvent(
        metric_name="m",
        metric_value=1.0,
        algorithm=AnomalyAlgorithm.ISOLATION_FOREST,
        severity=AnomalySeverity.HIGH,
        score=3.5,
        threshold=2.5,
        description="test",
    )
    assert e.exceeds_threshold is True

    e2 = AnomalyEvent(
        metric_name="m",
        metric_value=1.0,
        algorithm=AnomalyAlgorithm.MOVING_AVERAGE,
        severity=AnomalySeverity.LOW,
        score=1.0,
        threshold=2.5,
        description="test",
    )
    assert e2.exceeds_threshold is False


def test_anomaly_exceeds_threshold_negative_score():
    e = AnomalyEvent(
        metric_name="m",
        metric_value=1.0,
        algorithm=AnomalyAlgorithm.Z_SCORE,
        severity=AnomalySeverity.HIGH,
        score=-3.0,
        threshold=2.5,
        description="Negative deviation",
    )
    assert e.exceeds_threshold is True


def test_anomaly_severity_enum_values():
    assert AnomalySeverity.CRITICAL.value == "CRITICAL"
    assert AnomalySeverity.HIGH.value == "HIGH"
    assert AnomalySeverity.MEDIUM.value == "MEDIUM"
    assert AnomalySeverity.LOW.value == "LOW"
    assert AnomalySeverity.INFO.value == "INFO"


def test_anomaly_algorithm_enum_values():
    assert AnomalyAlgorithm.Z_SCORE.value == "Z_SCORE"
    assert AnomalyAlgorithm.IQR.value == "IQR"
    assert AnomalyAlgorithm.ISOLATION_FOREST.value == "ISOLATION_FOREST"
    assert AnomalyAlgorithm.MOVING_AVERAGE.value == "MOVING_AVERAGE"
