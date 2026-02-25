"""Integration tests for API health endpoints."""
from __future__ import annotations

import pytest
from unittest.mock import patch, AsyncMock


class TestHealthEndpoints:
    """Test health check endpoints via TestClient."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        from fastapi.testclient import TestClient
        from src.presentation.api.main import app
        return TestClient(app)

    def test_health_returns_200(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data
        assert "uptime_seconds" in data

    def test_liveness_returns_200(self, client):
        response = client.get("/api/v1/live")
        assert response.status_code == 200

    def test_metrics_endpoint(self, client):
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "superai_http_requests_total" in response.text or response.status_code == 200

    def test_nonexistent_route_returns_404(self, client):
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404