"""Infrastructure security — JWT handling, password hashing, RBAC enforcement."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import structlog
from jose import JWTError, jwt

from src.domain.exceptions import (
    AuthenticationException,
    AuthorizationException,
    InvalidTokenException,
    TokenExpiredException,
)
from src.domain.value_objects.role import Permission, RolePermissions, UserRole

logger = structlog.get_logger(__name__)


# --- Password Hashing ---

class PasswordHasher:
    """Bcrypt password hashing service."""

    @staticmethod
    def hash(plain: str) -> str:
        pwd_bytes = plain.encode("utf-8")
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")

    @staticmethod
    def verify(plain: str, hashed: str) -> bool:
        try:
            return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
        except (ValueError, TypeError):
            return False


# --- JWT Token Handler ---

class JWTHandler:
    """JWT token creation and validation."""

    def __init__(self) -> None:
        from src.infrastructure.config import get_settings
        self._settings = get_settings().jwt

    def create_access_token(self, subject: str, role: str, extra: dict[str, Any] | None = None) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": subject,
            "role": role,
            "iss": self._settings.issuer,
            "aud": self._settings.audience,
            "iat": now,
            "exp": now + timedelta(minutes=self._settings.expiration_minutes),
            "type": "access",
        }
        if extra:
            payload.update(extra)
        return jwt.encode(payload, self._settings.secret_key, algorithm=self._settings.algorithm)

    def create_refresh_token(self, subject: str) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": subject,
            "iss": self._settings.issuer,
            "iat": now,
            "exp": now + timedelta(days=self._settings.refresh_expiration_days),
            "type": "refresh",
        }
        return jwt.encode(payload, self._settings.secret_key, algorithm=self._settings.algorithm)

    def decode_token(self, token: str) -> dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                self._settings.secret_key,
                algorithms=[self._settings.algorithm],
                audience=self._settings.audience,
                issuer=self._settings.issuer,
            )
            return payload
        except JWTError as e:
            error_str = str(e).lower()
            if "expired" in error_str:
                raise TokenExpiredException() from e
            raise InvalidTokenException() from e

    def verify_access_token(self, token: str) -> dict[str, Any]:
        payload = self.decode_token(token)
        if payload.get("type") != "access":
            raise InvalidTokenException()
        return payload

    def verify_refresh_token(self, token: str) -> dict[str, Any]:
        # Refresh tokens don't have audience claim
        try:
            payload = jwt.decode(
                token,
                self._settings.secret_key,
                algorithms=[self._settings.algorithm],
                issuer=self._settings.issuer,
                options={"verify_aud": False},
            )
        except JWTError as e:
            error_str = str(e).lower()
            if "expired" in error_str:
                raise TokenExpiredException() from e
            raise InvalidTokenException() from e

        if payload.get("type") != "refresh":
            raise InvalidTokenException()
        return payload


# --- RBAC Enforcer ---

class RBACEnforcer:
    """Role-Based Access Control enforcement."""

    @staticmethod
    def check_permission(role: str | UserRole, permission: Permission) -> None:
        user_role = UserRole(role) if isinstance(role, str) else role
        if not RolePermissions.has_permission(user_role, permission):
            logger.warning(
                "rbac_denied",
                role=user_role.value,
                permission=permission.value,
            )
            raise AuthorizationException(
                f"Role '{user_role.value}' lacks permission '{permission.value}'"
            )

    @staticmethod
    def check_any_permission(role: str | UserRole, permissions: set[Permission]) -> None:
        user_role = UserRole(role) if isinstance(role, str) else role
        if not RolePermissions.has_any_permission(user_role, permissions):
            perm_str = ", ".join(p.value for p in permissions)
            raise AuthorizationException(
                f"Role '{user_role.value}' lacks any of: {perm_str}"
            )

    @staticmethod
    def require_admin(role: str | UserRole) -> None:
        user_role = UserRole(role) if isinstance(role, str) else role
        if user_role != UserRole.ADMIN:
            raise AuthorizationException("Admin role required")


__all__ = ["PasswordHasher", "JWTHandler", "RBACEnforcer"]