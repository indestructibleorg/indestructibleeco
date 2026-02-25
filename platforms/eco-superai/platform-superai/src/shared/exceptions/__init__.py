"""Infrastructure exception hierarchy for the SuperAI Platform.

Provides a structured exception taxonomy for infrastructure-level failures
(database, cache, external services, configuration, serialization) that is
separate from the domain exception hierarchy.  The presentation layer maps
these exceptions to appropriate HTTP status codes via global exception
handlers.
"""
from __future__ import annotations

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


# ---------------------------------------------------------------------------
# Base infrastructure exception
# ---------------------------------------------------------------------------

class InfrastructureException(Exception):
    """Base exception for all infrastructure-level failures.

    Every infrastructure exception carries a human-readable *message* and a
    machine-readable *code* that the exception handlers translate into the
    ``error.code`` field of API error responses.
    """

    def __init__(self, message: str, code: str = "INFRASTRUCTURE_ERROR") -> None:
        self.message = message
        self.code = code
        super().__init__(message)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(code={self.code!r}, message={self.message!r})"


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

class DatabaseConnectionError(InfrastructureException):
    """Raised when the application cannot connect to or communicate with the
    primary database (PostgreSQL).
    """

    def __init__(self, details: str = "") -> None:
        msg = "Database connection failed"
        if details:
            msg = f"{msg}: {details}"
        super().__init__(msg, "DB_CONNECTION_ERROR")


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

class CacheConnectionError(InfrastructureException):
    """Raised when the application cannot connect to or communicate with the
    caching layer (Redis).
    """

    def __init__(self, details: str = "") -> None:
        msg = "Cache connection failed"
        if details:
            msg = f"{msg}: {details}"
        super().__init__(msg, "CACHE_CONNECTION_ERROR")


# ---------------------------------------------------------------------------
# External services
# ---------------------------------------------------------------------------

class ExternalServiceError(InfrastructureException):
    """Raised when a call to an external service (Kubernetes API, third-party
    API, etc.) fails or returns an unexpected response.

    The ``service`` attribute identifies which service failed so that error
    handlers and monitoring can provide actionable context.
    """

    def __init__(self, service: str, details: str = "") -> None:
        msg = f"External service '{service}' error"
        if details:
            msg = f"{msg}: {details}"
        super().__init__(msg, "EXTERNAL_SERVICE_ERROR")
        self.service = service


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

class ConfigurationError(InfrastructureException):
    """Raised when the application encounters an invalid, missing, or
    inconsistent configuration value (e.g. missing required environment
    variable, invalid URL format, unsupported enum variant).
    """

    def __init__(self, details: str = "") -> None:
        msg = "Configuration error"
        if details:
            msg = f"{msg}: {details}"
        super().__init__(msg, "CONFIGURATION_ERROR")


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

class SerializationError(InfrastructureException):
    """Raised when serialization or deserialization of data fails (JSON
    encode/decode, Protobuf, MessagePack, etc.).
    """

    def __init__(self, details: str = "") -> None:
        msg = "Serialization error"
        if details:
            msg = f"{msg}: {details}"
        super().__init__(msg, "SERIALIZATION_ERROR")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__ = [
    # Domain (re-exported for convenience)
    "DomainException",
    "EntityNotFoundException",
    "EntityAlreadyExistsException",
    "EntityStateException",
    "InvalidEmailError",
    "WeakPasswordError",
    "AuthenticationException",
    "AuthorizationException",
    "InvalidTokenException",
    "TokenExpiredException",
    "BusinessRuleViolation",
    "ConcurrencyConflictException",
    "RateLimitExceededException",
    # Infrastructure
    "InfrastructureException",
    "DatabaseConnectionError",
    "CacheConnectionError",
    "ExternalServiceError",
    "ConfigurationError",
    "SerializationError",
]
