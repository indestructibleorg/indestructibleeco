"""Anomaly API — Anomaly detection and alerting endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel

from engines.anomaly_detector.engine import AnomalyDetectorEngine

router = APIRouter()

_detector = AnomalyDetectorEngine()


class IngestMetricRequest(BaseModel):
    """Request to ingest a metric data point."""

    metric_name: str
    value: float
    labels: dict[str, str] = {}


@router.post("/ingest")
async def ingest_metric(request: IngestMetricRequest):
    """Ingest a metric data point and check for anomalies."""
    anomaly = _detector.ingest(
        metric_name=request.metric_name,
        value=request.value,
        labels=request.labels,
    )
    if anomaly:
        return {
            "anomaly_detected": True,
            "event_id": anomaly.event_id,
            "severity": anomaly.severity.value,
            "algorithm": anomaly.algorithm.value,
            "score": anomaly.score,
            "description": anomaly.description,
        }
    return {"anomaly_detected": False}


@router.get("/report")
async def anomaly_report():
    """Get anomaly detection report."""
    return _detector.get_anomaly_report()


@router.get("/metrics/{metric_name}")
async def metric_summary(metric_name: str):
    """Get summary statistics for a specific metric."""
    return _detector.get_metric_summary(metric_name)
