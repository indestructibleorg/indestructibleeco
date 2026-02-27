"""Targeted tests for remaining uncovered lines in infrastructure modules.

Covers:
- external/__init__.py lines 36, 55, 74, 95: HTTPClientBase retry exhaustion returns {}
- external/__init__.py lines 67-69: put HTTPStatusError
- database.py lines 28-29, 33-34: create_engine and get_session
- worker.py line 285: worker exception handler
- settings.py lines 182-183: Settings validation
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# HTTPClientBase – retry exhaustion returns {} (lines 36, 55, 74, 95)
# ---------------------------------------------------------------------------

class TestHTTPClientBaseRetryExhaustion:
    """Cover lines 36, 55, 74, 95: retry loop exhausted returns empty dict."""

    @pytest.mark.asyncio
    async def test_get_returns_empty_dict_when_max_retries_zero(self):
        """Line 36 – GET returns {} when max_retries=0 (loop never executes)."""
        from src.infrastructure.external import HTTPClientBase

        # max_retries=0 means the for loop never runs, falling through to return {}
        client = HTTPClientBase(base_url="http://test.example.com", max_retries=0)
        result = await client.get("/test")
        assert result == {}

    @pytest.mark.asyncio
    async def test_post_returns_empty_dict_when_max_retries_zero(self):
        """Line 55 – POST returns {} when max_retries=0 (loop never executes)."""
        from src.infrastructure.external import HTTPClientBase

        client = HTTPClientBase(base_url="http://test.example.com", max_retries=0)
        result = await client.post("/test", json={"key": "value"})
        assert result == {}

    @pytest.mark.asyncio
    async def test_put_http_status_error_logged(self):
        """Lines 67-69 – PUT HTTPStatusError is logged and re-raised on last attempt."""
        import httpx
        from src.infrastructure.external import HTTPClientBase

        client = HTTPClientBase(base_url="http://test.example.com", max_retries=1)

        mock_response = MagicMock()
        mock_response.status_code = 400  # 4xx - not retried
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Bad Request", request=MagicMock(), response=mock_response
        )

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_async_client = AsyncMock()
            mock_async_client.__aenter__ = AsyncMock(return_value=mock_async_client)
            mock_async_client.__aexit__ = AsyncMock(return_value=False)
            mock_async_client.put = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_async_client

            with pytest.raises(httpx.HTTPStatusError):
                await client.put("/test", json={"key": "value"})

    @pytest.mark.asyncio
    async def test_put_returns_empty_dict_when_max_retries_zero(self):
        """Line 74 – PUT returns {} when max_retries=0 (loop never executes)."""
        from src.infrastructure.external import HTTPClientBase

        client = HTTPClientBase(base_url="http://test.example.com", max_retries=0)
        result = await client.put("/test", json={"key": "value"})
        assert result == {}

    @pytest.mark.asyncio
    async def test_delete_returns_empty_dict_when_max_retries_zero(self):
        """Line 95 – DELETE returns {} when max_retries=0 (loop never executes)."""
        from src.infrastructure.external import HTTPClientBase

        client = HTTPClientBase(base_url="http://test.example.com", max_retries=0)
        result = await client.delete("/test")
        assert result == {}


# ---------------------------------------------------------------------------
# database.py – create_engine and get_session (lines 28-29, 33-34)
# ---------------------------------------------------------------------------

class TestDatabaseModule:
    """Cover lines 28-29, 33-34: database engine creation and session."""

    def test_engine_is_created(self):
        """Lines 28-29 – engine is created with the DATABASE_URL."""
        from src.infrastructure.persistence.database import engine
        assert engine is not None

    @pytest.mark.asyncio
    async def test_get_session_yields_session(self):
        """Lines 33-34 – get_session yields an AsyncSession."""
        from sqlalchemy.ext.asyncio import AsyncSession
        from src.infrastructure.persistence.database import get_session

        # Use the test SQLite database
        sessions = []
        async for session in get_session():
            sessions.append(session)
            break  # Only need one session

        assert len(sessions) == 1
        assert isinstance(sessions[0], AsyncSession)


# ---------------------------------------------------------------------------
# worker.py – main() function (line 285)
# ---------------------------------------------------------------------------

class TestWorkerMain:
    """Cover line 285: worker main() calls celery_app.worker_main."""

    def test_main_calls_celery_worker_main(self):
        """Line 285 – main() calls celery_app.worker_main with correct argv."""
        from src.infrastructure.tasks import worker as worker_module

        with patch.object(worker_module.celery_app, "worker_main") as mock_worker_main:
            worker_module.main()

        mock_worker_main.assert_called_once()
        call_args = mock_worker_main.call_args[1] or {}
        argv = mock_worker_main.call_args[0][0] if mock_worker_main.call_args[0] else mock_worker_main.call_args[1].get("argv", [])
        assert "worker" in argv


# ---------------------------------------------------------------------------
# settings.py – validation (lines 182-183)
# ---------------------------------------------------------------------------

class TestSettingsValidation:
    """Cover lines 182-183: Settings production validation."""

    def test_settings_loaded_correctly(self):
        """Lines 182-183 – Settings model is loaded with correct values."""
        from src.infrastructure.config.settings import Settings

        settings = Settings()
        assert settings is not None
        assert hasattr(settings, "app_env")
        assert hasattr(settings, "jwt")

    def test_settings_production_jwt_secret_validation(self):
        """Lines 182-183 – Production settings raise ValueError for default JWT secret."""
        from src.infrastructure.config.settings import Settings, Environment
        import pytest

        with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
            Settings(
                app_env=Environment.PRODUCTION,
                secret_key="secure-production-secret-key-that-is-long-enough-to-pass",
                app_debug=False,
                # jwt.secret_key defaults to change-me... which should fail
            )
