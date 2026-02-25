"""PlatformId — strongly-typed identifier for every platform in the ecosystem."""

from __future__ import annotations

import re
from dataclasses import dataclass

_SLUG_RE = re.compile(r"^[a-z][a-z0-9-]{1,62}[a-z0-9]$")


@dataclass(frozen=True, slots=True)
class PlatformId:
    """Immutable, validated platform identifier.

    Format: lowercase alphanumeric slug with hyphens, 3-64 chars.
    Examples: ``automation-platform``, ``governance-platform``
    """

    value: str

    def __post_init__(self) -> None:
        if not _SLUG_RE.match(self.value):
            raise ValueError(
                f"Invalid PlatformId '{self.value}': must be lowercase slug, 3-64 chars"
            )

    def __str__(self) -> str:
        return self.value

    @property
    def package_name(self) -> str:
        """Python package name (hyphens → underscores)."""
        return self.value.replace("-", "_")
