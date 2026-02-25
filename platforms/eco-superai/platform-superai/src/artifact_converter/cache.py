"""Content-hash based incremental conversion cache.

Prevents redundant re-conversion when source content has not changed.  The
cache stores a mapping of ``(source_hash, output_format, template)`` to the
previously generated output, persisted as JSON in a configurable directory.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import structlog

from .config import CacheSettings

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class CacheKey:
    """Immutable compound cache key."""

    content_hash: str
    output_format: str
    template: str | None = None

    def to_filename(self) -> str:
        """Deterministic filename derived from the key components."""
        parts = [self.content_hash, self.output_format]
        if self.template:
            parts.append(
                hashlib.sha256(self.template.encode()).hexdigest()[:12]
            )
        return "_".join(parts) + ".json"


@dataclass
class CacheEntry:
    """A single cached conversion result."""

    key: CacheKey
    output_text: str
    created_at: float = field(default_factory=time.time)
    source_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "content_hash": self.key.content_hash,
            "output_format": self.key.output_format,
            "template": self.key.template,
            "output_text": self.output_text,
            "created_at": self.created_at,
            "source_path": self.source_path,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CacheEntry":
        key = CacheKey(
            content_hash=data["content_hash"],
            output_format=data["output_format"],
            template=data.get("template"),
        )
        return cls(
            key=key,
            output_text=data["output_text"],
            created_at=data.get("created_at", 0.0),
            source_path=data.get("source_path"),
        )


class ConversionCache:
    """Disk-backed, hash-addressed conversion cache.

    The cache directory contains one JSON file per entry, named after the
    deterministic :pymethod:`CacheKey.to_filename`.  An in-memory index
    accelerates lookups so only cache misses touch the filesystem.
    """

    def __init__(self, settings: CacheSettings | None = None) -> None:
        self._settings = settings or CacheSettings()
        self._dir = self._settings.directory
        self._algorithm = self._settings.hash_algorithm
        self._max_entries = self._settings.max_entries
        self._index: dict[str, CacheEntry] = {}

        if self._settings.enabled:
            self._dir.mkdir(parents=True, exist_ok=True)
            self._load_index()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def enabled(self) -> bool:
        return self._settings.enabled

    def content_hash(self, content: str | bytes) -> str:
        """Compute a hex-digest hash of *content*."""
        raw = content.encode("utf-8") if isinstance(content, str) else content
        return hashlib.new(self._algorithm, raw).hexdigest()

    def get(self, key: CacheKey) -> CacheEntry | None:
        """Return the cached entry for *key*, or ``None`` on a miss."""
        if not self._settings.enabled:
            return None

        filename = key.to_filename()
        entry = self._index.get(filename)
        if entry is not None:
            logger.debug("cache_hit", key=filename)
            return entry

        # Fallback: check disk in case index is stale
        path = self._dir / filename
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                entry = CacheEntry.from_dict(data)
                self._index[filename] = entry
                logger.debug("cache_hit_disk", key=filename)
                return entry
            except (json.JSONDecodeError, KeyError):
                logger.warning("cache_corrupt_entry", path=str(path))
                path.unlink(missing_ok=True)

        logger.debug("cache_miss", key=filename)
        return None

    def put(self, entry: CacheEntry) -> None:
        """Store *entry* in the cache, evicting old entries if necessary."""
        if not self._settings.enabled:
            return

        filename = entry.key.to_filename()
        self._index[filename] = entry

        path = self._dir / filename
        path.write_text(
            json.dumps(entry.to_dict(), ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        logger.debug("cache_put", key=filename)

        self._evict_if_needed()

    def invalidate(self, key: CacheKey) -> bool:
        """Remove *key* from the cache.  Returns ``True`` if it existed."""
        filename = key.to_filename()
        existed = filename in self._index
        self._index.pop(filename, None)
        path = self._dir / filename
        path.unlink(missing_ok=True)
        if existed:
            logger.debug("cache_invalidated", key=filename)
        return existed

    def clear(self) -> int:
        """Remove all cache entries.  Returns the number removed."""
        count = len(self._index)
        self._index.clear()
        if self._dir.exists():
            for child in self._dir.iterdir():
                if child.suffix == ".json":
                    child.unlink(missing_ok=True)
        logger.info("cache_cleared", removed=count)
        return count

    def stats(self) -> dict[str, Any]:
        """Return diagnostic information about the cache."""
        disk_count = (
            sum(1 for p in self._dir.iterdir() if p.suffix == ".json")
            if self._dir.exists()
            else 0
        )
        return {
            "enabled": self._settings.enabled,
            "directory": str(self._dir),
            "index_size": len(self._index),
            "disk_entries": disk_count,
            "max_entries": self._max_entries,
            "algorithm": self._algorithm,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_index(self) -> None:
        """Bootstrap the in-memory index from disk."""
        if not self._dir.exists():
            return
        loaded = 0
        for path in sorted(self._dir.iterdir()):
            if path.suffix != ".json":
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                entry = CacheEntry.from_dict(data)
                self._index[path.name] = entry
                loaded += 1
            except (json.JSONDecodeError, KeyError):
                logger.warning("cache_corrupt_entry_skipped", path=str(path))
        logger.debug("cache_index_loaded", entries=loaded)

    def _evict_if_needed(self) -> None:
        """Evict oldest entries when the cache exceeds ``max_entries``."""
        if len(self._index) <= self._max_entries:
            return

        sorted_keys = sorted(
            self._index,
            key=lambda k: self._index[k].created_at,
        )
        evict_count = len(self._index) - self._max_entries
        for filename in sorted_keys[:evict_count]:
            self._index.pop(filename, None)
            (self._dir / filename).unlink(missing_ok=True)
        logger.info("cache_evicted", count=evict_count)
