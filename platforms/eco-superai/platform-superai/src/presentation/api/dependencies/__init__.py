"""FastAPI dependency injection providers.

Centralised DI for database sessions, authentication, authorisation,
and repository instances.
"""
from __future__ import annotations

from typing import Any, AsyncGenerator, Callable, Sequence

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.exceptions import (
    AuthenticationException,
    AuthorizationException,
    InvalidTokenException,
    TokenExpiredException,
)
from src.domain.value_objects.role import Permission, RolePermissions, UserRole
from src.infrastructure.security import JWTHandler, RBACEnforcer

_bearer_scheme = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Database session
# ---------------------------------------------------------------------------

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Async generator that yields an ``AsyncSession`` and handles
    commit / rollback semantics automatically.

    Usage in route handlers::

        @router.get("/items")
        async def list_items(session: AsyncSession = Depends(get_db_session)):
            ...
    """
    from src.infrastructure.persistence.database import get_session

    async for session in get_session():
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> dict[str, Any]:
    """Extract and validate a JWT from the ``Authorization: Bearer <token>``
    header.  Returns a dict with at least ``user_id``, ``username``,
    ``role``, and ``status`` keys.

    Raises ``401`` when the token is missing, expired, or invalid.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "UNAUTHORIZED",
                "message": "Missing authentication token",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        jwt_handler = JWTHandler()
        payload = jwt_handler.verify_access_token(credentials.credentials)
        return {
            "user_id": payload.get("user_id", ""),
            "username": payload.get("sub", ""),
            "role": payload.get("role", "viewer"),
            "status": payload.get("status", "active"),
            "permissions": list(
                RolePermissions.get_permissions(
                    UserRole(payload.get("role", "viewer"))
                )
            ),
        }
    except TokenExpiredException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "TOKEN_EXPIRED",
                "message": "Token has expired",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (InvalidTokenException, AuthenticationException):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_TOKEN",
                "message": "Invalid or malformed token",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "AUTHENTICATION_ERROR",
                "message": "Could not validate credentials",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Depends on :func:`get_current_user` and additionally verifies the
    user's ``status`` is ``active``.

    Raises ``403 Forbidden`` when the account is suspended, pending, or
    deleted.
    """
    user_status = current_user.get("status", "active")
    if user_status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "ACCOUNT_INACTIVE",
                "message": f"Account is {user_status}. Only active accounts may access this resource.",
            },
        )
    return current_user


# ---------------------------------------------------------------------------
# Role-based authorisation
# ---------------------------------------------------------------------------

def require_role(*roles: str) -> Callable[..., Any]:
    """Dependency factory that restricts access to users whose ``role`` is
    in the supplied *roles* whitelist.

    Usage::

        @router.get("/admin/dashboard", dependencies=[Depends(require_role("admin", "operator"))])
        async def admin_dashboard(): ...
    """
    allowed: frozenset[str] = frozenset(roles)

    async def _check_role(
        current_user: dict[str, Any] = Depends(get_current_active_user),
    ) -> dict[str, Any]:
        user_role = current_user.get("role", "")
        if user_role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "FORBIDDEN",
                    "message": (
                        f"Role '{user_role}' is not allowed. "
                        f"Required one of: {', '.join(sorted(allowed))}"
                    ),
                },
            )
        return current_user

    return _check_role


def require_permission(permission: Permission) -> Callable[..., Any]:
    """Dependency factory that checks the current user's role has the
    required *permission* (via the domain RBAC model).

    Usage::

        @router.post("/quantum/execute",
                      dependencies=[Depends(require_permission(Permission.QUANTUM_EXECUTE))])
        async def run_quantum_job(): ...
    """

    async def _check_permission(
        current_user: dict[str, Any] = Depends(get_current_active_user),
    ) -> dict[str, Any]:
        try:
            RBACEnforcer.check_permission(current_user["role"], permission)
        except AuthorizationException as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "FORBIDDEN",
                    "message": exc.message,
                },
            )
        return current_user

    return _check_permission


# ---------------------------------------------------------------------------
# Repository providers
# ---------------------------------------------------------------------------

async def get_user_repository(
    session: AsyncSession = Depends(get_db_session),
) -> Any:
    """Provide a :class:`SQLAlchemyUserRepository` bound to the current
    database session.
    """
    from src.infrastructure.persistence.repositories import SQLAlchemyUserRepository

    return SQLAlchemyUserRepository(session)


async def get_quantum_job_repository(
    session: AsyncSession = Depends(get_db_session),
) -> Any:
    """Provide a :class:`SQLAlchemyQuantumJobRepository` bound to the
    current database session.
    """
    from src.infrastructure.persistence.repositories import SQLAlchemyQuantumJobRepository

    return SQLAlchemyQuantumJobRepository(session)


# ---------------------------------------------------------------------------
# Utility dependencies
# ---------------------------------------------------------------------------

def get_client_ip(request: Request) -> str:
    """Extract the real client IP, respecting ``X-Forwarded-For``."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    x_real_ip = request.headers.get("X-Real-IP")
    if x_real_ip:
        return x_real_ip.strip()
    return request.client.host if request.client else "unknown"


def require_admin() -> Callable[..., Any]:
    """Convenience shortcut: require ``admin:full`` permission."""
    return require_permission(Permission.ADMIN_FULL)


__all__ = [
    "get_db_session",
    "get_current_user",
    "get_current_active_user",
    "require_role",
    "require_permission",
    "require_admin",
    "get_user_repository",
    "get_quantum_job_repository",
    "get_client_ip",
]
