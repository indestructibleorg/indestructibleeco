"""Unit tests for SQLAlchemy repository — mapper logic and query construction."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domain.entities.user import Email, HashedPassword, User, UserRole, UserStatus
from src.domain.value_objects.email import Email as EmailVO
from src.domain.value_objects.password import HashedPassword as PasswordVO


# ---------------------------------------------------------------------------
# Entity ↔ Model Mapper Tests (pure logic, no DB)
# ---------------------------------------------------------------------------

class TestUserEntityConstruction:
    """Verify User aggregate construction and value object integration."""

    def test_create_user_via_factory(self) -> None:
        user = User.create(
            username="testuser",
            email="test@example.com",
            hashed_password="$2b$12$" + "a" * 53,
            full_name="Test User",
            role=UserRole.DEVELOPER,
        )
        assert user.username == "testuser"
        assert user.email.value == "test@example.com"
        assert user.role == UserRole.DEVELOPER
        assert user.status == UserStatus.PENDING_VERIFICATION
        assert len(user.id) == 36  # UUID

    def test_create_user_raises_event(self) -> None:
        user = User.create(
            username="eventuser",
            email="event@example.com",
            hashed_password="$2b$12$" + "b" * 53,
        )
        events = user.collect_events()
        assert len(events) == 1
        assert events[0].event_type == "user.created"
        assert events[0].payload["username"] == "eventuser"

    def test_activate_user(self) -> None:
        user = User.create(
            username="inactive",
            email="inactive@example.com",
            hashed_password="$2b$12$" + "c" * 53,
        )
        assert user.status == UserStatus.PENDING_VERIFICATION
        user.activate()
        assert user.status == UserStatus.ACTIVE
        assert user.version == 1

    def test_suspend_user(self) -> None:
        user = User.create(
            username="suspendme",
            email="suspend@example.com",
            hashed_password="$2b$12$" + "d" * 53,
        )
        user.activate()
        user.suspend(reason="policy violation")
        assert user.status == UserStatus.SUSPENDED
        events = user.collect_events()
        suspend_events = [e for e in events if e.event_type == "user.suspended"]
        assert len(suspend_events) == 1
        assert suspend_events[0].payload["reason"] == "policy violation"

    def test_change_role(self) -> None:
        user = User.create(
            username="rolechange",
            email="role@example.com",
            hashed_password="$2b$12$" + "e" * 53,
            role=UserRole.VIEWER,
        )
        user.change_role(UserRole.SCIENTIST)
        assert user.role == UserRole.SCIENTIST

    def test_change_password(self) -> None:
        user = User.create(
            username="pwdchange",
            email="pwd@example.com",
            hashed_password="$2b$12$" + "f" * 53,
        )
        new_hash = "$2b$12$" + "g" * 53
        user.change_password(new_hash)
        assert user.hashed_password.value == new_hash
        assert user.failed_login_attempts == 0

    def test_login_failure_lockout(self) -> None:
        user = User.create(
            username="lockout",
            email="lockout@example.com",
            hashed_password="$2b$12$" + "h" * 53,
        )
        for _ in range(5):
            user.record_login_failure(max_attempts=5)
        assert user.is_locked is True
        assert user.locked_until is not None

    def test_login_success_resets_failures(self) -> None:
        user = User.create(
            username="resetfail",
            email="reset@example.com",
            hashed_password="$2b$12$" + "i" * 53,
        )
        user.record_login_failure()
        user.record_login_failure()
        assert user.failed_login_attempts == 2
        user.record_login_success()
        assert user.failed_login_attempts == 0
        assert user.last_login_at is not None

    def test_admin_has_all_permissions(self) -> None:
        user = User.create(
            username="admin",
            email="admin@example.com",
            hashed_password="$2b$12$" + "j" * 53,
            role=UserRole.ADMIN,
        )
        assert user.has_permission("anything") is True

    def test_grant_and_revoke_permission(self) -> None:
        user = User.create(
            username="perms",
            email="perms@example.com",
            hashed_password="$2b$12$" + "k" * 53,
            role=UserRole.DEVELOPER,
        )
        user.grant_permission("deploy:production")
        assert user.has_permission("deploy:production") is True
        user.revoke_permission("deploy:production")
        assert user.has_permission("deploy:production") is False

    def test_invalid_username_rejected(self) -> None:
        with pytest.raises(ValueError):
            User.create(
                username="invalid user!",
                email="bad@example.com",
                hashed_password="$2b$12$" + "l" * 53,
            )

    def test_invalid_email_rejected(self) -> None:
        with pytest.raises(ValueError):
            User.create(
                username="validuser",
                email="not-an-email",
                hashed_password="$2b$12$" + "m" * 53,
            )


# ---------------------------------------------------------------------------
# QuantumJob Entity Tests
# ---------------------------------------------------------------------------

class TestQuantumJobEntity:
    """Verify QuantumJob aggregate lifecycle."""

    def test_submit_creates_job(self) -> None:
        from src.domain.entities.quantum_job import JobStatus, QuantumJob
        job = QuantumJob.submit(
            user_id="user-1",
            algorithm="bell",
            num_qubits=2,
            shots=1024,
        )
        assert job.status == JobStatus.SUBMITTED
        assert job.algorithm.value == "bell"
        assert job.user_id == "user-1"

    def test_job_lifecycle_submit_start_complete(self) -> None:
        from src.domain.entities.quantum_job import JobStatus, QuantumJob
        job = QuantumJob.submit(user_id="u1", algorithm="ghz", num_qubits=3)
        job.collect_events()  # clear submit event

        job.start()
        assert job.status == JobStatus.RUNNING
        assert job.started_at is not None

        job.complete(result={"counts": {"000": 512, "111": 512}}, execution_time_ms=42.5)
        assert job.status == JobStatus.COMPLETED
        assert job.result["counts"]["000"] == 512
        assert job.execution_time_ms == 42.5
        assert job.is_terminal is True

    def test_job_failure(self) -> None:
        from src.domain.entities.quantum_job import JobStatus, QuantumJob
        job = QuantumJob.submit(user_id="u2", algorithm="vqe", num_qubits=4)
        job.start()
        job.fail("Qiskit not installed")
        assert job.status == JobStatus.FAILED
        assert job.error_message == "Qiskit not installed"

    def test_job_cancel(self) -> None:
        from src.domain.entities.quantum_job import JobStatus, QuantumJob
        job = QuantumJob.submit(user_id="u3", algorithm="qaoa")
        job.cancel(reason="user request")
        assert job.status == JobStatus.CANCELLED

    def test_cannot_start_completed_job(self) -> None:
        from src.domain.entities.quantum_job import QuantumJob
        job = QuantumJob.submit(user_id="u4", algorithm="bell")
        job.start()
        job.complete(result={}, execution_time_ms=1.0)
        with pytest.raises(ValueError, match="Cannot start"):
            job.start()

    def test_cannot_cancel_completed_job(self) -> None:
        from src.domain.entities.quantum_job import QuantumJob
        job = QuantumJob.submit(user_id="u5", algorithm="bell")
        job.start()
        job.complete(result={}, execution_time_ms=1.0)
        with pytest.raises(ValueError, match="Cannot cancel"):
            job.cancel()


# ---------------------------------------------------------------------------
# AIExpert Entity Tests
# ---------------------------------------------------------------------------

class TestAIExpertEntity:
    """Verify AIExpert aggregate lifecycle."""

    def test_create_expert(self) -> None:
        from src.domain.entities.ai_expert import AIExpert, ExpertStatus
        expert = AIExpert.create(
            name="QuantumBot",
            domain="quantum",
            owner_id="owner-1",
            model="gpt-4-turbo-preview",
        )
        assert expert.name == "QuantumBot"
        assert expert.status == ExpertStatus.ACTIVE
        assert expert.query_count == 0

    def test_record_query_increments(self) -> None:
        from src.domain.entities.ai_expert import AIExpert
        expert = AIExpert.create(name="Bot", domain="ml", owner_id="o1")
        expert.record_query(tokens_used=150)
        expert.record_query(tokens_used=200)
        assert expert.query_count == 2
        assert expert.total_tokens_used == 350
        assert expert.last_queried_at is not None

    def test_deactivate_and_activate(self) -> None:
        from src.domain.entities.ai_expert import AIExpert, ExpertStatus
        expert = AIExpert.create(name="Bot", domain="devops", owner_id="o2")
        expert.deactivate(reason="maintenance")
        assert expert.status == ExpertStatus.INACTIVE
        expert.activate()
        assert expert.status == ExpertStatus.ACTIVE

    def test_update_knowledge_base(self) -> None:
        from src.domain.entities.ai_expert import AIExpert
        expert = AIExpert.create(name="Bot", domain="security", owner_id="o3")
        assert expert.has_knowledge_base is False
        expert.update_knowledge_base(["kb-1", "kb-2"])
        assert expert.has_knowledge_base is True
        assert len(expert.knowledge_base_ids) == 2

    def test_effective_system_prompt_default(self) -> None:
        from src.domain.entities.ai_expert import AIExpert
        expert = AIExpert.create(name="Bot", domain="quantum", owner_id="o4")
        assert "quantum computing" in expert.effective_system_prompt.lower()

    def test_effective_system_prompt_custom(self) -> None:
        from src.domain.entities.ai_expert import AIExpert
        expert = AIExpert.create(
            name="Bot", domain="general", owner_id="o5",
            system_prompt="You are a custom bot.",
        )
        assert expert.effective_system_prompt == "You are a custom bot."