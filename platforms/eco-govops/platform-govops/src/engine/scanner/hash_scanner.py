"""
Hash Scanner — Compute, compare, and detect drift in directory-tree
SHA-256 hash signatures used for governance integrity verification.

@GL-governed
@GL-layer: GL30-49
@GL-semantic: governance-integrity
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

EXCLUDED_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    ".idea", ".vscode", ".governance", "outputs",
}


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class HashDrift:
    """Represents a single hash mismatch between baseline and actual."""

    path: str
    expected_hash: str
    actual_hash: str
    drift_type: str  # "modified" | "added" | "removed"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HashReport:
    """Aggregated result of a hash-scanning pass."""

    scan_id: str
    timestamp: str
    directory: str
    tree_hash: str
    file_hashes: dict[str, str] = field(default_factory=dict)
    drifts: list[HashDrift] = field(default_factory=list)
    files_scanned: int = 0

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["drifts"] = [d.to_dict() for d in self.drifts]
        return data


# ---------------------------------------------------------------------------
# HashScanner
# ---------------------------------------------------------------------------

class HashScanner:
    """Compute deterministic SHA-256 hashes for directory trees and detect
    drift against a known baseline."""

    def __init__(self) -> None:
        self.log = structlog.get_logger(self.__class__.__name__)

    # -- public API ---------------------------------------------------------

    def scan_hashes(
        self, directory: Path, baseline: dict[str, str] | None = None,
    ) -> HashReport:
        """Compute hashes for every file under *directory* and compare
        against an optional *baseline* dict ``{relative_path: sha256}``."""
        directory = directory.resolve()
        ts = datetime.now(timezone.utc)
        report = HashReport(
            scan_id=f"HASH-{ts.strftime('%Y%m%dT%H%M%S')}",
            timestamp=ts.isoformat(),
            directory=str(directory),
            tree_hash="",
        )

        self.log.info("scan_hashes.start", directory=str(directory))

        file_hashes: dict[str, str] = {}
        for file_path in sorted(
            p for p in directory.rglob("*")
            if p.is_file() and not any(part in EXCLUDED_DIRS for part in p.parts)
        ):
            rel = str(file_path.relative_to(directory))
            file_hashes[rel] = self._hash_file(file_path)

        report.file_hashes = file_hashes
        report.files_scanned = len(file_hashes)
        report.tree_hash = self.compute_tree_hash(directory)

        if baseline is not None:
            report.drifts = self.diff_hashes(baseline, file_hashes)

        self.log.info(
            "scan_hashes.complete",
            files=report.files_scanned,
            drifts=len(report.drifts),
        )
        return report

    def compute_tree_hash(self, directory: Path) -> str:
        """Return a single SHA-256 representing the entire directory tree."""
        directory = directory.resolve()
        digest = hashlib.sha256()
        for file_path in sorted(
            p for p in directory.rglob("*")
            if p.is_file() and not any(part in EXCLUDED_DIRS for part in p.parts)
        ):
            rel = str(file_path.relative_to(directory))
            digest.update(rel.encode("utf-8"))
            digest.update(self._hash_file(file_path).encode("utf-8"))
        return digest.hexdigest()

    def diff_hashes(
        self,
        old: dict[str, str],
        new: dict[str, str],
    ) -> list[HashDrift]:
        """Compare two hash dictionaries and return a list of drifts."""
        drifts: list[HashDrift] = []
        all_paths = set(old) | set(new)

        for path in sorted(all_paths):
            old_hash = old.get(path, "")
            new_hash = new.get(path, "")

            if old_hash and not new_hash:
                drifts.append(HashDrift(
                    path=path,
                    expected_hash=old_hash,
                    actual_hash="",
                    drift_type="removed",
                ))
            elif not old_hash and new_hash:
                drifts.append(HashDrift(
                    path=path,
                    expected_hash="",
                    actual_hash=new_hash,
                    drift_type="added",
                ))
            elif old_hash != new_hash:
                drifts.append(HashDrift(
                    path=path,
                    expected_hash=old_hash,
                    actual_hash=new_hash,
                    drift_type="modified",
                ))

        return drifts

    # -- private helpers ----------------------------------------------------

    @staticmethod
    def _hash_file(path: Path) -> str:
        """SHA-256 of a single file."""
        digest = hashlib.sha256()
        try:
            with path.open("rb") as fh:
                for chunk in iter(lambda: fh.read(8192), b""):
                    digest.update(chunk)
        except OSError:
            return ""
        return digest.hexdigest()
