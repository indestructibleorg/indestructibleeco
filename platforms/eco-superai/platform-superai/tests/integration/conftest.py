"""Integration test conftest — shared fixtures for tests requiring infrastructure."""
from __future__ import annotations

import os
import pytest

os.environ["APP_ENV"] = "testing"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///test_integration.db"
os.environ["DATABASE_URL_SYNC"] = "sqlite:///test_integration.db"


@pytest.fixture
def client():
    """FastAPI TestClient for integration tests."""
    from fastapi.testclient import TestClient
    from src.presentation.api.main import app
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Admin JWT token headers."""
    from src.infrastructure.security import JWTHandler
    import uuid
    handler = JWTHandler()
    token = handler.create_access_token(
        subject="integration_admin",
        role="admin",
        extra={"user_id": str(uuid.uuid4())},
    )
    return {"Authorization": f"Bearer {token}"}