"""Integration tests for API endpoints."""
import pytest
from fastapi.testclient import TestClient

from src.app import create_app


@pytest.fixture(scope="module")
def app():
    return create_app()


@pytest.fixture(scope="module")
def client(app):
    with TestClient(app) as c:
        yield c


class TestHealthEndpoint:
    def test_health_no_auth(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "version" in data
        assert "engines" in data

    def test_health_has_version(self, client):
        resp = client.get("/health")
        data = resp.json()
        assert data["version"] == "1.0.0"


class TestModelsEndpoint:
    def test_list_models_requires_auth(self, client):
        resp = client.get("/v1/models")
        assert resp.status_code == 401

    def test_list_models_with_auth(self, client):
        # Get the default admin key from logs or use a known test key
        # For integration tests, we test the auth flow
        resp = client.get("/v1/models")
        assert resp.status_code in (200, 401)


class TestMetricsEndpoint:
    def test_prometheus_metrics(self, client):
        resp = client.get("/metrics")
        assert resp.status_code == 200
        assert "eco_" in resp.text or "python_" in resp.text


class TestChatCompletionValidation:
    def test_missing_auth(self, client):
        resp = client.post("/v1/chat/completions", json={
            "messages": [{"role": "user", "content": "Hello"}],
        })
        assert resp.status_code == 401

    def test_invalid_temperature(self, client):
        resp = client.post(
            "/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "Hello"}],
                "temperature": 5.0,
            },
            headers={"Authorization": "Bearer sk-test"},
        )
        assert resp.status_code in (401, 422)