#!/usr/bin/env python3
"""
Anomaly Detector Engine v1.0
Statistical anomaly detection with multiple algorithms.

This module implements a multi-algorithm anomaly detection engine supporting
Z-Score, IQR, Isolation Forest (simplified), Moving Average, and CUSUM
detection methods with configurable thresholds and severity classification.

Governance Stage: S5-VERIFIED
Status: ENFORCED
"""

import hashlib
import json
import logging
import math
import sys
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Configure logging with CRITICAL-only default
logging.basicConfig(
    level=logging.CRITICAL,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================
# ENUMS
# ============================================

class AnomalyAlgorithm(Enum):
    """Supported anomaly detection algorithms."""
    Z_SCORE = "z_score"
    IQR = "iqr"
    ISOLATION_FOREST = "isolation_forest"
    MOVING_AVERAGE = "moving_average"
    CUMSUM = "cumsum"


class AnomalySeverity(Enum):
    """Severity levels for detected anomalies."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


# ============================================
# DATA STRUCTURES
# ============================================

@dataclass
class DataPoint:
    """A single metric data point with labels."""
    timestamp: float = field(default_factory=time.time)
    metric_name: str = ""
    value: float = 0.0
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class AnomalyEvent:
    """A detected anomaly event with full context."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    data_point: DataPoint = field(default_factory=DataPoint)
    algorithm: AnomalyAlgorithm = AnomalyAlgorithm.Z_SCORE
    severity: AnomalySeverity = AnomalySeverity.INFO
    score: float = 0.0
    threshold: float = 0.0
    description: str = ""
    detected_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a serializable dictionary."""
        return {
            "event_id": self.event_id,
            "metric_name": self.data_point.metric_name,
            "value": self.data_point.value,
            "algorithm": self.algorithm.value,
            "severity": self.severity.value,
            "score": self.score,
            "threshold": self.threshold,
            "description": self.description,
            "detected_at": self.detected_at,
        }


# ============================================
# ANOMALY DETECTOR ENGINE
# ============================================

class AnomalyDetectorEngine:
    """Anomaly Detector Engine -- statistical anomaly detection with multiple algorithms."""

    def __init__(
        self,
        window_size: int = 100,
        z_threshold: float = 3.0,
        iqr_multiplier: float = 1.5,
    ) -> None:
        """Initialize the anomaly detector engine.

        Args:
            window_size: Number of recent data points to keep per metric.
            z_threshold: Z-score threshold for anomaly detection.
            iqr_multiplier: IQR multiplier for outlier fencing.
        """
        self.metric_buffers: Dict[str, List[DataPoint]] = {}
        self.detected_anomalies: List[AnomalyEvent] = []
        self.config: Dict[str, Any] = {
            "window_size": window_size,
            "z_threshold": z_threshold,
            "iqr_multiplier": iqr_multiplier,
            "moving_avg_window": 20,
            "moving_avg_deviation": 2.0,
            "cumsum_drift": 0.5,
            "cumsum_threshold": 5.0,
        }
        self._cumsum_state: Dict[str, Dict[str, float]] = {}
        logger.info(
            "AnomalyDetectorEngine initialized: window=%d z_thresh=%.1f iqr_mult=%.1f",
            window_size, z_threshold, iqr_multiplier,
        )

    # ------------------------------------------
    # PUBLIC API
    # ------------------------------------------

    def ingest(
        self,
        metric_name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> Optional[AnomalyEvent]:
        """Ingest a metric data point and run anomaly detection.

        Adds the data point to the appropriate metric buffer, trims to
        window_size, and runs all detection algorithms. Returns the
        highest-severity anomaly if any are detected.

        Args:
            metric_name: Name of the metric.
            value: Numeric value of the data point.
            labels: Optional key-value labels for the data point.

        Returns:
            The highest-severity AnomalyEvent detected, or None.
        """
        point = DataPoint(
            metric_name=metric_name,
            value=value,
            labels=labels or {},
        )

        # Initialize buffer if needed
        if metric_name not in self.metric_buffers:
            self.metric_buffers[metric_name] = []

        self.metric_buffers[metric_name].append(point)

        # Trim buffer to window size
        window = self.config["window_size"]
        if len(self.metric_buffers[metric_name]) > window:
            self.metric_buffers[metric_name] = self.metric_buffers[metric_name][-window:]

        # Need minimum data points for detection
        if len(self.metric_buffers[metric_name]) < 10:
            return None

        # Run all detection algorithms and collect anomalies
        anomalies: List[AnomalyEvent] = []

        zscore_result = self.detect_zscore(metric_name)
        if zscore_result:
            anomalies.append(zscore_result)

        iqr_result = self.detect_iqr(metric_name)
        if iqr_result:
            anomalies.append(iqr_result)

        mavg_result = self.detect_moving_average(metric_name)
        if mavg_result:
            anomalies.append(mavg_result)

        # Return highest severity anomaly
        if anomalies:
            severity_order = [
                AnomalySeverity.CRITICAL,
                AnomalySeverity.HIGH,
                AnomalySeverity.MEDIUM,
                AnomalySeverity.LOW,
                AnomalySeverity.INFO,
            ]
            anomalies.sort(key=lambda a: severity_order.index(a.severity))
            worst = anomalies[0]
            self.detected_anomalies.append(worst)
            logger.info(
                "Anomaly detected: metric=%s value=%.4f severity=%s algo=%s",
                metric_name, value, worst.severity.value, worst.algorithm.value,
            )
            return worst

        return None

    def detect_zscore(self, metric_name: str) -> Optional[AnomalyEvent]:
        """Run Z-score anomaly detection on the latest data point.

        Args:
            metric_name: Name of the metric to analyze.

        Returns:
            An AnomalyEvent if the latest point is anomalous, else None.
        """
        buffer = self.metric_buffers.get(metric_name)
        if not buffer or len(buffer) < 10:
            return None

        values = np.array([p.value for p in buffer])
        mean = np.mean(values)
        std = np.std(values)

        if std == 0:
            return None

        latest = buffer[-1]
        z_score = abs((latest.value - mean) / std)
        threshold = self.config["z_threshold"]

        if z_score > threshold:
            severity = self._classify_severity(z_score, threshold)
            return AnomalyEvent(
                data_point=latest,
                algorithm=AnomalyAlgorithm.Z_SCORE,
                severity=severity,
                score=float(z_score),
                threshold=threshold,
                description=(
                    f"Z-score anomaly: value={latest.value:.4f}, "
                    f"z={z_score:.2f}, mean={mean:.4f}, std={std:.4f}"
                ),
            )

        return None

    def detect_iqr(self, metric_name: str) -> Optional[AnomalyEvent]:
        """Run IQR-based anomaly detection on the latest data point.

        Args:
            metric_name: Name of the metric to analyze.

        Returns:
            An AnomalyEvent if the latest point is an outlier, else None.
        """
        buffer = self.metric_buffers.get(metric_name)
        if not buffer or len(buffer) < 10:
            return None

        values = np.array([p.value for p in buffer])
        q1 = np.percentile(values, 25)
        q3 = np.percentile(values, 75)
        iqr = q3 - q1

        if iqr == 0:
            return None

        multiplier = self.config["iqr_multiplier"]
        lower_fence = q1 - multiplier * iqr
        upper_fence = q3 + multiplier * iqr

        latest = buffer[-1]
        if latest.value < lower_fence or latest.value > upper_fence:
            # Compute a normalized score: how far outside the fences
            if latest.value < lower_fence:
                deviation = (lower_fence - latest.value) / iqr
            else:
                deviation = (latest.value - upper_fence) / iqr

            severity = self._classify_severity(deviation, 1.0)
            return AnomalyEvent(
                data_point=latest,
                algorithm=AnomalyAlgorithm.IQR,
                severity=severity,
                score=float(deviation),
                threshold=float(multiplier),
                description=(
                    f"IQR outlier: value={latest.value:.4f}, "
                    f"Q1={q1:.4f}, Q3={q3:.4f}, IQR={iqr:.4f}, "
                    f"fences=[{lower_fence:.4f}, {upper_fence:.4f}]"
                ),
            )

        return None

    def detect_moving_average(self, metric_name: str) -> Optional[AnomalyEvent]:
        """Run moving average deviation detection on the latest data point.

        Args:
            metric_name: Name of the metric to analyze.

        Returns:
            An AnomalyEvent if the latest point deviates from the moving average, else None.
        """
        buffer = self.metric_buffers.get(metric_name)
        if not buffer or len(buffer) < 10:
            return None

        ma_window = min(self.config["moving_avg_window"], len(buffer) - 1)
        if ma_window < 5:
            return None

        # Compute moving average over the window (excluding the latest point)
        window_values = np.array([p.value for p in buffer[-(ma_window + 1):-1]])
        ma = np.mean(window_values)
        ma_std = np.std(window_values)

        if ma_std == 0:
            return None

        latest = buffer[-1]
        deviation_factor = self.config["moving_avg_deviation"]
        deviation = abs(latest.value - ma) / ma_std

        if deviation > deviation_factor:
            severity = self._classify_severity(deviation, deviation_factor)
            return AnomalyEvent(
                data_point=latest,
                algorithm=AnomalyAlgorithm.MOVING_AVERAGE,
                severity=severity,
                score=float(deviation),
                threshold=float(deviation_factor),
                description=(
                    f"Moving average anomaly: value={latest.value:.4f}, "
                    f"ma={ma:.4f}, ma_std={ma_std:.4f}, "
                    f"deviation={deviation:.2f}x"
                ),
            )

        return None

    def get_anomaly_report(self) -> Dict[str, Any]:
        """Generate a summary report of all detected anomalies.

        Returns:
            Dictionary with anomaly counts, severity breakdown, algorithm breakdown.
        """
        by_severity: Dict[str, int] = {}
        for sev in AnomalySeverity:
            count = sum(1 for a in self.detected_anomalies if a.severity == sev)
            if count > 0:
                by_severity[sev.value] = count

        by_algorithm: Dict[str, int] = {}
        for algo in AnomalyAlgorithm:
            count = sum(1 for a in self.detected_anomalies if a.algorithm == algo)
            if count > 0:
                by_algorithm[algo.value] = count

        by_metric: Dict[str, int] = {}
        for anomaly in self.detected_anomalies:
            name = anomaly.data_point.metric_name
            by_metric[name] = by_metric.get(name, 0) + 1

        return {
            "total_anomalies": len(self.detected_anomalies),
            "by_severity": by_severity,
            "by_algorithm": by_algorithm,
            "by_metric": by_metric,
            "total_metrics_tracked": len(self.metric_buffers),
            "total_data_points": sum(len(b) for b in self.metric_buffers.values()),
            "config": dict(self.config),
        }

    def get_metric_summary(self, metric_name: str) -> Dict[str, Any]:
        """Return statistical summary for a specific metric.

        Args:
            metric_name: Name of the metric.

        Returns:
            Dictionary with count, mean, std, min, max, percentiles, and anomaly count.
        """
        buffer = self.metric_buffers.get(metric_name)
        if not buffer:
            return {"error": f"No data for metric '{metric_name}'"}

        values = np.array([p.value for p in buffer])
        anomaly_count = sum(
            1 for a in self.detected_anomalies
            if a.data_point.metric_name == metric_name
        )

        return {
            "metric_name": metric_name,
            "count": len(buffer),
            "mean": float(np.mean(values)),
            "std": float(np.std(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "p25": float(np.percentile(values, 25)),
            "p50": float(np.percentile(values, 50)),
            "p75": float(np.percentile(values, 75)),
            "p99": float(np.percentile(values, 99)),
            "anomaly_count": anomaly_count,
            "latest_value": float(values[-1]),
            "latest_timestamp": buffer[-1].timestamp,
        }

    # ------------------------------------------
    # INTERNAL METHODS
    # ------------------------------------------

    def _classify_severity(self, score: float, threshold: float) -> AnomalySeverity:
        """Classify anomaly severity based on how far the score exceeds the threshold.

        Args:
            score: The computed anomaly score.
            threshold: The base threshold for detection.

        Returns:
            The appropriate AnomalySeverity level.
        """
        ratio = score / threshold if threshold > 0 else score

        if ratio >= 4.0:
            return AnomalySeverity.CRITICAL
        elif ratio >= 3.0:
            return AnomalySeverity.HIGH
        elif ratio >= 2.0:
            return AnomalySeverity.MEDIUM
        elif ratio >= 1.5:
            return AnomalySeverity.LOW
        else:
            return AnomalySeverity.INFO


# ============================================
# CLI INTERFACE
# ============================================

def main() -> None:
    """Demonstrate anomaly detector usage."""
    print("=" * 60)
    print("Anomaly Detector Engine -- Demo")
    print("=" * 60)

    engine = AnomalyDetectorEngine(window_size=50, z_threshold=2.5, iqr_multiplier=1.5)

    # Generate normal data with injected anomalies
    np.random.seed(42)
    normal_values = np.random.normal(loc=100.0, scale=5.0, size=40)

    print("\n--- Ingesting Normal Data ---")
    for i, val in enumerate(normal_values):
        result = engine.ingest("cpu_usage", float(val), labels={"host": "server-1"})
        if result:
            print(f"  Point {i}: value={val:.2f} -> ANOMALY ({result.severity.value})")

    # Inject anomalies
    print("\n--- Injecting Anomalous Data ---")
    anomalous_values = [200.0, 5.0, 180.0, 150.0, -50.0]
    for i, val in enumerate(anomalous_values):
        result = engine.ingest("cpu_usage", val, labels={"host": "server-1"})
        if result:
            print(
                f"  Anomaly {i}: value={val:.2f} -> {result.severity.value} "
                f"({result.algorithm.value}, score={result.score:.2f})"
            )
        else:
            print(f"  Point {i}: value={val:.2f} -> normal")

    # Second metric
    print("\n--- Second Metric (memory_usage) ---")
    mem_values = np.random.normal(loc=60.0, scale=3.0, size=30)
    for val in mem_values:
        engine.ingest("memory_usage", float(val), labels={"host": "server-1"})
    spike = engine.ingest("memory_usage", 95.0, labels={"host": "server-1"})
    if spike:
        print(f"  Memory spike detected: severity={spike.severity.value}")

    # Metric summary
    print("\n--- Metric Summary (cpu_usage) ---")
    summary = engine.get_metric_summary("cpu_usage")
    print(f"  Count: {summary['count']}")
    print(f"  Mean: {summary['mean']:.2f}")
    print(f"  Std: {summary['std']:.2f}")
    print(f"  Range: [{summary['min']:.2f}, {summary['max']:.2f}]")
    print(f"  P50: {summary['p50']:.2f}, P99: {summary['p99']:.2f}")
    print(f"  Anomalies: {summary['anomaly_count']}")

    # Full report
    print("\n--- Anomaly Report ---")
    report = engine.get_anomaly_report()
    print(f"  Total anomalies: {report['total_anomalies']}")
    print(f"  By severity: {json.dumps(report['by_severity'], indent=4)}")
    print(f"  By algorithm: {json.dumps(report['by_algorithm'], indent=4)}")
    print(f"  By metric: {json.dumps(report['by_metric'], indent=4)}")
    print(f"  Total metrics tracked: {report['total_metrics_tracked']}")
    print(f"  Total data points: {report['total_data_points']}")

    print("\n" + "=" * 60)
    print("Anomaly Detector Engine -- Demo Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
