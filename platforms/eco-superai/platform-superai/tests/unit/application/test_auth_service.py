"""Unit tests for application auth service."""
from __future__ import annotations

import pytest

from src.application.services import AuthService
from src.domain.exceptions import TokenExpiredException, InvalidTokenException


class TestAuthService:
    def setup_method(self):
        self.auth = AuthService()

    def test_hash_and_verify_password(self):
        hashed = self.auth.hash_password("SecureP@ss1")
        assert hashed != "SecureP@ss1"
        assert self.auth.verify_password("SecureP@ss1", hashed)
        assert not self.auth.verify_password("wrong", hashed)

    def test_create_tokens(self):
        tokens = self.auth.create_tokens(user_id="u-123", username="testuser", role="admin")
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"
        assert tokens["expires_in"] > 0

    def test_verify_access_token(self):
        tokens = self.auth.create_tokens(user_id="u-123", username="testuser", role="developer")
        payload = self.auth.verify_access_token(tokens["access_token"])
        assert payload["sub"] == "testuser"
        assert payload["role"] == "developer"
        assert payload["user_id"] == "u-123"
        assert payload["type"] == "access"

    def test_invalid_token_raises(self):
        with pytest.raises(InvalidTokenException):
            self.auth.verify_access_token("invalid.token.here")

    def test_refresh_token_not_valid_as_access(self):
        tokens = self.auth.create_tokens(user_id="u-123", username="testuser", role="admin")
        with pytest.raises(InvalidTokenException):
            self.auth.verify_access_token(tokens["refresh_token"])