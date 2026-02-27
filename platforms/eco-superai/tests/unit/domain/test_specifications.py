"""Unit tests for domain specifications.

All tests use real domain entities (User) instead of MagicMock, ensuring
that the specification logic is tested against the actual .status.value
and .role.value access paths used in production.
"""
from __future__ import annotations

import uuid

import pytest

from src.domain.entities.user import User, UserRole, UserStatus
from src.domain.value_objects.email import Email
from src.domain.value_objects.password import HashedPassword
from src.domain.specifications import (
    ActiveUserSpecification,
    UserByEmailDomainSpecification,
    UserByRoleSpecification,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_FAKE_HASH = "$2b$12$LJ3m4ys3Lg.Ry5qFnGmMHOPbEEYpzOEjSMfB7xUqHCDeaIiqHuMy"


def _make_user(
    role: UserRole = UserRole.DEVELOPER,
    status: UserStatus = UserStatus.ACTIVE,
    email: str | None = None,
) -> User:
    """Create a User using the factory method, then force the desired status.

    User.create() always starts with PENDING_VERIFICATION; we mutate the
    status field directly via model_copy to avoid triggering business-rule
    guards (activate/suspend) that would emit unwanted domain events.
    """
    uid = uuid.uuid4().hex[:8]
    user = User.create(
        username=f"user_{uid}",
        email=email or f"user_{uid}@example.com",
        hashed_password=_FAKE_HASH,
        full_name="Test User",
        role=role,
    )
    # Force desired status without going through the state-machine methods
    object.__setattr__(user, "status", status)
    return user


# ---------------------------------------------------------------------------
# ActiveUserSpecification
# ---------------------------------------------------------------------------

class TestActiveUserSpecification:

    def test_active_user_matches(self) -> None:
        spec = ActiveUserSpecification()
        user = _make_user(status=UserStatus.ACTIVE)
        assert spec.is_satisfied_by(user) is True

    def test_suspended_user_does_not_match(self) -> None:
        spec = ActiveUserSpecification()
        user = _make_user(status=UserStatus.SUSPENDED)
        assert spec.is_satisfied_by(user) is False

    def test_pending_user_does_not_match(self) -> None:
        spec = ActiveUserSpecification()
        user = _make_user(status=UserStatus.PENDING_VERIFICATION)
        assert spec.is_satisfied_by(user) is False

    def test_inactive_user_does_not_match(self) -> None:
        spec = ActiveUserSpecification()
        user = _make_user(status=UserStatus.INACTIVE)
        assert spec.is_satisfied_by(user) is False


# ---------------------------------------------------------------------------
# UserByRoleSpecification
# ---------------------------------------------------------------------------

class TestUserByRoleSpecification:

    def test_matching_role_admin(self) -> None:
        spec = UserByRoleSpecification("admin")
        user = _make_user(role=UserRole.ADMIN)
        assert spec.is_satisfied_by(user) is True

    def test_non_matching_role(self) -> None:
        spec = UserByRoleSpecification("admin")
        user = _make_user(role=UserRole.VIEWER)
        assert spec.is_satisfied_by(user) is False

    def test_matching_role_scientist(self) -> None:
        spec = UserByRoleSpecification("scientist")
        user = _make_user(role=UserRole.SCIENTIST)
        assert spec.is_satisfied_by(user) is True

    def test_matching_role_operator(self) -> None:
        spec = UserByRoleSpecification("operator")
        user = _make_user(role=UserRole.OPERATOR)
        assert spec.is_satisfied_by(user) is True


# ---------------------------------------------------------------------------
# UserByEmailDomainSpecification
# ---------------------------------------------------------------------------

class TestUserByEmailDomainSpecification:

    def test_matching_domain(self) -> None:
        spec = UserByEmailDomainSpecification("company.com")
        user = _make_user(email="john@company.com")
        assert spec.is_satisfied_by(user) is True

    def test_non_matching_domain(self) -> None:
        spec = UserByEmailDomainSpecification("company.com")
        user = _make_user(email="john@other.com")
        assert spec.is_satisfied_by(user) is False

    def test_subdomain_does_not_match_parent(self) -> None:
        spec = UserByEmailDomainSpecification("company.com")
        user = _make_user(email="john@sub.company.com")
        # sub.company.com != company.com — must not match
        assert spec.is_satisfied_by(user) is False

    def test_case_insensitive_domain(self) -> None:
        spec = UserByEmailDomainSpecification("Company.COM")
        user = _make_user(email="john@company.com")
        # Email is normalised to lowercase on creation
        assert spec.is_satisfied_by(user) is True


# ---------------------------------------------------------------------------
# Composite specifications
# ---------------------------------------------------------------------------

class TestCompositeSpecifications:

    def test_and_specification_both_true(self) -> None:
        active = ActiveUserSpecification()
        admin = UserByRoleSpecification("admin")
        combined = active.and_(admin)
        user = _make_user(role=UserRole.ADMIN, status=UserStatus.ACTIVE)
        assert combined.is_satisfied_by(user) is True

    def test_and_specification_first_false(self) -> None:
        active = ActiveUserSpecification()
        admin = UserByRoleSpecification("admin")
        combined = active.and_(admin)
        user = _make_user(role=UserRole.ADMIN, status=UserStatus.SUSPENDED)
        assert combined.is_satisfied_by(user) is False

    def test_and_specification_second_false(self) -> None:
        active = ActiveUserSpecification()
        admin = UserByRoleSpecification("admin")
        combined = active.and_(admin)
        user = _make_user(role=UserRole.VIEWER, status=UserStatus.ACTIVE)
        assert combined.is_satisfied_by(user) is False

    def test_or_specification_first_matches(self) -> None:
        admin = UserByRoleSpecification("admin")
        operator = UserByRoleSpecification("operator")
        combined = admin.or_(operator)
        user = _make_user(role=UserRole.ADMIN)
        assert combined.is_satisfied_by(user) is True

    def test_or_specification_second_matches(self) -> None:
        admin = UserByRoleSpecification("admin")
        operator = UserByRoleSpecification("operator")
        combined = admin.or_(operator)
        user = _make_user(role=UserRole.OPERATOR)
        assert combined.is_satisfied_by(user) is True

    def test_or_specification_neither_matches(self) -> None:
        admin = UserByRoleSpecification("admin")
        operator = UserByRoleSpecification("operator")
        combined = admin.or_(operator)
        user = _make_user(role=UserRole.VIEWER)
        assert combined.is_satisfied_by(user) is False

    def test_not_specification_inverts_true(self) -> None:
        active = ActiveUserSpecification()
        inactive = active.not_()
        user = _make_user(status=UserStatus.SUSPENDED)
        assert inactive.is_satisfied_by(user) is True

    def test_not_specification_inverts_false(self) -> None:
        active = ActiveUserSpecification()
        inactive = active.not_()
        user = _make_user(status=UserStatus.ACTIVE)
        assert inactive.is_satisfied_by(user) is False

    def test_complex_chain_and_or_not(self) -> None:
        """active AND (admin OR scientist) AND NOT deleted"""
        active = ActiveUserSpecification()
        admin = UserByRoleSpecification("admin")
        scientist = UserByRoleSpecification("scientist")
        deleted = ActiveUserSpecification().not_()  # inverted — is deleted

        spec = active.and_(admin.or_(scientist))

        # Admin + active: should match
        assert spec.is_satisfied_by(
            _make_user(role=UserRole.ADMIN, status=UserStatus.ACTIVE)
        ) is True

        # Scientist + active: should match
        assert spec.is_satisfied_by(
            _make_user(role=UserRole.SCIENTIST, status=UserStatus.ACTIVE)
        ) is True

        # Admin + suspended: should NOT match
        assert spec.is_satisfied_by(
            _make_user(role=UserRole.ADMIN, status=UserStatus.SUSPENDED)
        ) is False

        # Viewer + active: should NOT match
        assert spec.is_satisfied_by(
            _make_user(role=UserRole.VIEWER, status=UserStatus.ACTIVE)
        ) is False
