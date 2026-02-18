"""Unit tests for authentication middleware."""
import pytest
import time

from src.middleware.auth import AuthMiddleware
from src.schemas.auth import APIKeyCreate, UserRole


@pytest.fixture
def auth():
    return AuthMiddleware()


class TestAuthMiddleware:
    def test_default_key_created(self, auth):
        keys = auth.list_api_keys()
        assert len(keys) >= 1
        assert any(k.name == "Default Admin Key" for k in keys)

    def test_create_api_key(self, auth):
        result = auth.create_api_key(APIKeyCreate(
            name="test-key",
            role=UserRole.DEVELOPER,
            rate_limit_per_minute=100,
        ))
        assert result.key.startswith("sk-eco-")
        assert result.info.name == "test-key"
        assert result.info.role == UserRole.DEVELOPER
        assert result.info.is_active is True

    def test_validate_api_key(self, auth):
        result = auth.create_api_key(APIKeyCreate(name="validate-test"))
        key_data = auth.validate_api_key(result.key)
        assert key_data is not None
        assert key_data["name"] == "validate-test"

    def test_validate_invalid_key(self, auth):
        key_data = auth.validate_api_key("sk-eco-invalid-key-12345")
        assert key_data is None

    def test_revoke_api_key(self, auth):
        result = auth.create_api_key(APIKeyCreate(name="revoke-test"))
        key_id = result.info.key_id

        revoked = auth.revoke_api_key(key_id)
        assert revoked is True

        key_data = auth.validate_api_key(result.key)
        assert key_data is None

    def test_revoke_nonexistent_key(self, auth):
        revoked = auth.revoke_api_key("nonexistent-id")
        assert revoked is False

    def test_jwt_token_roundtrip(self, auth):
        token = auth.create_jwt_token("user-123", "admin")
        assert isinstance(token, str)

        payload = auth.verify_jwt_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["role"] == "admin"

    def test_jwt_invalid_token(self, auth):
        payload = auth.verify_jwt_token("invalid.jwt.token")
        assert payload is None

    def test_list_api_keys(self, auth):
        auth.create_api_key(APIKeyCreate(name="list-test-1"))
        auth.create_api_key(APIKeyCreate(name="list-test-2"))
        keys = auth.list_api_keys()
        names = [k.name for k in keys]
        assert "list-test-1" in names
        assert "list-test-2" in names

    def test_key_request_counting(self, auth):
        result = auth.create_api_key(APIKeyCreate(name="count-test"))
        for _ in range(5):
            auth.validate_api_key(result.key)
        key_data = auth.validate_api_key(result.key)
        assert key_data["total_requests"] == 6  # 5 + 1 from this call