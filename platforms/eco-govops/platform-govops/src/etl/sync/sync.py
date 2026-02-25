"""Change tracking and synchronisation for the GovOps ETL pipeline.

Provides incremental sync capabilities by tracking source data fingerprints
and only processing changed records on subsequent pipeline runs.

@GL-governed
@GL-layer: GL30-49
@GL-semantic: etl-sync
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

import structlog

from etl.extractors.base_extractor import Record

logger = structlog.get_logger(__name__)


class ChangeTracker:
    """Tracks record fingerprints to detect new or changed data.

    Stores a mapping of ``(source, key) → fingerprint`` so that subsequent
    pipeline runs can skip records that haven't changed.
    """

    def __init__(self) -> None:
        self._fingerprints: dict[str, str] = {}
        self._log = logger.bind(component="change-tracker")
        self._changes_detected: int = 0
        self._unchanged: int = 0

    def is_changed(self, record: Record, key_field: str = "id") -> bool:
        """Return ``True`` if the record is new or has changed since last seen."""
        key_value = record.data.get(key_field, record.fingerprint)
        cache_key = f"{record.source}:{key_value}"
        current_fp = record.fingerprint

        previous_fp = self._fingerprints.get(cache_key)
        self._fingerprints[cache_key] = current_fp

        if previous_fp is None or previous_fp != current_fp:
            self._changes_detected += 1
            return True

        self._unchanged += 1
        return False

    def reset(self) -> None:
        """Clear all tracked fingerprints."""
        self._fingerprints.clear()
        self._changes_detected = 0
        self._unchanged = 0

    @property
    def metrics(self) -> dict[str, Any]:
        return {
            "tracked_records": len(self._fingerprints),
            "changes_detected": self._changes_detected,
            "unchanged": self._unchanged,
        }


class SyncManager:
    """Manages incremental synchronisation across pipeline runs.

    Wraps a :class:`ChangeTracker` and provides higher-level methods for
    filtering record batches to only include changed data.
    """

    def __init__(self, key_field: str = "id") -> None:
        self.key_field = key_field
        self.tracker = ChangeTracker()
        self._last_sync: datetime | None = None
        self._log = logger.bind(component="sync-manager")

    def filter_changed(self, records: list[Record]) -> list[Record]:
        """Return only records that are new or have changed."""
        changed = [r for r in records if self.tracker.is_changed(r, self.key_field)]
        self._last_sync = datetime.now(timezone.utc)
        self._log.info(
            "sync_filter_applied",
            total=len(records),
            changed=len(changed),
            skipped=len(records) - len(changed),
        )
        return changed

    @property
    def metrics(self) -> dict[str, Any]:
        return {
            **self.tracker.metrics,
            "last_sync": self._last_sync.isoformat() if self._last_sync else None,
        }
