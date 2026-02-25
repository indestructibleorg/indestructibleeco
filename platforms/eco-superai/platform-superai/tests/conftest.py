"""Root conftest — shared fixtures for all test suites."""
from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncGenerator

import pytest

# Ensure the platform root is on sys.path so ``from src.…`` imports work.
_platform_root = str(Path(__file__).resolve().parent.parent)
if _platform_root not in sys.path:
    sys.path.insert(0, _platform_root)

# Force testing environment
os.environ["APP_ENV"] = "testing"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///test.db"
os.environ["DATABASE_URL_SYNC"] = "sqlite:///test.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"


@pytest.fixture
def user_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def sample_user_data() -> dict[str, Any]:
    return {
        "username": f"testuser_{uuid.uuid4().hex[:6]}",
        "email": f"test_{uuid.uuid4().hex[:6]}@example.com",
        "password": "SecureP@ss123",
        "full_name": "Test User",
        "role": "developer",
    }


@pytest.fixture
def sample_admin_data() -> dict[str, Any]:
    return {
        "username": f"admin_{uuid.uuid4().hex[:6]}",
        "email": f"admin_{uuid.uuid4().hex[:6]}@example.com",
        "password": "AdminP@ss456",
        "full_name": "Admin User",
        "role": "admin",
    }


@pytest.fixture
def sample_quantum_params() -> dict[str, Any]:
    return {
        "num_qubits": 2,
        "circuit_type": "bell",
        "shots": 100,
        "parameters": {},
    }


@pytest.fixture
def sample_matrix() -> list[list[float]]:
    return [[4.0, -2.0], [1.0, 1.0]]


@pytest.fixture
def sample_dataset() -> dict[str, Any]:
    return {
        "features": [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0], [7.0, 8.0], [9.0, 10.0]],
        "labels": [0.0, 0.0, 1.0, 1.0, 1.0],
    }


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Generate a test JWT token for authenticated requests."""
    from src.infrastructure.security import JWTHandler
    handler = JWTHandler()
    token = handler.create_access_token(subject="testuser", role="admin", extra={"user_id": str(uuid.uuid4())})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def now() -> datetime:
    return datetime.now(timezone.utc)