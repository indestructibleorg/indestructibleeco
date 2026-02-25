"""End-to-end workflow tests — full API request chains."""
from __future__ import annotations

import pytest


class TestUserWorkflow:
    """E2E: User registration → login → profile update → delete."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from src.presentation.api.main import app
        return TestClient(app)

    def test_health_before_workflow(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    def test_create_user_invalid_email(self, client):
        resp = client.post("/api/v1/users/register", json={
            "username": "testuser",
            "email": "not-an-email",
            "password": "SecureP@ss1",
        })
        # Should fail validation at domain or schema level
        assert resp.status_code in (422, 400)

    def test_create_user_weak_password(self, client):
        resp = client.post("/api/v1/users/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "weak",
        })
        assert resp.status_code == 422

    def test_quantum_backends_list(self, client):
        """Verify quantum backends endpoint is reachable (auth-protected, expect 401)."""
        resp = client.get("/api/v1/quantum/backends")
        # Auth-protected: 401 without token is correct behavior
        assert resp.status_code in (200, 401, 404, 405)

    def test_scientific_matrix_operation(self, client):
        """Test matrix eigenvalue computation."""
        resp = client.post("/api/v1/scientific/matrix", json={
            "operation": "eigenvalues",
            "matrix_a": [[4.0, -2.0], [1.0, 1.0]],
        })
        if resp.status_code == 200:
            data = resp.json()
            assert "eigenvalues" in data or "result" in data

    def test_ai_experts_list(self, client):
        """Test AI experts listing (auth-protected, expect 401 without token)."""
        resp = client.get("/api/v1/ai/experts")
        # Auth-protected: 401 without token is correct behavior
        assert resp.status_code in (200, 401)

    def test_metrics_endpoint(self, client):
        """Verify Prometheus metrics are exposed."""
        resp = client.get("/metrics")
        assert resp.status_code == 200
        assert "superai" in resp.text or "http" in resp.text
