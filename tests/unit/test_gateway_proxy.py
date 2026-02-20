"""Unit tests for root gateway proxy routing (Step 23)."""
import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.app import create_app


@pytest.fixture(scope="module")
def app():
    return create_app()


@pytest.fixture(scope="module")
def client(app):
    with TestClient(app) as c:
        yield c


def _get_auth_header(app):
    from src.schemas.auth import APIKeyCreate, UserRole
    result = app.state.auth.create_api_key(APIKeyCreate(
        name="test-gateway-key",
        role=UserRole.ADMIN,
        rate_limit_per_minute=1000,
    ))
    return {"Authorization": f"Bearer {result.key}"}


class TestGatewayHealth:
    def test_health_no_auth(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "uptime_seconds" in data

    def test_health_has_engines(self, client):
        resp = client.get("/health")
        data = resp.json()
        assert "engines" in data
        assert isinstance(data["engines"], list)


class TestGatewayMetrics:
    def test_metrics_has_queue_depth(self, client):
        resp = client.get("/metrics")
        assert resp.status_code == 200
        assert "eco_queue_depth" in resp.text


class TestGatewayModels:
    def test_models_requires_auth(self, client):
        resp = client.get("/v1/models")
        assert resp.status_code == 401

    def test_models_with_auth(self, client, app):
        headers = _get_auth_header(app)
        resp = client.get("/v1/models", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data


class TestGatewayChatCompletions:
    def test_chat_requires_auth(self, client):
        resp = client.post("/v1/chat/completions", json={
            "messages": [{"role": "user", "content": "hi"}]
        })
        assert resp.status_code == 401

    def test_chat_fallback_works(self, client, app):
        headers = _get_auth_header(app)
        resp = client.post("/v1/chat/completions", json={
            "messages": [{"role": "user", "content": "hello"}],
            "model": "llama-3.1-8b",
        }, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "choices" in data
        assert len(data["choices"]) >= 1


class TestGatewayProxyRoutes:
    def test_generate_requires_auth(self, client):
        resp = client.post("/api/v1/generate", json={"prompt": "test"})
        assert resp.status_code == 401

    def test_yaml_generate_requires_auth(self, client):
        resp = client.post("/api/v1/yaml/generate", json={"name": "test"})
        assert resp.status_code == 401

    def test_yaml_validate_requires_auth(self, client):
        resp = client.post("/api/v1/yaml/validate", json={"content": "test"})
        assert resp.status_code == 401

    def test_platforms_requires_auth(self, client):
        resp = client.get("/api/v1/platforms")
        assert resp.status_code == 401

    def test_proxy_returns_502_when_upstream_down(self, client, app):
        headers = _get_auth_header(app)
        resp = client.post("/api/v1/generate", json={"prompt": "test"}, headers=headers)
        # Upstream not running, should get 502
        assert resp.status_code == 502
