"""Email value object with validation."""
from __future__ import annotations

import re

from src.domain.entities.base import ValueObject


class Email(ValueObject):
    """Validated email address."""

    value: str

    @classmethod
    def create(cls, value: str) -> Email:
        normalized = value.strip().lower()
        if not cls._is_valid(normalized):
            from src.domain.exceptions import InvalidEmailError
            raise InvalidEmailError(normalized)
        return cls(value=normalized)

    @staticmethod
    def _is_valid(email: str) -> bool:
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email)) and len(email) <= 254

    @property
    def domain(self) -> str:
        return self.value.split("@")[1]

    @property
    def local_part(self) -> str:
        return self.value.split("@")[0]

    def __str__(self) -> str:
        return self.value