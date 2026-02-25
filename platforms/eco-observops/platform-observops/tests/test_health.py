"""Tests for ObservOps Platform health and API endpoints."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from fastapi.testclient import TestClient
from presentation.api.main import app

client = TestClient(app)


def test_healthz():
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "observops-platform"
    assert data["namespace"] == "eco-observops"


def test_livez():
    response = client.get("/livez")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"


def test_readyz():
    response = client.get("/readyz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "components" in data


def test_metrics_ingest():
    response = client.post("/api/v1/metrics/ingest", json={"name": "cpu_usage", "value": 0.75})
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"


def test_metrics_list():
    response = client.get("/api/v1/metrics/")
    assert response.status_code == 200
    assert "metrics" in response.json()


def test_metrics_query():
    client.post("/api/v1/metrics/ingest", json={"name": "test_metric", "value": 1.0})
    response = client.get("/api/v1/metrics/query?name=test_metric")
    assert response.status_code == 200
    assert response.json()["count"] >= 1


def test_alerts_create():
    alert = {"alert_id": "a1", "name": "HighCPU", "severity": "critical", "message": "CPU > 90%"}
    response = client.post("/api/v1/alerts/", json=alert)
    assert response.status_code == 200
    assert response.json()["status"] == "created"


def test_alerts_list():
    response = client.get("/api/v1/alerts/")
    assert response.status_code == 200
    assert "alerts" in response.json()


def test_alerts_active():
    response = client.get("/api/v1/alerts/active")
    assert response.status_code == 200


def test_alerts_resolve():
    client.post("/api/v1/alerts/", json={"alert_id": "a2", "name": "Test", "severity": "info"})
    response = client.post("/api/v1/alerts/a2/resolve")
    assert response.status_code == 200


def test_traces_ingest_span():
    span = {"trace_id": "t1", "span_id": "s1", "operation_name": "GET /api", "service_name": "web"}
    response = client.post("/api/v1/traces/spans", json=span)
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"


def test_traces_list():
    response = client.get("/api/v1/traces/")
    assert response.status_code == 200
    assert "trace_ids" in response.json()


def test_traces_get():
    client.post("/api/v1/traces/spans", json={"trace_id": "t2", "span_id": "s2", "operation_name": "DB", "service_name": "db"})
    response = client.get("/api/v1/traces/t2")
    assert response.status_code == 200
    assert response.json()["span_count"] >= 1


def test_traces_timeline():
    response = client.get("/api/v1/traces/t2/timeline")
    assert response.status_code == 200
    assert "timeline" in response.json()


def test_openapi_schema():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "ObservOps Platform"
