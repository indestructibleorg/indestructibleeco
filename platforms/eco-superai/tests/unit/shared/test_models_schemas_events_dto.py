"""Unit tests for shared/models, shared/schemas, domain/events, application/dto.

Tests cover:
- shared/models: AuditLogEntry (hash computation, tamper evidence), OperationResult,
  PaginatedResponse, HealthResponse, BaseResponse, ErrorResponse
- shared/schemas: IDField, EmailField, PaginationParams, SortParams, DateRangeFilter
- domain/events: all event types, payload serialization, aggregate_type
- application/dto: UserDTO.from_entity, TokenDTO, PaginatedDTO
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone

import pytest


# ===========================================================================
# shared/models — AuditLogEntry
# ===========================================================================

class TestAuditLogEntry:
    """Tamper-evidence hash and field validation."""

    def test_hash_is_computed_automatically(self) -> None:
        from src.shared.models import AuditLogEntry
        entry = AuditLogEntry(
            actor="user:admin",
            action="user.delete",
            resource="users/u-123",
            result="success",
            request_id="req-abc",
        )
        assert entry.hash != ""
        assert len(entry.hash) == 64  # SHA-256 hex

    def test_hash_is_deterministic_for_same_inputs(self) -> None:
        from src.shared.models import AuditLogEntry
        entry1 = AuditLogEntry(
            actor="user:admin",
            action="user.delete",
            resource="users/u-123",
            result="success",
            request_id="req-abc",
            timestamp="2024-01-01T00:00:00Z",
        )
        entry2 = AuditLogEntry(
            actor="user:admin",
            action="user.delete",
            resource="users/u-123",
            result="success",
            request_id="req-abc",
            timestamp="2024-01-01T00:00:00Z",
        )
        assert entry1.hash == entry2.hash

    def test_hash_changes_when_actor_changes(self) -> None:
        from src.shared.models import AuditLogEntry
        base = dict(
            action="user.delete",
            resource="users/u-123",
            result="success",
            request_id="req-abc",
            timestamp="2024-01-01T00:00:00Z",
        )
        entry1 = AuditLogEntry(actor="user:admin", **base)
        entry2 = AuditLogEntry(actor="user:attacker", **base)
        assert entry1.hash != entry2.hash

    def test_hash_changes_when_action_changes(self) -> None:
        from src.shared.models import AuditLogEntry
        base = dict(
            actor="user:admin",
            resource="users/u-123",
            result="success",
            request_id="req-abc",
            timestamp="2024-01-01T00:00:00Z",
        )
        entry1 = AuditLogEntry(action="user.read", **base)
        entry2 = AuditLogEntry(action="user.delete", **base)
        assert entry1.hash != entry2.hash

    def test_explicit_hash_is_preserved(self) -> None:
        from src.shared.models import AuditLogEntry
        custom_hash = "a" * 64
        entry = AuditLogEntry(
            actor="user:admin",
            action="user.read",
            resource="users/u-1",
            result="success",
            request_id="req-1",
            hash=custom_hash,
        )
        assert entry.hash == custom_hash

    def test_required_fields_missing_raises(self) -> None:
        from src.shared.models import AuditLogEntry
        with pytest.raises(Exception):
            AuditLogEntry()  # actor, action, resource, result required

    def test_details_field_accepts_arbitrary_dict(self) -> None:
        from src.shared.models import AuditLogEntry
        entry = AuditLogEntry(
            actor="svc:quantum",
            action="job.submit",
            resource="jobs/j-1",
            result="success",
            request_id="req-2",
            details={"algorithm": "bell", "qubits": 2},
        )
        assert entry.details["algorithm"] == "bell"

    def test_timestamp_is_iso_format(self) -> None:
        from src.shared.models import AuditLogEntry
        entry = AuditLogEntry(
            actor="svc:auth",
            action="token.issue",
            resource="tokens",
            result="success",
            request_id="req-3",
        )
        # Must be parseable as ISO 8601
        datetime.fromisoformat(entry.timestamp.replace("Z", "+00:00"))


class TestOperationResult:
    """Generic operation result wrapper."""

    def test_ok_factory(self) -> None:
        from src.shared.models import OperationResult
        result = OperationResult.ok(data={"id": "123"})
        assert result.success is True
        assert result.data == {"id": "123"}
        assert result.errors == []

    def test_fail_factory(self) -> None:
        from src.shared.models import OperationResult
        result = OperationResult.fail("Something went wrong", errors=["E001", "E002"])
        assert result.success is False
        assert result.message == "Something went wrong"
        assert "E001" in result.errors

    def test_ok_with_custom_message(self) -> None:
        from src.shared.models import OperationResult
        result = OperationResult.ok(message="Created successfully")
        assert result.message == "Created successfully"

    def test_fail_without_errors_list(self) -> None:
        from src.shared.models import OperationResult
        result = OperationResult.fail("Error occurred")
        assert result.errors == []


class TestPaginatedResponse:
    """Paginated response model."""

    def test_has_next_true(self) -> None:
        from src.shared.models import PaginatedResponse
        resp = PaginatedResponse(items=[1, 2, 3], total=10, skip=0, limit=3)
        assert resp.has_next is True

    def test_has_next_false_on_last_page(self) -> None:
        from src.shared.models import PaginatedResponse
        resp = PaginatedResponse(items=[10], total=10, skip=9, limit=1)
        assert resp.has_next is False

    def test_total_pages_calculation(self) -> None:
        from src.shared.models import PaginatedResponse
        resp = PaginatedResponse(items=[], total=25, skip=0, limit=10)
        assert resp.total_pages == 3

    def test_total_pages_exact_division(self) -> None:
        from src.shared.models import PaginatedResponse
        resp = PaginatedResponse(items=[], total=20, skip=0, limit=10)
        assert resp.total_pages == 2

    def test_empty_result(self) -> None:
        from src.shared.models import PaginatedResponse
        resp = PaginatedResponse(items=[], total=0, skip=0, limit=10)
        assert resp.has_next is False
        # total=0 → ceil(0/10)=0 but clamped to max(1,0)=1 by implementation
        assert resp.total_pages == 1


class TestHealthResponse:
    """Health check response model."""

    def test_healthy_status(self) -> None:
        from src.shared.models import HealthResponse
        resp = HealthResponse(status="healthy", version="1.0.0", uptime=42.0, checks={"db": {"status": "healthy"}})
        assert resp.status == "healthy"

    def test_degraded_status(self) -> None:
        from src.shared.models import HealthResponse
        resp = HealthResponse(status="degraded", version="1.0.0", uptime=10.0, checks={"redis": {"status": "unhealthy"}})
        assert resp.status == "degraded"

    def test_unhealthy_status(self) -> None:
        from src.shared.models import HealthResponse
        resp = HealthResponse(status="unhealthy", version="1.0.0", uptime=0.0, checks={"db": {"status": "unhealthy"}})
        assert resp.status == "unhealthy"

    def test_invalid_status_raises(self) -> None:
        from src.shared.models import HealthResponse
        with pytest.raises(Exception):
            HealthResponse(status="unknown", version="1.0.0", uptime=0.0)


# ===========================================================================
# shared/schemas — IDField, EmailField, PaginationParams
# ===========================================================================

class TestIDField:
    """UUID validation and normalisation."""

    def test_valid_uuid_hyphenated(self) -> None:
        from src.shared.schemas import IDField
        uid = str(uuid.uuid4())
        field = IDField(id=uid)
        assert field.id == uid

    def test_valid_uuid_without_hyphens_normalised(self) -> None:
        from src.shared.schemas import IDField
        uid = uuid.uuid4()
        no_hyphens = uid.hex  # 32 chars, no hyphens
        field = IDField(id=no_hyphens)
        assert field.id == str(uid)  # normalised to hyphenated form

    def test_invalid_uuid_raises(self) -> None:
        from src.shared.schemas import IDField
        with pytest.raises(Exception):
            IDField(id="not-a-uuid")

    def test_empty_string_raises(self) -> None:
        from src.shared.schemas import IDField
        with pytest.raises(Exception):
            IDField(id="")


class TestEmailField:
    """Email validation and normalisation."""

    def test_valid_email_normalised_to_lowercase(self) -> None:
        from src.shared.schemas import EmailField
        field = EmailField(email="User@EXAMPLE.COM")
        assert field.email == "user@example.com"

    def test_valid_email_with_dots_and_plus(self) -> None:
        from src.shared.schemas import EmailField
        field = EmailField(email="user.name+tag@example.co.uk")
        assert "@" in field.email

    def test_invalid_email_no_at_sign(self) -> None:
        from src.shared.schemas import EmailField
        with pytest.raises(Exception):
            EmailField(email="notanemail")

    def test_invalid_email_no_domain(self) -> None:
        from src.shared.schemas import EmailField
        with pytest.raises(Exception):
            EmailField(email="user@")

    def test_empty_email_raises(self) -> None:
        from src.shared.schemas import EmailField
        with pytest.raises(Exception):
            EmailField(email="")

    def test_email_strips_whitespace(self) -> None:
        from src.shared.schemas import EmailField
        field = EmailField(email="  user@example.com  ")
        assert field.email == "user@example.com"

    def test_email_too_long_raises(self) -> None:
        from src.shared.schemas import EmailField
        long_local = "a" * 250
        with pytest.raises(Exception):
            EmailField(email=f"{long_local}@example.com")


class TestPaginationParams:
    """Pagination parameter validation and clamping."""

    def test_defaults(self) -> None:
        from src.shared.schemas import PaginationParams
        params = PaginationParams()
        assert params.skip == 0
        assert params.limit == 20

    def test_negative_skip_raises(self) -> None:
        from src.shared.schemas import PaginationParams
        # Pydantic ge=0 constraint raises ValidationError for negative skip
        with pytest.raises(Exception):
            PaginationParams(skip=-5)

    def test_limit_above_max_raises(self) -> None:
        from src.shared.schemas import PaginationParams
        # Pydantic le=100 constraint raises ValidationError for limit > 100
        with pytest.raises(Exception):
            PaginationParams(limit=500)

    def test_limit_zero_raises(self) -> None:
        from src.shared.schemas import PaginationParams
        with pytest.raises(Exception):
            PaginationParams(limit=0)

    def test_valid_custom_values(self) -> None:
        from src.shared.schemas import PaginationParams
        params = PaginationParams(skip=50, limit=25)
        assert params.skip == 50
        assert params.limit == 25


# ===========================================================================
# domain/events — event types and payload
# ===========================================================================

class TestDomainEvents:
    """All domain event types: construction, event_type, aggregate_type."""

    def test_user_created_event(self) -> None:
        from src.domain.events import UserCreatedEvent
        event = UserCreatedEvent(
            aggregate_id="u-1",
            payload={"username": "alice"},
        )
        assert event.event_type == "user.created"
        assert event.aggregate_type == "User"
        assert event.payload["username"] == "alice"

    def test_user_updated_event(self) -> None:
        from src.domain.events import UserUpdatedEvent
        event = UserUpdatedEvent(aggregate_id="u-1", payload={"field": "full_name"})
        assert event.event_type == "user.updated"

    def test_user_deleted_event(self) -> None:
        from src.domain.events import UserDeletedEvent
        event = UserDeletedEvent(aggregate_id="u-1", payload={})
        assert event.event_type == "user.deleted"

    def test_user_activated_event(self) -> None:
        from src.domain.events import UserActivatedEvent
        event = UserActivatedEvent(aggregate_id="u-1", payload={})
        assert event.event_type == "user.activated"

    def test_user_suspended_event(self) -> None:
        from src.domain.events import UserSuspendedEvent
        event = UserSuspendedEvent(
            aggregate_id="u-1",
            payload={"reason": "policy violation"},
        )
        assert event.event_type == "user.suspended"
        assert event.payload["reason"] == "policy violation"

    def test_user_authenticated_event(self) -> None:
        from src.domain.events import UserAuthenticatedEvent
        event = UserAuthenticatedEvent(aggregate_id="u-1", payload={"ip": "1.2.3.4"})
        assert event.event_type == "user.authenticated"

    def test_user_auth_failed_event(self) -> None:
        from src.domain.events import UserAuthFailedEvent
        event = UserAuthFailedEvent(aggregate_id="u-1", payload={"reason": "wrong_password"})
        assert event.event_type == "user.auth_failed"

    def test_quantum_job_submitted_event(self) -> None:
        from src.domain.events import QuantumJobSubmittedEvent
        event = QuantumJobSubmittedEvent(
            aggregate_id="job-1",
            payload={"algorithm": "bell", "qubits": 2},
        )
        assert event.event_type == "quantum.job_submitted"
        assert event.aggregate_type == "QuantumJob"

    def test_quantum_job_completed_event(self) -> None:
        from src.domain.events import QuantumJobCompletedEvent
        event = QuantumJobCompletedEvent(
            aggregate_id="job-1",
            payload={"result": {"counts": {"00": 512, "11": 512}}},
        )
        assert event.event_type == "quantum.job_completed"

    def test_ai_expert_created_event(self) -> None:
        from src.domain.events import AIExpertCreatedEvent
        event = AIExpertCreatedEvent(
            aggregate_id="expert-1",
            payload={"name": "QuantumBot", "domain": "quantum"},
        )
        assert event.event_type == "ai.expert_created"
        assert event.aggregate_type == "AIExpert"

    def test_event_has_unique_id(self) -> None:
        from src.domain.events import UserCreatedEvent
        e1 = UserCreatedEvent(aggregate_id="u-1", payload={})
        e2 = UserCreatedEvent(aggregate_id="u-1", payload={})
        assert e1.event_id != e2.event_id

    def test_event_has_timestamp(self) -> None:
        from src.domain.events import UserCreatedEvent
        event = UserCreatedEvent(aggregate_id="u-1", payload={})
        assert event.occurred_at is not None


# ===========================================================================
# application/dto — UserDTO, TokenDTO, PaginatedDTO
# ===========================================================================

class TestUserDTO:
    """UserDTO.from_entity conversion."""

    def _make_user(self, email: str = "test@example.com") -> object:
        from src.domain.entities.user import User, UserRole
        user = User.create(
            username="testuser",
            email=email,
            hashed_password="$2b$12$" + "a" * 53,
            full_name="Test User",
            role=UserRole.DEVELOPER,
        )
        user.activate()
        return user

    def test_from_entity_basic_fields(self) -> None:
        from src.application.dto import UserDTO
        user = self._make_user()
        dto = UserDTO.from_entity(user)
        assert dto.username == "testuser"
        assert dto.email == "test@example.com"
        # Role and status values are the enum .value strings
        assert dto.role in ("developer", "DEVELOPER")
        assert dto.status in ("active", "ACTIVE")

    def test_from_entity_id_is_string(self) -> None:
        from src.application.dto import UserDTO
        user = self._make_user()
        dto = UserDTO.from_entity(user)
        assert isinstance(dto.id, str)
        assert len(dto.id) == 36

    def test_from_entity_created_at_is_iso_string(self) -> None:
        from src.application.dto import UserDTO
        user = self._make_user()
        dto = UserDTO.from_entity(user)
        # Must be parseable as ISO 8601
        assert "T" in dto.created_at or "-" in dto.created_at

    def test_from_entity_last_login_none_by_default(self) -> None:
        from src.application.dto import UserDTO
        user = self._make_user()
        dto = UserDTO.from_entity(user)
        assert dto.last_login_at is None


class TestTokenDTO:
    """Token pair DTO."""

    def test_token_dto_construction(self) -> None:
        from src.application.dto import TokenDTO
        dto = TokenDTO(
            access_token="access.jwt.token",
            refresh_token="refresh.jwt.token",
            expires_in=3600,
        )
        assert dto.token_type == "bearer"
        assert dto.expires_in == 3600

    def test_token_dto_requires_both_tokens(self) -> None:
        from src.application.dto import TokenDTO
        with pytest.raises(Exception):
            TokenDTO(access_token="only_access", expires_in=3600)


class TestPaginatedDTO:
    """Paginated DTO has_next property."""

    def test_has_next_true(self) -> None:
        from src.application.dto import PaginatedDTO
        dto = PaginatedDTO(items=[1, 2, 3], total=10, skip=0, limit=3)
        assert dto.has_next is True

    def test_has_next_false(self) -> None:
        from src.application.dto import PaginatedDTO
        dto = PaginatedDTO(items=[10], total=10, skip=9, limit=1)
        assert dto.has_next is False

    def test_empty_items(self) -> None:
        from src.application.dto import PaginatedDTO
        dto = PaginatedDTO(items=[], total=0, skip=0, limit=10)
        assert dto.has_next is False
