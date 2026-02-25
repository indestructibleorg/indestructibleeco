"""Unit tests for domain specifications."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from src.domain.specifications import (
    ActiveUserSpecification,
    UserByRoleSpecification,
    UserByEmailDomainSpecification,
)


class TestActiveUserSpecification:
    def test_active_user_matches(self):
        spec = ActiveUserSpecification()
        user = MagicMock()
        user.status.value = "active"
        assert spec.is_satisfied_by(user)

    def test_suspended_user_does_not_match(self):
        spec = ActiveUserSpecification()
        user = MagicMock()
        user.status.value = "suspended"
        assert not spec.is_satisfied_by(user)


class TestUserByRoleSpecification:
    def test_matching_role(self):
        spec = UserByRoleSpecification("admin")
        user = MagicMock()
        user.role.value = "admin"
        assert spec.is_satisfied_by(user)

    def test_non_matching_role(self):
        spec = UserByRoleSpecification("admin")
        user = MagicMock()
        user.role.value = "viewer"
        assert not spec.is_satisfied_by(user)


class TestUserByEmailDomainSpecification:
    def test_matching_domain(self):
        spec = UserByEmailDomainSpecification("company.com")
        user = MagicMock()
        user.email.value = "john@company.com"
        assert spec.is_satisfied_by(user)

    def test_non_matching_domain(self):
        spec = UserByEmailDomainSpecification("company.com")
        user = MagicMock()
        user.email.value = "john@other.com"
        assert not spec.is_satisfied_by(user)


class TestCompositeSpecifications:
    def test_and_specification(self):
        active = ActiveUserSpecification()
        admin = UserByRoleSpecification("admin")
        combined = active.and_(admin)

        user = MagicMock()
        user.status.value = "active"
        user.role.value = "admin"
        assert combined.is_satisfied_by(user)

        user2 = MagicMock()
        user2.status.value = "suspended"
        user2.role.value = "admin"
        assert not combined.is_satisfied_by(user2)

    def test_or_specification(self):
        admin = UserByRoleSpecification("admin")
        operator = UserByRoleSpecification("operator")
        combined = admin.or_(operator)

        user = MagicMock()
        user.role.value = "operator"
        assert combined.is_satisfied_by(user)

        user2 = MagicMock()
        user2.role.value = "viewer"
        assert not combined.is_satisfied_by(user2)

    def test_not_specification(self):
        active = ActiveUserSpecification()
        inactive = active.not_()

        user = MagicMock()
        user.status.value = "suspended"
        assert inactive.is_satisfied_by(user)