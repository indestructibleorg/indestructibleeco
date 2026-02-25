"""Application services — cross-cutting orchestration that doesn't belong in use cases."""
from __future__ import annotations

from typing import Any

import structlog

from src.domain.exceptions import AuthenticationException
from src.infrastructure.security import JWTHandler, PasswordHasher

logger = structlog.get_logger(__name__)


class AuthService:
    """Authentication service — coordinates JWT and password operations."""

    def __init__(self) -> None:
        self._jwt = JWTHandler()
        self._hasher = PasswordHasher()

    def hash_password(self, plain: str) -> str:
        return self._hasher.hash(plain)

    def verify_password(self, plain: str, hashed: str) -> bool:
        return self._hasher.verify(plain, hashed)

    def create_tokens(self, user_id: str, username: str, role: str) -> dict[str, Any]:
        from src.infrastructure.config import get_settings
        settings = get_settings()
        access = self._jwt.create_access_token(
            subject=username,
            role=role,
            extra={"user_id": user_id},
        )
        refresh = self._jwt.create_refresh_token(subject=username)
        return {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
            "expires_in": settings.jwt.expiration_minutes * 60,
        }

    def verify_access_token(self, token: str) -> dict[str, Any]:
        return self._jwt.verify_access_token(token)

    def refresh_access_token(self, refresh_token: str) -> dict[str, Any]:
        payload = self._jwt.verify_refresh_token(refresh_token)
        subject = payload["sub"]
        # Re-issue access token (role must be fetched from DB in real impl)
        access = self._jwt.create_access_token(subject=subject, role="viewer")
        from src.infrastructure.config import get_settings
        settings = get_settings()
        return {
            "access_token": access,
            "token_type": "bearer",
            "expires_in": settings.jwt.expiration_minutes * 60,
        }


class AuditService:
    """Audit logging service for security-critical operations."""

    @staticmethod
    async def log(
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        user_id: str | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        logger.info(
            "audit_event",
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            details=details,
            ip_address=ip_address,
        )


__all__ = ["AuthService", "AuditService"]