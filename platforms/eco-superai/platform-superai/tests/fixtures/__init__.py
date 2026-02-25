"""Test fixtures and factory helpers."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any


class UserFactory:
    """Factory for creating test User entities."""

    @staticmethod
    def build(**overrides: Any) -> dict[str, Any]:
        defaults = {
            "id": str(uuid.uuid4()),
            "username": f"user_{uuid.uuid4().hex[:6]}",
            "email": f"user_{uuid.uuid4().hex[:6]}@test.com",
            "hashed_password": "$2b$12$fakehashfortest",
            "full_name": "Test User",
            "role": "developer",
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        defaults.update(overrides)
        return defaults

    @staticmethod
    def build_many(count: int, **overrides: Any) -> list[dict[str, Any]]:
        return [UserFactory.build(**overrides) for _ in range(count)]


class QuantumJobFactory:
    """Factory for creating test quantum job data."""

    @staticmethod
    def build(**overrides: Any) -> dict[str, Any]:
        defaults = {
            "job_id": f"qj-{uuid.uuid4().hex[:8]}",
            "algorithm": "vqe",
            "backend": "aer_simulator",
            "status": "completed",
            "num_qubits": 4,
            "shots": 1024,
            "result": {"optimal_value": -1.857, "iterations": 47},
            "execution_time_ms": 123.45,
        }
        defaults.update(overrides)
        return defaults


__all__ = ["UserFactory", "QuantumJobFactory"]