"""Password value object — stores only hashed representation."""
from __future__ import annotations

from src.domain.entities.base import ValueObject


class HashedPassword(ValueObject):
    """Bcrypt-hashed password. Never stores plaintext."""

    value: str

    @classmethod
    def from_plain(cls, plain: str) -> HashedPassword:
        cls._validate_strength(plain)
        import bcrypt
        pwd_bytes = plain.encode("utf-8")
        return cls(value=bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode("utf-8"))

    @classmethod
    def from_hash(cls, hashed: str) -> HashedPassword:
        return cls(value=hashed)

    def verify(self, plain: str) -> bool:
        import bcrypt
        try:
            return bcrypt.checkpw(plain.encode("utf-8"), self.value.encode("utf-8"))
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _validate_strength(plain: str) -> None:
        errors: list[str] = []
        if len(plain) < 8:
            errors.append("minimum 8 characters")
        if len(plain.encode("utf-8")) > 72:
            errors.append("maximum 72 bytes when UTF-8 encoded (bcrypt limit)")
        if not any(c.isupper() for c in plain):
            errors.append("at least one uppercase letter")
        if not any(c.islower() for c in plain):
            errors.append("at least one lowercase letter")
        if not any(c.isdigit() for c in plain):
            errors.append("at least one digit")
        if errors:
            from src.domain.exceptions import WeakPasswordError
            raise WeakPasswordError(errors)

    def __str__(self) -> str:
        return "***HASHED***"

    def __repr__(self) -> str:
        return "HashedPassword(***)"