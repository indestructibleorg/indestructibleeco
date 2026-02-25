"""Unit tests for domain entities and value objects."""
from __future__ import annotations

import pytest

from src.domain.entities.base import AggregateRoot, DomainEvent, Entity, ValueObject
from src.domain.entities.user import User, UserRole, UserStatus
from src.domain.value_objects.email import Email
from src.domain.value_objects.password import HashedPassword
from src.domain.value_objects.role import Permission, RolePermissions, UserRole as RoleEnum
from src.domain.exceptions import InvalidEmailError, WeakPasswordError, EntityStateException


class TestEntity:
    def test_entity_has_id(self):
        entity = Entity()
        assert entity.id is not None
        assert len(entity.id) == 36  # UUID format

    def test_entity_has_timestamps(self):
        entity = Entity()
        assert entity.created_at is not None
        assert entity.updated_at is not None

    def test_entity_equality_by_id(self):
        e1 = Entity(id="abc-123")
        e2 = Entity(id="abc-123")
        e3 = Entity(id="xyz-789")
        assert e1 == e2
        assert e1 != e3

    def test_entity_hash(self):
        e1 = Entity(id="abc-123")
        e2 = Entity(id="abc-123")
        assert hash(e1) == hash(e2)


class TestAggregateRoot:
    def test_aggregate_version_starts_at_zero(self):
        agg = AggregateRoot()
        assert agg.version == 0

    def test_increment_version(self):
        agg = AggregateRoot()
        agg.increment_version()
        assert agg.version == 1

    def test_domain_events(self):
        agg = AggregateRoot()
        event = DomainEvent(event_type="test.event", aggregate_id=agg.id)
        agg.raise_event(event)
        events = agg.collect_events()
        assert len(events) == 1
        assert events[0].event_type == "test.event"

    def test_collect_events_clears_list(self):
        agg = AggregateRoot()
        agg.raise_event(DomainEvent(event_type="test"))
        agg.collect_events()
        assert len(agg.collect_events()) == 0


class TestValueObject:
    def test_value_object_equality(self):
        vo1 = ValueObject()
        vo2 = ValueObject()
        assert vo1 == vo2

    def test_value_object_immutable(self):
        vo = ValueObject()
        with pytest.raises(Exception):
            vo.some_field = "value"  # type: ignore


class TestEmail:
    def test_valid_email(self):
        email = Email.create("User@Example.COM")
        assert email.value == "user@example.com"

    def test_email_domain(self):
        email = Email.create("test@company.io")
        assert email.domain == "company.io"

    def test_email_local_part(self):
        email = Email.create("john.doe@example.com")
        assert email.local_part == "john.doe"

    def test_invalid_email_raises(self):
        with pytest.raises(InvalidEmailError):
            Email.create("not-an-email")

    def test_empty_email_raises(self):
        with pytest.raises(InvalidEmailError):
            Email.create("")

    def test_email_str(self):
        email = Email.create("test@example.com")
        assert str(email) == "test@example.com"


class TestHashedPassword:
    def test_hash_and_verify(self):
        pwd = HashedPassword.from_plain("SecureP@ss1")
        assert pwd.verify("SecureP@ss1")
        assert not pwd.verify("wrong")

    def test_hash_is_not_plaintext(self):
        pwd = HashedPassword.from_plain("SecureP@ss1")
        assert pwd.value != "SecureP@ss1"
        assert pwd.value.startswith("$2b$")

    def test_weak_password_no_uppercase(self):
        with pytest.raises(WeakPasswordError):
            HashedPassword.from_plain("nouppercase1")

    def test_weak_password_too_short(self):
        with pytest.raises(WeakPasswordError):
            HashedPassword.from_plain("Ab1")

    def test_weak_password_no_digit(self):
        with pytest.raises(WeakPasswordError):
            HashedPassword.from_plain("NoDigitHere")

    def test_str_hides_value(self):
        pwd = HashedPassword.from_plain("SecureP@ss1")
        assert "HASHED" in str(pwd)


class TestRolePermissions:
    def test_admin_has_all_permissions(self):
        perms = RolePermissions.get_permissions(RoleEnum.ADMIN)
        assert Permission.ADMIN_FULL in perms
        assert Permission.QUANTUM_EXECUTE in perms

    def test_viewer_limited_permissions(self):
        perms = RolePermissions.get_permissions(RoleEnum.VIEWER)
        assert Permission.USER_READ in perms
        assert Permission.ADMIN_FULL not in perms
        assert Permission.QUANTUM_EXECUTE not in perms

    def test_scientist_can_execute_quantum(self):
        assert RolePermissions.has_permission(RoleEnum.SCIENTIST, Permission.QUANTUM_EXECUTE)

    def test_viewer_cannot_execute_quantum(self):
        assert not RolePermissions.has_permission(RoleEnum.VIEWER, Permission.QUANTUM_EXECUTE)

    def test_has_any_permission(self):
        assert RolePermissions.has_any_permission(
            RoleEnum.DEVELOPER,
            {Permission.QUANTUM_EXECUTE, Permission.ADMIN_FULL},
        )


class TestUser:
    def test_create_user(self):
        email = Email.create("test@example.com")
        pwd = HashedPassword.from_plain("SecureP@ss1")
        user = User.create(
            username="testuser",
            email=email,
            hashed_password=pwd,
            full_name="Test User",
            role=UserRole.DEVELOPER,
        )
        assert user.username == "testuser"
        assert user.status == UserStatus.PENDING_VERIFICATION

    def test_suspend_user(self):
        email = Email.create("test@example.com")
        pwd = HashedPassword.from_plain("SecureP@ss1")
        user = User.create(username="testuser", email=email, hashed_password=pwd, full_name="Test", role=UserRole.DEVELOPER)
        user.suspend("policy violation")
        assert user.status == UserStatus.SUSPENDED

    def test_activate_suspended_user(self):
        email = Email.create("test@example.com")
        pwd = HashedPassword.from_plain("SecureP@ss1")
        user = User.create(username="testuser", email=email, hashed_password=pwd, full_name="Test", role=UserRole.DEVELOPER)
        user.suspend("test")
        user.activate()
        assert user.status == UserStatus.ACTIVE