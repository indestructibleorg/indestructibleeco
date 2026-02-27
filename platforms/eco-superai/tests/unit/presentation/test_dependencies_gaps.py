"""Targeted tests for remaining uncovered lines in presentation/api/dependencies/__init__.py.

Covers:
- get_db_session rollback path (lines 40-48)
- get_current_user generic exception handler (lines 106-107)
- get_user_repository (lines 212-214)
- get_quantum_job_repository (lines 223-225)
- get_client_ip fallback (line 240)
- require_admin (line 245)
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# get_db_session – rollback path (lines 40-48)
# ---------------------------------------------------------------------------

class TestGetDbSessionRollback:
    """Cover lines 40-48: get_db_session rolls back on exception."""

    @pytest.mark.asyncio
    async def test_get_db_session_rollback_on_exception(self):
        """Lines 46-48 – session.rollback() is called when exception occurs."""
        from src.presentation.api.dependencies import get_db_session

        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()

        async def mock_get_session():
            yield mock_session

        with patch(
            "src.infrastructure.persistence.database.get_session",
            return_value=mock_get_session(),
        ):
            gen = get_db_session()
            session = await gen.__anext__()
            assert session is mock_session

            # Simulate an exception during the request
            with pytest.raises(ValueError):
                await gen.athrow(ValueError("test error"))

            mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_db_session_commits_on_success(self):
        """Lines 44-45 – session.commit() is called on success."""
        from src.presentation.api.dependencies import get_db_session

        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()

        async def mock_get_session():
            yield mock_session

        with patch(
            "src.infrastructure.persistence.database.get_session",
            return_value=mock_get_session(),
        ):
            gen = get_db_session()
            session = await gen.__anext__()
            assert session is mock_session

            # Normal completion
            try:
                await gen.__anext__()
            except StopAsyncIteration:
                pass

            mock_session.commit.assert_called_once()


# ---------------------------------------------------------------------------
# get_current_user – generic exception handler (lines 106-107)
# ---------------------------------------------------------------------------

class TestGetCurrentUserGenericException:
    """Cover lines 106-107: generic exception raises 401 AUTHENTICATION_ERROR."""

    @pytest.mark.asyncio
    async def test_generic_exception_raises_401(self):
        """Lines 106-107 – unexpected exception results in 401 AUTHENTICATION_ERROR."""
        from fastapi import HTTPException
        from fastapi.security import HTTPAuthorizationCredentials
        from src.presentation.api.dependencies import get_current_user

        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="some.jwt.token")

        with patch(
            "src.infrastructure.security.JWTHandler.decode_token",
            side_effect=RuntimeError("unexpected error"),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials=creds)

            assert exc_info.value.status_code == 401
            assert exc_info.value.detail["code"] == "AUTHENTICATION_ERROR"


# ---------------------------------------------------------------------------
# get_user_repository (lines 212-214)
# ---------------------------------------------------------------------------

class TestGetUserRepository:
    """Cover lines 212-214: get_user_repository returns SQLAlchemyUserRepository."""

    @pytest.mark.asyncio
    async def test_get_user_repository_returns_correct_type(self):
        """Lines 212-214 – returns SQLAlchemyUserRepository bound to session."""
        from src.presentation.api.dependencies import get_user_repository
        from src.infrastructure.persistence.repositories import SQLAlchemyUserRepository

        mock_session = AsyncMock()
        repo = await get_user_repository(session=mock_session)
        assert isinstance(repo, SQLAlchemyUserRepository)


# ---------------------------------------------------------------------------
# get_quantum_job_repository (lines 223-225)
# ---------------------------------------------------------------------------

class TestGetQuantumJobRepository:
    """Cover lines 223-225: get_quantum_job_repository returns SQLAlchemyQuantumJobRepository."""

    @pytest.mark.asyncio
    async def test_get_quantum_job_repository_returns_correct_type(self):
        """Lines 223-225 – returns SQLAlchemyQuantumJobRepository bound to session."""
        from src.presentation.api.dependencies import get_quantum_job_repository
        from src.infrastructure.persistence.repositories import SQLAlchemyQuantumJobRepository

        mock_session = AsyncMock()
        repo = await get_quantum_job_repository(session=mock_session)
        assert isinstance(repo, SQLAlchemyQuantumJobRepository)


# ---------------------------------------------------------------------------
# get_client_ip – fallback to unknown (line 240)
# ---------------------------------------------------------------------------

class TestGetClientIpFallback:
    """Cover line 240: get_client_ip returns 'unknown' when client is None."""

    def test_get_client_ip_no_client_returns_unknown(self):
        """Line 240 – returns 'unknown' when request.client is None."""
        from src.presentation.api.dependencies import get_client_ip

        request = MagicMock()
        request.headers.get = lambda h, d=None: d  # no forwarded headers
        request.client = None

        ip = get_client_ip(request)
        assert ip == "unknown"

    def test_get_client_ip_from_x_forwarded_for(self):
        """Lines 234-236 – X-Forwarded-For header is used."""
        from src.presentation.api.dependencies import get_client_ip

        request = MagicMock()
        request.headers.get = lambda h, d=None: "1.2.3.4, 5.6.7.8" if h == "X-Forwarded-For" else d

        ip = get_client_ip(request)
        assert ip == "1.2.3.4"


# ---------------------------------------------------------------------------
# require_admin (line 245)
# ---------------------------------------------------------------------------

class TestRequireAdmin:
    """Cover line 245: require_admin returns a callable."""

    def test_require_admin_returns_callable(self):
        """Line 245 – require_admin() returns a callable dependency."""
        from src.presentation.api.dependencies import require_admin

        dep = require_admin()
        assert callable(dep)
