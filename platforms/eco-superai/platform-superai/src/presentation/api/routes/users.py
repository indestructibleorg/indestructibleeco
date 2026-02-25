"""User management API routes -- registration, authentication, CRUD, lifecycle."""
from __future__ import annotations

import structlog
from typing import Any

from fastapi import APIRouter, Depends, Query, Request, status

from src.application.services import AuditService, AuthService
from src.application.use_cases.user_management import (
    ActivateUserUseCase,
    AuthenticateUserUseCase,
    CreateUserUseCase,
    DeleteUserUseCase,
    GetUserUseCase,
    ListUsersUseCase,
    SuspendUserUseCase,
    UpdateUserUseCase,
)
from src.domain.value_objects.role import Permission
from src.presentation.api.dependencies import (
    get_client_ip,
    get_current_user,
    get_user_repository,
    require_permission,
)
from src.presentation.api.schemas import (
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserCreateRequest,
    UserListResponse,
    UserResponse,
    UserUpdateRequest,
)

logger = structlog.get_logger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Public endpoints (no authentication required)
# ---------------------------------------------------------------------------


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register_user(
    body: UserCreateRequest,
    request: Request,
    repo=Depends(get_user_repository),
    client_ip: str = Depends(get_client_ip),
) -> dict[str, Any]:
    """Create a new user account.  Open to the public; the default role is
    ``viewer``.  Administrative role assignment requires a separate update
    by an admin.
    """
    use_case = CreateUserUseCase(repo=repo)
    result = await use_case.execute(
        username=body.username,
        email=body.email,
        password=body.password,
        full_name=body.full_name,
        role=body.role,
    )
    await AuditService.log(
        action="user.registered",
        resource_type="User",
        resource_id=result.get("id"),
        details={"username": body.username, "email": body.email, "role": body.role},
        ip_address=client_ip,
        user_agent=request.headers.get("User-Agent"),
    )
    return result


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and obtain JWT tokens",
)
async def login(
    body: LoginRequest,
    request: Request,
    repo=Depends(get_user_repository),
    client_ip: str = Depends(get_client_ip),
) -> dict[str, Any]:
    """Authenticate with username and password.  Returns an access token and
    a refresh token.
    """
    use_case = AuthenticateUserUseCase(repo=repo)
    result = await use_case.execute(username=body.username, password=body.password)
    await AuditService.log(
        action="user.login",
        resource_type="User",
        details={"username": body.username},
        ip_address=client_ip,
        user_agent=request.headers.get("User-Agent"),
    )
    return result


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh an access token",
)
async def refresh_token(body: RefreshTokenRequest) -> dict[str, Any]:
    """Exchange a valid refresh token for a new access token."""
    auth = AuthService()
    result = auth.refresh_access_token(body.refresh_token)
    # The refresh response from AuthService does not include a new refresh token,
    # so we carry the original one forward for client convenience.
    result.setdefault("refresh_token", body.refresh_token)
    return result


# ---------------------------------------------------------------------------
# Authenticated endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the currently authenticated user profile",
)
async def get_me(
    current_user: dict[str, Any] = Depends(get_current_user),
    repo=Depends(get_user_repository),
) -> dict[str, Any]:
    """Return the profile of the user identified by the JWT bearer token."""
    use_case = GetUserUseCase(repo=repo)
    return await use_case.execute(user_id=current_user["user_id"])


@router.get(
    "",
    response_model=UserListResponse,
    summary="List users (paginated)",
)
async def list_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Page size"),
    search: str | None = Query(None, max_length=100, description="Search by username or email"),
    current_user: dict[str, Any] = Depends(require_permission(Permission.USER_READ)),
    repo=Depends(get_user_repository),
) -> dict[str, Any]:
    """List users with optional search.  Requires ``user:read`` permission."""
    use_case = ListUsersUseCase(repo=repo)
    return await use_case.execute(skip=skip, limit=limit, search=search)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
)
async def get_user(
    user_id: str,
    current_user: dict[str, Any] = Depends(require_permission(Permission.USER_READ)),
    repo=Depends(get_user_repository),
) -> dict[str, Any]:
    """Retrieve a single user record.  Requires ``user:read`` permission."""
    use_case = GetUserUseCase(repo=repo)
    return await use_case.execute(user_id=user_id)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user profile",
)
async def update_user(
    user_id: str,
    body: UserUpdateRequest,
    request: Request,
    current_user: dict[str, Any] = Depends(require_permission(Permission.USER_WRITE)),
    repo=Depends(get_user_repository),
    client_ip: str = Depends(get_client_ip),
) -> dict[str, Any]:
    """Update mutable fields on a user record.  Role changes require
    ``user:write`` permission.
    """
    use_case = UpdateUserUseCase(repo=repo)
    result = await use_case.execute(user_id=user_id, **body.model_dump(exclude_none=True))
    await AuditService.log(
        action="user.updated",
        resource_type="User",
        resource_id=user_id,
        user_id=current_user["user_id"],
        details={"changed_fields": body.model_dump(exclude_none=True)},
        ip_address=client_ip,
        user_agent=request.headers.get("User-Agent"),
    )
    return result


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user (soft delete)",
)
async def delete_user(
    user_id: str,
    request: Request,
    current_user: dict[str, Any] = Depends(require_permission(Permission.USER_DELETE)),
    repo=Depends(get_user_repository),
    client_ip: str = Depends(get_client_ip),
) -> None:
    """Soft-delete a user.  Requires ``user:delete`` permission."""
    use_case = DeleteUserUseCase(repo=repo)
    await use_case.execute(user_id=user_id)
    await AuditService.log(
        action="user.deleted",
        resource_type="User",
        resource_id=user_id,
        user_id=current_user["user_id"],
        ip_address=client_ip,
        user_agent=request.headers.get("User-Agent"),
    )


@router.post(
    "/{user_id}/activate",
    response_model=UserResponse,
    summary="Activate a suspended user",
)
async def activate_user(
    user_id: str,
    request: Request,
    current_user: dict[str, Any] = Depends(require_permission(Permission.USER_ADMIN)),
    repo=Depends(get_user_repository),
    client_ip: str = Depends(get_client_ip),
) -> dict[str, Any]:
    """Re-activate a previously suspended user account.  Requires ``user:admin``
    permission.
    """
    use_case = ActivateUserUseCase(repo=repo)
    result = await use_case.execute(user_id=user_id)
    await AuditService.log(
        action="user.activated",
        resource_type="User",
        resource_id=user_id,
        user_id=current_user["user_id"],
        ip_address=client_ip,
        user_agent=request.headers.get("User-Agent"),
    )
    return result


@router.post(
    "/{user_id}/suspend",
    response_model=UserResponse,
    summary="Suspend a user account",
)
async def suspend_user(
    user_id: str,
    request: Request,
    reason: str = Query("", max_length=500, description="Suspension reason"),
    current_user: dict[str, Any] = Depends(require_permission(Permission.USER_ADMIN)),
    repo=Depends(get_user_repository),
    client_ip: str = Depends(get_client_ip),
) -> dict[str, Any]:
    """Suspend a user account, optionally providing a reason.  Requires
    ``user:admin`` permission.
    """
    use_case = SuspendUserUseCase(repo=repo)
    result = await use_case.execute(user_id=user_id, reason=reason)
    await AuditService.log(
        action="user.suspended",
        resource_type="User",
        resource_id=user_id,
        user_id=current_user["user_id"],
        details={"reason": reason},
        ip_address=client_ip,
        user_agent=request.headers.get("User-Agent"),
    )
    return result
