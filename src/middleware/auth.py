"""Authentication Middleware — API Key lifecycle, JWT, rate limiting.

URI: indestructibleeco://src/middleware/auth

Contracts defined by: tests/unit/test_auth.py
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid1

from ..schemas.auth import APIKeyCreate, APIKeyInfo, APIKeyResult, UserRole


class AuthMiddleware:
    """Manages API keys and JWT tokens for the platform.

    On instantiation, creates a default admin key.
    """

    _JWT_ALG = "HS256"
    _JWT_EXPIRY = 86400  # 24 hours

    def __init__(self, jwt_secret: str = "eco-jwt-secret-change-in-production") -> None:
        self._keys: Dict[str, _KeyRecord] = {}
        self._jwt_secret = jwt_secret
        self._create_default_key()

    # ── API Key Management ──────────────────────────────────────────

    def create_api_key(self, req: APIKeyCreate) -> APIKeyResult:
        """Create a new API key. Returns the raw key exactly once."""
        raw_key = f"sk-eco-{secrets.token_hex(24)}"
        key_id = str(uuid1())
        hashed = self._hash_key(raw_key)

        info = APIKeyInfo(
            key_id=key_id,
            name=req.name,
            role=req.role,
            is_active=True,
            rate_limit_per_minute=req.rate_limit_per_minute,
            total_requests=0,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        self._keys[hashed] = _KeyRecord(info=info, raw_prefix=raw_key[:16])

        return APIKeyResult(key=raw_key, info=info)

    def validate_api_key(self, key: str) -> Optional[Dict[str, Any]]:
        """Validate an API key. Returns key metadata or None if invalid/revoked."""
        hashed = self._hash_key(key)
        record = self._keys.get(hashed)
        if record is None or not record.info.is_active:
            return None

        record.info.total_requests += 1

        return {
            "key_id": record.info.key_id,
            "name": record.info.name,
            "role": record.info.role.value,
            "is_active": record.info.is_active,
            "rate_limit_per_minute": record.info.rate_limit_per_minute,
            "total_requests": record.info.total_requests,
        }

    def revoke_api_key(self, key_id: str) -> bool:
        """Revoke an API key by its ID. Returns True if found and revoked."""
        for record in self._keys.values():
            if record.info.key_id == key_id:
                record.info.is_active = False
                return True
        return False

    def list_api_keys(self) -> List[APIKeyInfo]:
        """List all API keys (active and revoked)."""
        return [record.info for record in self._keys.values()]

    # ── JWT Token Management ────────────────────────────────────────

    def create_jwt_token(self, user_id: str, role: str) -> str:
        """Create a signed JWT token."""
        now = int(time.time())
        payload = {
            "sub": user_id,
            "role": role,
            "iat": now,
            "exp": now + self._JWT_EXPIRY,
            "iss": "indestructibleeco",
        }
        return self._jwt_encode(payload)

    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token. Returns payload or None."""
        try:
            payload = self._jwt_decode(token)
            if payload.get("exp", 0) < int(time.time()):
                return None
            return payload
        except Exception:
            return None

    # ── Internal ────────────────────────────────────────────────────

    def _create_default_key(self) -> None:
        """Create the default admin key on startup."""
        self.create_api_key(APIKeyCreate(
            name="Default Admin Key",
            role=UserRole.ADMIN,
            rate_limit_per_minute=1000,
        ))

    @staticmethod
    def _hash_key(key: str) -> str:
        return hashlib.sha256(key.encode()).hexdigest()

    def _jwt_encode(self, payload: Dict[str, Any]) -> str:
        """Minimal HMAC-SHA256 JWT encoder (no external dependency)."""
        import base64

        def b64url(data: bytes) -> str:
            return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

        header = b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
        body = b64url(json.dumps(payload).encode())
        signing_input = f"{header}.{body}"
        signature = b64url(
            hmac.new(self._jwt_secret.encode(), signing_input.encode(), hashlib.sha256).digest()
        )
        return f"{signing_input}.{signature}"

    def _jwt_decode(self, token: str) -> Dict[str, Any]:
        """Minimal HMAC-SHA256 JWT decoder."""
        import base64

        def b64url(data: bytes) -> str:
            return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid JWT format")

        signing_input = f"{parts[0]}.{parts[1]}"
        expected_sig = b64url(
            hmac.new(self._jwt_secret.encode(), signing_input.encode(), hashlib.sha256).digest()
        )

        if not hmac.compare_digest(expected_sig, parts[2]):
            raise ValueError("Invalid JWT signature")

        # Decode payload
        padded = parts[1] + "=" * (4 - len(parts[1]) % 4)
        payload_bytes = base64.urlsafe_b64decode(padded)
        return json.loads(payload_bytes)


class _KeyRecord:
    """Internal storage for an API key."""

    __slots__ = ("info", "raw_prefix")

    def __init__(self, info: APIKeyInfo, raw_prefix: str) -> None:
        self.info = info
        self.raw_prefix = raw_prefix