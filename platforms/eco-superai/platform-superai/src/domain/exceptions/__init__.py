"""Domain exception hierarchy — pure business rule violations."""
from __future__ import annotations


class DomainException(Exception):
    """Base domain exception."""

    def __init__(self, message: str, code: str = "DOMAIN_ERROR") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


# --- Entity Exceptions ---

class EntityNotFoundException(DomainException):
    def __init__(self, entity_type: str, entity_id: str) -> None:
        super().__init__(
            message=f"{entity_type} with id '{entity_id}' not found",
            code="ENTITY_NOT_FOUND",
        )
        self.entity_type = entity_type
        self.entity_id = entity_id


class EntityAlreadyExistsException(DomainException):
    def __init__(self, entity_type: str, field: str, value: str) -> None:
        super().__init__(
            message=f"{entity_type} with {field}='{value}' already exists",
            code="ENTITY_ALREADY_EXISTS",
        )
        self.entity_type = entity_type
        self.field = field
        self.value = value


class EntityStateException(DomainException):
    def __init__(self, entity_type: str, current_state: str, attempted_action: str) -> None:
        super().__init__(
            message=f"Cannot {attempted_action} {entity_type} in state '{current_state}'",
            code="INVALID_ENTITY_STATE",
        )


# --- Value Object Exceptions ---

class InvalidEmailError(DomainException):
    def __init__(self, email: str) -> None:
        super().__init__(message=f"Invalid email address: '{email}'", code="INVALID_EMAIL")


class WeakPasswordError(DomainException):
    def __init__(self, violations: list[str]) -> None:
        msg = "Password does not meet requirements: " + "; ".join(violations)
        super().__init__(message=msg, code="WEAK_PASSWORD")
        self.violations = violations


# --- Authorization Exceptions ---

class AuthorizationException(DomainException):
    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(message=message, code="FORBIDDEN")


class AuthenticationException(DomainException):
    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message=message, code="UNAUTHORIZED")


class TokenExpiredException(AuthenticationException):
    def __init__(self) -> None:
        super().__init__(message="Token has expired")
        self.code = "TOKEN_EXPIRED"


class InvalidTokenException(AuthenticationException):
    def __init__(self) -> None:
        super().__init__(message="Invalid or malformed token")
        self.code = "INVALID_TOKEN"


# --- Business Rule Exceptions ---

class BusinessRuleViolation(DomainException):
    def __init__(self, rule: str, details: str = "") -> None:
        msg = f"Business rule violated: {rule}"
        if details:
            msg += f" — {details}"
        super().__init__(message=msg, code="BUSINESS_RULE_VIOLATION")


class ConcurrencyConflictException(DomainException):
    def __init__(self, entity_type: str, entity_id: str) -> None:
        super().__init__(
            message=f"Concurrency conflict on {entity_type} '{entity_id}'. Entity was modified by another process.",
            code="CONCURRENCY_CONFLICT",
        )


class RateLimitExceededException(DomainException):
    def __init__(self, limit: int, window_seconds: int) -> None:
        super().__init__(
            message=f"Rate limit exceeded: {limit} requests per {window_seconds}s",
            code="RATE_LIMITED",
        )
        self.limit = limit
        self.window_seconds = window_seconds