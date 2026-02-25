"""Unit tests for domain exceptions."""
from __future__ import annotations

import pytest

from src.domain.exceptions import (
    DomainException,
    EntityNotFoundException,
    EntityAlreadyExistsException,
    EntityStateException,
    InvalidEmailError,
    WeakPasswordError,
    AuthenticationException,
    AuthorizationException,
    TokenExpiredException,
    InvalidTokenException,
    BusinessRuleViolation,
    ConcurrencyConflictException,
    RateLimitExceededException,
)


class TestDomainExceptions:
    def test_base_domain_exception(self):
        exc = DomainException("test error", "TEST_CODE")
        assert exc.message == "test error"
        assert exc.code == "TEST_CODE"
        assert str(exc) == "test error"

    def test_entity_not_found(self):
        exc = EntityNotFoundException("User", "abc-123")
        assert "User" in exc.message
        assert "abc-123" in exc.message
        assert exc.code == "ENTITY_NOT_FOUND"
        assert exc.entity_type == "User"
        assert exc.entity_id == "abc-123"

    def test_entity_already_exists(self):
        exc = EntityAlreadyExistsException("User", "email", "test@test.com")
        assert "email" in exc.message
        assert exc.code == "ENTITY_ALREADY_EXISTS"

    def test_entity_state_exception(self):
        exc = EntityStateException("User", "suspended", "delete")
        assert "suspended" in exc.message
        assert "delete" in exc.message

    def test_invalid_email(self):
        exc = InvalidEmailError("bad-email")
        assert "bad-email" in exc.message
        assert exc.code == "INVALID_EMAIL"

    def test_weak_password(self):
        exc = WeakPasswordError(["too short", "no digit"])
        assert "too short" in exc.message
        assert len(exc.violations) == 2

    def test_authentication_exception(self):
        exc = AuthenticationException()
        assert exc.code == "UNAUTHORIZED"

    def test_authorization_exception(self):
        exc = AuthorizationException("no access")
        assert exc.code == "FORBIDDEN"

    def test_token_expired(self):
        exc = TokenExpiredException()
        assert exc.code == "TOKEN_EXPIRED"

    def test_invalid_token(self):
        exc = InvalidTokenException()
        assert exc.code == "INVALID_TOKEN"

    def test_business_rule_violation(self):
        exc = BusinessRuleViolation("max users", "limit is 100")
        assert "max users" in exc.message
        assert "limit is 100" in exc.message

    def test_concurrency_conflict(self):
        exc = ConcurrencyConflictException("User", "abc")
        assert "abc" in exc.message

    def test_rate_limit_exceeded(self):
        exc = RateLimitExceededException(100, 60)
        assert exc.limit == 100
        assert exc.window_seconds == 60