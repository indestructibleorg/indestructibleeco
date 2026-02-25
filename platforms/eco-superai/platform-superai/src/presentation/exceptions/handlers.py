"""Global exception handlers — map domain/infrastructure exceptions to HTTP responses."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse

from src.domain.exceptions import (
    AuthenticationException,
    AuthorizationException,
    BusinessRuleViolation,
    ConcurrencyConflictException,
    DomainException,
    EntityAlreadyExistsException,
    EntityNotFoundException,
    EntityStateException,
    InvalidEmailError,
    InvalidTokenException,
    RateLimitExceededException,
    TokenExpiredException,
    WeakPasswordError,
)
from src.shared.exceptions import (
    CacheConnectionError,
    DatabaseConnectionError,
    ExternalServiceError,
    InfrastructureException,
)

logger = structlog.get_logger(__name__)


def _error_response(status: int, code: str, message: str, details: list | None = None, request_id: str | None = None) -> ORJSONResponse:
    body: dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
            "details": details or [],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    }
    if request_id:
        body["error"]["request_id"] = request_id
    return ORJSONResponse(status_code=status, content=body)


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI app."""

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> ORJSONResponse:
        details = []
        for error in exc.errors():
            loc = " → ".join(str(l) for l in error.get("loc", []))
            details.append({"field": loc, "message": error.get("msg", "")})
        return _error_response(422, "VALIDATION_ERROR", "Invalid request parameters", details)

    @app.exception_handler(EntityNotFoundException)
    async def not_found_handler(request: Request, exc: EntityNotFoundException) -> ORJSONResponse:
        return _error_response(404, exc.code, exc.message)

    @app.exception_handler(EntityAlreadyExistsException)
    async def conflict_handler(request: Request, exc: EntityAlreadyExistsException) -> ORJSONResponse:
        return _error_response(409, exc.code, exc.message)

    @app.exception_handler(EntityStateException)
    async def state_error_handler(request: Request, exc: EntityStateException) -> ORJSONResponse:
        return _error_response(422, exc.code, exc.message)

    @app.exception_handler(InvalidEmailError)
    async def email_error_handler(request: Request, exc: InvalidEmailError) -> ORJSONResponse:
        return _error_response(422, exc.code, exc.message)

    @app.exception_handler(WeakPasswordError)
    async def password_error_handler(request: Request, exc: WeakPasswordError) -> ORJSONResponse:
        details = [{"field": "password", "message": v} for v in exc.violations]
        return _error_response(422, exc.code, exc.message, details)

    @app.exception_handler(TokenExpiredException)
    async def token_expired_handler(request: Request, exc: TokenExpiredException) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=401,
            content={"error": {"code": exc.code, "message": exc.message}},
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(InvalidTokenException)
    async def invalid_token_handler(request: Request, exc: InvalidTokenException) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=401,
            content={"error": {"code": exc.code, "message": exc.message}},
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(AuthenticationException)
    async def auth_error_handler(request: Request, exc: AuthenticationException) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=401,
            content={"error": {"code": exc.code, "message": exc.message}},
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(AuthorizationException)
    async def authz_error_handler(request: Request, exc: AuthorizationException) -> ORJSONResponse:
        return _error_response(403, exc.code, exc.message)

    @app.exception_handler(RateLimitExceededException)
    async def rate_limit_handler(request: Request, exc: RateLimitExceededException) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=429,
            content={"error": {"code": exc.code, "message": exc.message}},
            headers={"Retry-After": str(exc.window_seconds)},
        )

    @app.exception_handler(BusinessRuleViolation)
    async def business_rule_handler(request: Request, exc: BusinessRuleViolation) -> ORJSONResponse:
        return _error_response(422, exc.code, exc.message)

    @app.exception_handler(ConcurrencyConflictException)
    async def concurrency_handler(request: Request, exc: ConcurrencyConflictException) -> ORJSONResponse:
        return _error_response(409, exc.code, exc.message)

    @app.exception_handler(DatabaseConnectionError)
    async def db_error_handler(request: Request, exc: DatabaseConnectionError) -> ORJSONResponse:
        logger.error("database_connection_error", error=exc.message)
        return _error_response(503, exc.code, "Service temporarily unavailable")

    @app.exception_handler(CacheConnectionError)
    async def cache_error_handler(request: Request, exc: CacheConnectionError) -> ORJSONResponse:
        logger.error("cache_connection_error", error=exc.message)
        return _error_response(503, exc.code, "Service temporarily unavailable")

    @app.exception_handler(ExternalServiceError)
    async def external_error_handler(request: Request, exc: ExternalServiceError) -> ORJSONResponse:
        logger.error("external_service_error", service=exc.service, error=exc.message)
        return _error_response(502, exc.code, f"External service error: {exc.service}")

    @app.exception_handler(InfrastructureException)
    async def infra_error_handler(request: Request, exc: InfrastructureException) -> ORJSONResponse:
        logger.error("infrastructure_error", error=exc.message)
        return _error_response(500, exc.code, "Internal server error")

    @app.exception_handler(DomainException)
    async def domain_error_handler(request: Request, exc: DomainException) -> ORJSONResponse:
        return _error_response(400, exc.code, exc.message)

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> ORJSONResponse:
        logger.error("unhandled_exception", error=str(exc), type=type(exc).__name__)
        return _error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")