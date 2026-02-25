"""SemVer — semantic versioning value object."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import total_ordering

_SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.]+))?$")


@total_ordering
@dataclass(frozen=True, slots=True)
class SemVer:
    major: int
    minor: int
    patch: int
    pre: str = ""

    @classmethod
    def parse(cls, text: str) -> SemVer:
        m = _SEMVER_RE.match(text)
        if not m:
            raise ValueError(f"Invalid semver: {text}")
        return cls(int(m[1]), int(m[2]), int(m[3]), m[4] or "")

    def __str__(self) -> str:
        base = f"{self.major}.{self.minor}.{self.patch}"
        return f"{base}-{self.pre}" if self.pre else base

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, SemVer):
            return NotImplemented
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

    def bump_patch(self) -> SemVer:
        return SemVer(self.major, self.minor, self.patch + 1)

    def bump_minor(self) -> SemVer:
        return SemVer(self.major, self.minor + 1, 0)

    def bump_major(self) -> SemVer:
        return SemVer(self.major + 1, 0, 0)
