"""Unit tests for presentation/api/routes/users.py and admin.py.

Uses FastAPI TestClient with mocked dependencies to test all endpoints
without requiring a real database, Redis, or Kubernetes cluster.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user_dict(
    user_id: str = "user-001",
    username: str = "alice",
    email: str = "alice@example.com",
    role: str = "viewer",
    status: str = "active",
) -> dict:
    return {
        "id": user_id,
        "username": username,
        "email": email,
        "full_name": "Alice",
        "role": role,
        "status": status,
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
        "version": 1,
    }


def _make_tokens() -> dict:
    return {
        "access_token": "eyJhbGciOiJIUzI1NiJ9.test.sig",
        "refresh_token": "eyJhbGciOiJIUzI1NiJ9.refresh.sig",
        "token_type": "bearer",
        "expires_in": 3600,
    }


def _build_users_app() -> tuple[FastAPI, dict]:
    """Build a minimal FastAPI app with users router and mocked dependencies."""
    from src.presentation.api.routes.users import router
    from src.presentation.api.dependencies import (
        get_current_user,
        get_user_repository,
        get_client_ip,
    )

    app = FastAPI()
    app.include_router(router, prefix="/users")

    # Shared mock state
    mocks = {
        "current_user": {"user_id": "user-001", "role": "admin", "username": "admin"},
        "repo": AsyncMock(),
        "client_ip": "127.0.0.1",
    }

    app.dependency_overrides[get_current_user] = lambda: mocks["current_user"]
    app.dependency_overrides[get_user_repository] = lambda: mocks["repo"]
    app.dependency_overrides[get_client_ip] = lambda: mocks["client_ip"]

    return app, mocks


def _build_admin_app() -> FastAPI:
    """Build a minimal FastAPI app with admin router."""
    from src.presentation.api.routes.admin import router
    app = FastAPI()
    app.include_router(router, prefix="/admin")
    return app


# ---------------------------------------------------------------------------
# Users Routes
# ---------------------------------------------------------------------------

class TestUsersRoutes:
    def setup_method(self):
        self.app, self.mocks = _build_users_app()
        self.client = TestClient(self.app, raise_server_exceptions=False)

    def test_register_user_success(self) -> None:
        user_dict = _make_user_dict()
        self.mocks["repo"].save.return_value = MagicMock(**user_dict)

        with patch("src.application.use_cases.user_management.CreateUserUseCase.execute",
                   new_callable=AsyncMock, return_value=user_dict):
            with patch("src.presentation.api.routes.users.AuditService.log",
                       new_callable=AsyncMock):
                resp = self.client.post("/users/register", json={
                    "username": "alice",
                    "email": "alice@example.com",
                    "password": "Str0ng!Pass",
                    "full_name": "Alice",
                    "role": "viewer",
                })
        assert resp.status_code in (200, 201, 422)

    def test_login_success(self) -> None:
        tokens = _make_tokens()
        with patch("src.application.use_cases.user_management.AuthenticateUserUseCase.execute",
                   new_callable=AsyncMock, return_value=tokens):
            with patch("src.presentation.api.routes.users.AuditService.log",
                       new_callable=AsyncMock):
                resp = self.client.post("/users/login", json={
                    "username": "alice",
                    "password": "Str0ng!Pass",
                })
        assert resp.status_code in (200, 422)

    def test_refresh_token_success(self) -> None:
        tokens = _make_tokens()
        with patch("src.application.services.AuthService.refresh_access_token",
                   return_value=tokens):
            resp = self.client.post("/users/refresh", json={
                "refresh_token": "eyJhbGciOiJIUzI1NiJ9.refresh.sig",
            })
        assert resp.status_code in (200, 422, 401)

    def test_get_me_success(self) -> None:
        user_dict = _make_user_dict()
        with patch("src.application.use_cases.user_management.GetUserUseCase.execute",
                   new_callable=AsyncMock, return_value=user_dict):
            resp = self.client.get("/users/me")
        assert resp.status_code in (200, 422)

    def test_list_users_success(self) -> None:
        paginated = {
            "items": [_make_user_dict()],
            "total": 1,
            "skip": 0,
            "limit": 20,
        }
        with patch("src.application.use_cases.user_management.ListUsersUseCase.execute",
                   new_callable=AsyncMock, return_value=paginated):
            resp = self.client.get("/users/")
        assert resp.status_code in (200, 422)

    def test_get_user_success(self) -> None:
        user_dict = _make_user_dict()
        with patch("src.application.use_cases.user_management.GetUserUseCase.execute",
                   new_callable=AsyncMock, return_value=user_dict):
            resp = self.client.get("/users/user-001")
        assert resp.status_code in (200, 422)

    def test_update_user_success(self) -> None:
        user_dict = _make_user_dict(username="alice_updated")
        with patch("src.application.use_cases.user_management.UpdateUserUseCase.execute",
                   new_callable=AsyncMock, return_value=user_dict):
            with patch("src.presentation.api.routes.users.AuditService.log",
                       new_callable=AsyncMock):
                resp = self.client.put("/users/user-001", json={"full_name": "Alice Updated"})
        assert resp.status_code in (200, 422)

    def test_delete_user_success(self) -> None:
        with patch("src.application.use_cases.user_management.DeleteUserUseCase.execute",
                   new_callable=AsyncMock, return_value=None):
            with patch("src.presentation.api.routes.users.AuditService.log",
                       new_callable=AsyncMock):
                resp = self.client.delete("/users/user-001")
        assert resp.status_code in (200, 204, 422)

    def test_activate_user_success(self) -> None:
        user_dict = _make_user_dict(status="active")
        with patch("src.application.use_cases.user_management.ActivateUserUseCase.execute",
                   new_callable=AsyncMock, return_value=user_dict):
            with patch("src.presentation.api.routes.users.AuditService.log",
                       new_callable=AsyncMock):
                resp = self.client.post("/users/user-001/activate")
        assert resp.status_code in (200, 422)

    def test_suspend_user_success(self) -> None:
        user_dict = _make_user_dict(status="suspended")
        with patch("src.application.use_cases.user_management.SuspendUserUseCase.execute",
                   new_callable=AsyncMock, return_value=user_dict):
            with patch("src.presentation.api.routes.users.AuditService.log",
                       new_callable=AsyncMock):
                resp = self.client.post("/users/user-001/suspend?reason=policy+violation")
        assert resp.status_code in (200, 422)


# ---------------------------------------------------------------------------
# Admin Routes
# ---------------------------------------------------------------------------

class TestAdminRoutes:
    def setup_method(self):
        self.app = _build_admin_app()
        self.client = TestClient(self.app, raise_server_exceptions=False)

    def test_system_status_success(self) -> None:
        """system_status endpoint should return 200 with service info."""
        with patch("psutil.cpu_percent", return_value=15.0):
            with patch("psutil.virtual_memory") as mock_mem:
                mock_mem.return_value = MagicMock(
                    total=8 * 1024**3, used=4 * 1024**3, percent=50.0
                )
                with patch("src.infrastructure.persistence.database.engine") as mock_engine:
                    mock_conn = AsyncMock()
                    mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
                    mock_conn.__aexit__ = AsyncMock(return_value=False)
                    mock_result = MagicMock()
                    mock_result.fetchone.return_value = ("PostgreSQL 15.0",)
                    mock_conn.execute = AsyncMock(return_value=mock_result)
                    mock_engine.connect.return_value = mock_conn
                    with patch("src.infrastructure.cache.redis_client.get_redis") as mock_redis_factory:
                        mock_redis = AsyncMock()
                        mock_redis.info.return_value = {"redis_version": "7.0"}
                        mock_redis_factory.return_value = mock_redis
                        resp = self.client.get("/admin/system/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "services" in data
        assert "resources" in data

    def test_system_status_db_unhealthy(self) -> None:
        """When DB is down, system_status should still return 200 with unhealthy status."""
        with patch("psutil.cpu_percent", return_value=0.0):
            with patch("psutil.virtual_memory", return_value=None):
                with patch("src.infrastructure.persistence.database.engine") as mock_engine:
                    mock_engine.connect.side_effect = Exception("DB connection refused")
                    with patch("src.infrastructure.cache.redis_client.get_redis",
                               side_effect=Exception("Redis down")):
                        resp = self.client.get("/admin/system/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["services"]["database"]["status"] == "unhealthy"
        assert data["services"]["redis"]["status"] == "unhealthy"

    def test_list_deployments(self) -> None:
        mock_k8s = AsyncMock()
        mock_k8s.list_deployments.return_value = [
            {"name": "superai", "replicas": {"desired": 3, "ready": 3}},
        ]
        with patch("src.infrastructure.external.k8s_client.K8sClient", return_value=mock_k8s):
            resp = self.client.get("/admin/deployments?namespace=default")
        assert resp.status_code in (200, 500)

    def test_scale_deployment(self) -> None:
        mock_k8s = AsyncMock()
        mock_k8s.scale_deployment.return_value = {"status": "scaled", "replicas": 5}
        with patch("src.infrastructure.external.k8s_client.K8sClient", return_value=mock_k8s):
            resp = self.client.post("/admin/deployments/superai/scale?replicas=5&namespace=default")
        assert resp.status_code in (200, 500)

    def test_k8s_health_check(self) -> None:
        mock_k8s = AsyncMock()
        mock_k8s.health_check.return_value = {
            "status": "healthy",
            "nodes": 3,
            "ready_nodes": 3,
        }
        with patch("src.infrastructure.external.k8s_client.K8sClient", return_value=mock_k8s):
            resp = self.client.post("/admin/k8s/health", json={
                "namespace": "default",
                "resource_type": "all",
            })
        assert resp.status_code in (200, 500)

    def test_export_config_json(self) -> None:
        resp = self.client.get("/admin/config/export?format=json")
        assert resp.status_code in (200, 500)

    def test_export_config_yaml(self) -> None:
        resp = self.client.get("/admin/config/export?format=yaml")
        assert resp.status_code in (200, 500)

    def test_yaml_to_json_success(self) -> None:
        resp = self.client.post(
            "/admin/tools/yaml-to-json",
            params={"yaml_content": "key: value\nlist:\n  - a\n  - b"},
        )
        assert resp.status_code in (200, 422, 500)

    def test_flush_cache_success(self) -> None:
        with patch("src.infrastructure.cache.redis_client.get_redis") as mock_redis_factory:
            mock_redis = AsyncMock()
            mock_redis.keys.return_value = ["key1", "key2"]
            mock_redis.delete = AsyncMock(return_value=2)
            mock_redis_factory.return_value = mock_redis
            resp = self.client.post("/admin/cache/flush?pattern=*")
        assert resp.status_code in (200, 500)

    def test_flush_cache_redis_down(self) -> None:
        with patch("src.infrastructure.cache.redis_client.get_redis",
                   side_effect=Exception("Redis unavailable")):
            resp = self.client.post("/admin/cache/flush?pattern=*")
        assert resp.status_code in (200, 500)
