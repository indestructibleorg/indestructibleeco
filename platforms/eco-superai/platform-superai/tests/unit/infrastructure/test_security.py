"""Unit tests for infrastructure security — PasswordHasher, JWTHandler, RBACEnforcer."""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.domain.exceptions import (
    AuthorizationException,
    InvalidTokenException,
    TokenExpiredException,
)
from src.domain.value_objects.role import Permission, UserRole
from src.infrastructure.security import JWTHandler, PasswordHasher, RBACEnforcer


# ---------------------------------------------------------------------------
# PasswordHasher
# ---------------------------------------------------------------------------

class TestPasswordHasher:
    """Tests for bcrypt password hashing."""

    def setup_method(self) -> None:
        self.hasher = PasswordHasher()

    def test_hash_returns_bcrypt_string(self) -> None:
        hashed = self.hasher.hash("StrongP@ss1")
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
        assert len(hashed) == 60

    def test_hash_produces_unique_salts(self) -> None:
        h1 = self.hasher.hash("same_password")
        h2 = self.hasher.hash("same_password")
        assert h1 != h2

    def test_verify_correct_password(self) -> None:
        plain = "MySecretP@ss99"
        hashed = self.hasher.hash(plain)
        assert self.hasher.verify(plain, hashed) is True

    def test_verify_wrong_password(self) -> None:
        hashed = self.hasher.hash("correct_password")
        assert self.hasher.verify("wrong_password", hashed) is False

    def test_verify_malformed_hash_returns_false(self) -> None:
        assert self.hasher.verify("anything", "not-a-hash") is False

    def test_verify_empty_password(self) -> None:
        hashed = self.hasher.hash("real_password")
        assert self.hasher.verify("", hashed) is False


# ---------------------------------------------------------------------------
# JWTHandler
# ---------------------------------------------------------------------------

class TestJWTHandler:
    """Tests for JWT token creation and verification."""

    def setup_method(self) -> None:
        self.handler = JWTHandler()

    def test_create_access_token_returns_string(self) -> None:
        token = self.handler.create_access_token(subject="testuser", role="admin")
        assert isinstance(token, str)
        assert len(token) > 50

    def test_create_refresh_token_returns_string(self) -> None:
        token = self.handler.create_refresh_token(subject="testuser")
        assert isinstance(token, str)
        assert len(token) > 50

    def test_verify_access_token_roundtrip(self) -> None:
        token = self.handler.create_access_token(
            subject="alice",
            role="scientist",
            extra={"user_id": "uid-123"},
        )
        payload = self.handler.verify_access_token(token)
        assert payload["sub"] == "alice"
        assert payload["role"] == "scientist"
        assert payload["user_id"] == "uid-123"
        assert payload["type"] == "access"

    def test_verify_refresh_token_roundtrip(self) -> None:
        token = self.handler.create_refresh_token(subject="bob")
        payload = self.handler.verify_refresh_token(token)
        assert payload["sub"] == "bob"
        assert payload["type"] == "refresh"

    def test_access_token_rejected_as_refresh(self) -> None:
        token = self.handler.create_access_token(subject="user", role="viewer")
        with pytest.raises(InvalidTokenException):
            self.handler.verify_refresh_token(token)

    def test_refresh_token_rejected_as_access(self) -> None:
        token = self.handler.create_refresh_token(subject="user")
        with pytest.raises(InvalidTokenException):
            self.handler.verify_access_token(token)

    def test_invalid_token_string_raises(self) -> None:
        with pytest.raises(InvalidTokenException):
            self.handler.verify_access_token("not.a.valid.jwt")

    def test_empty_token_raises(self) -> None:
        with pytest.raises(InvalidTokenException):
            self.handler.verify_access_token("")

    def test_tampered_token_raises(self) -> None:
        token = self.handler.create_access_token(subject="user", role="viewer")
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(InvalidTokenException):
            self.handler.verify_access_token(tampered)


# ---------------------------------------------------------------------------
# RBACEnforcer
# ---------------------------------------------------------------------------

class TestRBACEnforcer:
    """Tests for role-based access control enforcement."""

    def test_admin_has_all_permissions(self) -> None:
        # Admin should not raise for any permission
        for perm in Permission:
            RBACEnforcer.check_permission("admin", perm)

    def test_viewer_lacks_admin_permission(self) -> None:
        with pytest.raises(AuthorizationException):
            RBACEnforcer.check_permission("viewer", Permission.ADMIN_FULL)

    def test_viewer_lacks_write_permissions(self) -> None:
        with pytest.raises(AuthorizationException):
            RBACEnforcer.check_permission("viewer", Permission.USER_WRITE)

    def test_operator_has_quantum_execute(self) -> None:
        # Operator should be able to execute quantum jobs
        RBACEnforcer.check_permission("operator", Permission.QUANTUM_EXECUTE)

    def test_scientist_has_scientific_execute(self) -> None:
        RBACEnforcer.check_permission("scientist", Permission.SCIENTIFIC_EXECUTE)

    def test_check_any_permission_passes_if_one_matches(self) -> None:
        RBACEnforcer.check_any_permission(
            "viewer",
            {Permission.ADMIN_FULL, Permission.USER_READ},
        )

    def test_check_any_permission_fails_if_none_match(self) -> None:
        with pytest.raises(AuthorizationException):
            RBACEnforcer.check_any_permission(
                "viewer",
                {Permission.ADMIN_FULL, Permission.USER_WRITE},
            )

    def test_require_admin_passes_for_admin(self) -> None:
        RBACEnforcer.require_admin("admin")

    def test_require_admin_fails_for_non_admin(self) -> None:
        with pytest.raises(AuthorizationException):
            RBACEnforcer.require_admin("viewer")

    def test_invalid_role_raises_value_error(self) -> None:
        with pytest.raises(ValueError):
            RBACEnforcer.check_permission("nonexistent_role", Permission.USER_READ)