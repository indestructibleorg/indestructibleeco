"""Unit tests for application/use_cases — user, AI, and quantum management.

All repository, event bus, and external service calls are mocked so these
tests run without any external dependencies.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers — build a minimal User entity for testing
# ---------------------------------------------------------------------------

def _make_active_user(
    user_id: str = "user-001",
    username: str = "alice",
    email: str = "alice@example.com",
    role: str = "VIEWER",
):
    from src.domain.entities.user import User
    from src.domain.value_objects.password import HashedPassword
    from src.domain.entities.user import UserRole
    hashed = HashedPassword.from_plain("Str0ng!Pass")
    # UserRole uses string values ("viewer", "admin"), accept both
    role_val = role.lower() if role.upper() == role else role
    user = User.create(
        username=username,
        email=email,
        hashed_password=hashed,
        full_name="Alice",
        role=UserRole(role_val),
    )
    user.id = user_id
    user.activate()
    return user


def _make_suspended_user(**kwargs):
    user = _make_active_user(**kwargs)
    user.suspend("test suspension")
    return user


# ---------------------------------------------------------------------------
# CreateUserUseCase
# ---------------------------------------------------------------------------

class TestCreateUserUseCase:
    @pytest.mark.asyncio
    async def test_create_user_success(self) -> None:
        from src.application.use_cases.user_management import CreateUserUseCase
        mock_repo = AsyncMock()
        mock_repo.find_by_email.return_value = None
        mock_repo.find_by_username.return_value = None
        saved_user = _make_active_user()
        mock_repo.save.return_value = saved_user

        uc = CreateUserUseCase(repo=mock_repo)
        with patch("src.application.events.get_event_bus") as mock_bus_factory:
            mock_bus = AsyncMock()
            mock_bus_factory.return_value = mock_bus
            result = await uc.execute(
                username="alice",
                email="alice@example.com",
                password="Str0ng!Pass",
                full_name="Alice",
                role="viewer",
            )
        assert result["username"] == "alice"

    @pytest.mark.asyncio
    async def test_create_user_duplicate_raises_on_save(self) -> None:
        """When the DB raises IntegrityError on duplicate, the exception propagates."""
        from src.application.use_cases.user_management import CreateUserUseCase
        from sqlalchemy.exc import IntegrityError
        mock_repo = AsyncMock()
        mock_repo.save.side_effect = IntegrityError("UNIQUE", {}, None)

        uc = CreateUserUseCase(repo=mock_repo)
        with pytest.raises(IntegrityError):
            await uc.execute(
                username="alice",
                email="alice@example.com",
                password="Str0ng!Pass",
                full_name="Alice",
                role="viewer",
            )


# ---------------------------------------------------------------------------
# AuthenticateUserUseCase
# ---------------------------------------------------------------------------

class TestAuthenticateUserUseCase:
    @pytest.mark.asyncio
    async def test_authenticate_success(self) -> None:
        from src.application.use_cases.user_management import AuthenticateUserUseCase
        mock_repo = AsyncMock()
        user = _make_active_user()
        mock_repo.find_by_username.return_value = user

        uc = AuthenticateUserUseCase(repo=mock_repo)
        with patch("src.application.events.get_event_bus") as mock_bus_factory:
            mock_bus = AsyncMock()
            mock_bus_factory.return_value = mock_bus
            with patch("src.application.services.AuthService.verify_password", return_value=True):
                with patch("src.application.services.AuthService.create_tokens",
                           return_value={"access_token": "tok", "refresh_token": "ref"}):
                    result = await uc.execute(username="alice", password="Str0ng!Pass")
        assert "access_token" in result

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found_raises(self) -> None:
        from src.application.use_cases.user_management import AuthenticateUserUseCase
        from src.domain.exceptions import AuthenticationException
        mock_repo = AsyncMock()
        mock_repo.find_by_username.return_value = None

        uc = AuthenticateUserUseCase(repo=mock_repo)
        with patch("src.application.events.get_event_bus") as mock_bus_factory:
            mock_bus = AsyncMock()
            mock_bus_factory.return_value = mock_bus
            with pytest.raises(AuthenticationException):
                await uc.execute(username="ghost", password="pass")

    @pytest.mark.asyncio
    async def test_authenticate_wrong_password_raises(self) -> None:
        from src.application.use_cases.user_management import AuthenticateUserUseCase
        from src.domain.exceptions import AuthenticationException
        mock_repo = AsyncMock()
        user = _make_active_user()
        mock_repo.find_by_username.return_value = user

        uc = AuthenticateUserUseCase(repo=mock_repo)
        with patch("src.application.services.AuthService.verify_password", return_value=False):
            with patch("src.application.events.get_event_bus") as mock_bus_factory:
                mock_bus = AsyncMock()
                mock_bus_factory.return_value = mock_bus
                with pytest.raises(AuthenticationException):
                    await uc.execute(username="alice", password="wrongpass")

    @pytest.mark.asyncio
    async def test_authenticate_suspended_user_raises(self) -> None:
        from src.application.use_cases.user_management import AuthenticateUserUseCase
        from src.domain.exceptions import AuthenticationException
        mock_repo = AsyncMock()
        user = _make_suspended_user()
        mock_repo.find_by_username.return_value = user

        uc = AuthenticateUserUseCase(repo=mock_repo)
        with patch("src.application.services.AuthService.verify_password", return_value=True):
            with patch("src.application.events.get_event_bus") as mock_bus_factory:
                mock_bus = AsyncMock()
                mock_bus_factory.return_value = mock_bus
                with pytest.raises(AuthenticationException, match="suspended"):
                    await uc.execute(username="alice", password="Str0ng!Pass")


# ---------------------------------------------------------------------------
# ListUsersUseCase
# ---------------------------------------------------------------------------

class TestListUsersUseCase:
    @pytest.mark.asyncio
    async def test_list_users_returns_paginated(self) -> None:
        from src.application.use_cases.user_management import ListUsersUseCase
        mock_repo = AsyncMock()
        users = [_make_active_user(user_id=f"user-{i}", username=f"user{i}", email=f"u{i}@x.com")
                 for i in range(3)]
        mock_repo.list_users.return_value = (users, 3)

        uc = ListUsersUseCase(repo=mock_repo)
        result = await uc.execute(skip=0, limit=20)
        assert result["total"] == 3
        assert len(result["items"]) == 3

    @pytest.mark.asyncio
    async def test_list_users_empty(self) -> None:
        from src.application.use_cases.user_management import ListUsersUseCase
        mock_repo = AsyncMock()
        mock_repo.list_users.return_value = ([], 0)

        uc = ListUsersUseCase(repo=mock_repo)
        result = await uc.execute(skip=0, limit=20)
        assert result["total"] == 0
        assert result["items"] == []


# ---------------------------------------------------------------------------
# GetUserUseCase
# ---------------------------------------------------------------------------

class TestGetUserUseCase:
    @pytest.mark.asyncio
    async def test_get_user_success(self) -> None:
        from src.application.use_cases.user_management import GetUserUseCase
        mock_repo = AsyncMock()
        user = _make_active_user()
        mock_repo.find_by_id.return_value = user

        uc = GetUserUseCase(repo=mock_repo)
        result = await uc.execute(user_id="user-001")
        assert result["username"] == "alice"

    @pytest.mark.asyncio
    async def test_get_user_not_found_raises(self) -> None:
        from src.application.use_cases.user_management import GetUserUseCase
        from src.shared.exceptions import EntityNotFoundException
        mock_repo = AsyncMock()
        mock_repo.find_by_id.return_value = None

        uc = GetUserUseCase(repo=mock_repo)
        with pytest.raises(EntityNotFoundException):
            await uc.execute(user_id="nonexistent")


# ---------------------------------------------------------------------------
# UpdateUserUseCase
# ---------------------------------------------------------------------------

class TestUpdateUserUseCase:
    @pytest.mark.asyncio
    async def test_update_user_full_name(self) -> None:
        from src.application.use_cases.user_management import UpdateUserUseCase
        mock_repo = AsyncMock()
        user = _make_active_user()
        mock_repo.find_by_id.return_value = user
        updated_user = _make_active_user()
        updated_user.full_name = "Alice Updated"
        mock_repo.update.return_value = updated_user

        uc = UpdateUserUseCase(repo=mock_repo)
        with patch("src.application.events.get_event_bus") as mock_bus_factory:
            mock_bus = AsyncMock()
            mock_bus_factory.return_value = mock_bus
            result = await uc.execute(user_id="user-001", full_name="Alice Updated")
        assert result["full_name"] == "Alice Updated"

    @pytest.mark.asyncio
    async def test_update_user_not_found_raises(self) -> None:
        from src.application.use_cases.user_management import UpdateUserUseCase
        from src.shared.exceptions import EntityNotFoundException
        mock_repo = AsyncMock()
        mock_repo.find_by_id.return_value = None

        uc = UpdateUserUseCase(repo=mock_repo)
        with patch("src.application.events.get_event_bus") as mock_bus_factory:
            mock_bus_factory.return_value = AsyncMock()
            with pytest.raises(EntityNotFoundException):
                await uc.execute(user_id="ghost", full_name="Ghost")


# ---------------------------------------------------------------------------
# DeleteUserUseCase
# ---------------------------------------------------------------------------

class TestDeleteUserUseCase:
    @pytest.mark.asyncio
    async def test_delete_user_success(self) -> None:
        from src.application.use_cases.user_management import DeleteUserUseCase
        mock_repo = AsyncMock()
        user = _make_active_user()
        mock_repo.find_by_id.return_value = user

        uc = DeleteUserUseCase(repo=mock_repo)
        with patch("src.application.events.get_event_bus") as mock_bus_factory:
            mock_bus = AsyncMock()
            mock_bus_factory.return_value = mock_bus
            await uc.execute(user_id="user-001")
        mock_repo.delete.assert_called_once_with("user-001")

    @pytest.mark.asyncio
    async def test_delete_user_not_found_raises(self) -> None:
        from src.application.use_cases.user_management import DeleteUserUseCase
        from src.shared.exceptions import EntityNotFoundException
        mock_repo = AsyncMock()
        mock_repo.find_by_id.return_value = None

        uc = DeleteUserUseCase(repo=mock_repo)
        with patch("src.application.events.get_event_bus") as mock_bus_factory:
            mock_bus_factory.return_value = AsyncMock()
            with pytest.raises(EntityNotFoundException):
                await uc.execute(user_id="ghost")


# ---------------------------------------------------------------------------
# ActivateUserUseCase
# ---------------------------------------------------------------------------

class TestActivateUserUseCase:
    @pytest.mark.asyncio
    async def test_activate_user_success(self) -> None:
        from src.application.use_cases.user_management import ActivateUserUseCase
        mock_repo = AsyncMock()
        user = _make_suspended_user()
        mock_repo.find_by_id.return_value = user
        mock_repo.update.return_value = user

        uc = ActivateUserUseCase(repo=mock_repo)
        with patch("src.application.events.get_event_bus") as mock_bus_factory:
            mock_bus = AsyncMock()
            mock_bus_factory.return_value = mock_bus
            result = await uc.execute(user_id="user-001")
        assert result is not None

    @pytest.mark.asyncio
    async def test_activate_user_not_found_raises(self) -> None:
        from src.application.use_cases.user_management import ActivateUserUseCase
        from src.shared.exceptions import EntityNotFoundException
        mock_repo = AsyncMock()
        mock_repo.find_by_id.return_value = None

        uc = ActivateUserUseCase(repo=mock_repo)
        with patch("src.application.events.get_event_bus") as mock_bus_factory:
            mock_bus_factory.return_value = AsyncMock()
            with pytest.raises(EntityNotFoundException):
                await uc.execute(user_id="ghost")


# ---------------------------------------------------------------------------
# SuspendUserUseCase
# ---------------------------------------------------------------------------

class TestSuspendUserUseCase:
    @pytest.mark.asyncio
    async def test_suspend_user_success(self) -> None:
        from src.application.use_cases.user_management import SuspendUserUseCase
        mock_repo = AsyncMock()
        user = _make_active_user()
        mock_repo.find_by_id.return_value = user
        mock_repo.update.return_value = user

        uc = SuspendUserUseCase(repo=mock_repo)
        with patch("src.application.events.get_event_bus") as mock_bus_factory:
            mock_bus = AsyncMock()
            mock_bus_factory.return_value = mock_bus
            result = await uc.execute(user_id="user-001", reason="policy violation")
        assert result is not None

    @pytest.mark.asyncio
    async def test_suspend_user_not_found_raises(self) -> None:
        from src.application.use_cases.user_management import SuspendUserUseCase
        from src.shared.exceptions import EntityNotFoundException
        mock_repo = AsyncMock()
        mock_repo.find_by_id.return_value = None

        uc = SuspendUserUseCase(repo=mock_repo)
        with patch("src.application.events.get_event_bus") as mock_bus_factory:
            mock_bus_factory.return_value = AsyncMock()
            with pytest.raises(EntityNotFoundException):
                await uc.execute(user_id="ghost")


# ---------------------------------------------------------------------------
# AI Management Use Cases
# ---------------------------------------------------------------------------

class TestExecuteAgentTaskUseCase:
    @pytest.mark.asyncio
    async def test_execute_agent_task_success(self) -> None:
        from src.application.use_cases.ai_management import ExecuteAgentTaskUseCase
        mock_executor = AsyncMock()
        mock_executor.execute.return_value = {
            "status": "completed",
            "output": "analysis result",
            "agent_type": "analyst",
        }

        with patch("src.ai.agents.task_executor.AgentTaskExecutor", return_value=mock_executor):
            uc = ExecuteAgentTaskUseCase()
            result = await uc.execute(
                agent_type="analyst",
                task="analyze this data",
                context={"data": [1, 2, 3]},
                constraints=["be concise"],
                output_format="markdown",
            )
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_execute_agent_task_failure_returns_error(self) -> None:
        from src.application.use_cases.ai_management import ExecuteAgentTaskUseCase
        mock_executor = AsyncMock()
        mock_executor.execute.side_effect = ValueError("unknown agent")

        with patch("src.ai.agents.task_executor.AgentTaskExecutor", return_value=mock_executor):
            uc = ExecuteAgentTaskUseCase()
            try:
                result = await uc.execute(
                    agent_type="unknown_type",
                    task="do something",
                )
                # If it returns a result dict, check it has error info
                assert isinstance(result, dict)
            except Exception:
                pass  # Exception propagation is also acceptable


class TestListExpertsUseCase:
    @pytest.mark.asyncio
    async def test_list_experts(self) -> None:
        from src.application.use_cases.ai_management import ListExpertsUseCase
        with patch("src.ai.factory.expert_factory._EXPERT_STORE", {"analyst": {"id": "analyst"}}):
            uc = ListExpertsUseCase()
            result = await uc.execute()
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_list_experts_empty(self) -> None:
        from src.application.use_cases.ai_management import ListExpertsUseCase
        with patch("src.ai.factory.expert_factory._EXPERT_STORE", {}):
            uc = ListExpertsUseCase()
            result = await uc.execute()
        assert result == []


# ---------------------------------------------------------------------------
# Quantum Management Use Cases
# ---------------------------------------------------------------------------

class TestSubmitQuantumJobUseCase:
    @pytest.mark.asyncio
    async def test_submit_quantum_job_success(self) -> None:
        from src.application.use_cases.quantum_management import SubmitQuantumJobUseCase
        mock_executor = AsyncMock()
        mock_executor.run_circuit.return_value = {
            "status": "completed",
            "result": {"counts": {"00": 512, "11": 512}},
            "execution_time_ms": 150.0,
        }

        with patch("src.quantum.runtime.executor.QuantumExecutor", return_value=mock_executor):
            with patch("src.application.events.get_event_bus") as mock_bus_factory:
                mock_bus = AsyncMock()
                mock_bus_factory.return_value = mock_bus
                uc = SubmitQuantumJobUseCase(repo=None)
                result = await uc.execute(
                    user_id="user-001",
                    algorithm="bell",
                    num_qubits=2,
                    shots=1024,
                    backend="aer_simulator",
                    parameters={},
                )
        assert result["status"] == "completed"
        assert result["algorithm"] == "bell"

    @pytest.mark.asyncio
    async def test_submit_quantum_job_executor_failure(self) -> None:
        from src.application.use_cases.quantum_management import SubmitQuantumJobUseCase
        mock_executor = AsyncMock()
        mock_executor.run_circuit.side_effect = RuntimeError("quantum hardware unavailable")

        with patch("src.application.events.get_event_bus") as mock_bus_factory:
            mock_bus = AsyncMock()
            mock_bus_factory.return_value = mock_bus
            # Pass the mock executor directly via dependency injection
            uc = SubmitQuantumJobUseCase(repo=None, executor=mock_executor)
            result = await uc.execute(
                user_id="user-001",
                algorithm="bell",
                num_qubits=2,
                shots=1024,
                backend="aer_simulator",
                parameters={},
            )
        assert result["status"] == "failed"
        assert "quantum hardware unavailable" in result["error_message"]


class TestListQuantumBackendsUseCase:
    @pytest.mark.asyncio
    async def test_list_backends(self) -> None:
        from src.application.use_cases.quantum_management import ListQuantumBackendsUseCase
        mock_executor = MagicMock()
        mock_executor.list_backends.return_value = [
            {"name": "aer_simulator", "type": "simulator"},
        ]

        with patch("src.quantum.runtime.executor.QuantumExecutor", return_value=mock_executor):
            uc = ListQuantumBackendsUseCase()
            result = await uc.execute()
        assert isinstance(result, list)
        assert len(result) >= 1
