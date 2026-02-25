"""Tests for Platform Core health endpoints."""
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
    assert data["service"] == "platform-core"
    assert data["namespace"] == "eco-core"


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


def test_docs_available():
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_schema():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "Platform Core — Shared Kernel"
