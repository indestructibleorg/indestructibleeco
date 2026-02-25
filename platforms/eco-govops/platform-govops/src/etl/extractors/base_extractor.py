from __future__ import annotations

"""
Base Extractor Module for GovOps ETL Pipeline.

Provides the abstract base class for all data extractors and the Record
dataclass used as the canonical unit of data throughout the pipeline.
"""

import hashlib
import json
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class Record:
    """Immutable unit of extracted data flowing through the pipeline."""

    data: dict[str, Any]
    source: str
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def fingerprint(self) -> str:
        """Return a deterministic SHA-256 fingerprint of the record data."""
        payload = json.dumps(self.data, sort_keys=True, default=str)
        return hashlib.sha256(payload.encode()).hexdigest()

    def with_data(self, data: dict[str, Any]) -> Record:
        """Return a new Record with replaced data, preserving other fields."""
        return Record(
            data=data,
            source=self.source,
            timestamp=self.timestamp,
            metadata=self.metadata,
        )

    def with_metadata(self, extra: dict[str, Any]) -> Record:
        """Return a new Record with merged metadata."""
        merged = {**self.metadata, **extra}
        return Record(
            data=self.data,
            source=self.source,
            timestamp=self.timestamp,
            metadata=merged,
        )


class BaseExtractor(ABC):
    """Abstract base class for all data extractors.

    Subclasses must implement ``extract``, ``validate_source``, and
    ``health_check``.  The ``extract`` method is an async generator that
    yields ``Record`` instances one at a time to support back-pressure-
    friendly streaming.
    """

    def __init__(self, name: str = "base-extractor") -> None:
        self.name = name
        self._log = logger.bind(extractor=name)
        self._records_extracted: int = 0
        self._errors: int = 0
        self._last_run: datetime | None = None

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    async def extract(self, source_config: dict[str, Any]) -> AsyncIterator[Record]:
        """Yield records from the configured source.

        Parameters
        ----------
        source_config:
            Source-specific configuration (URLs, credentials, paths, etc.).

        Yields
        ------
        Record
            One record per extracted datum.
        """
        yield  # pragma: no cover – make this a valid async generator
        ...

    @abstractmethod
    def validate_source(self, source_config: dict[str, Any]) -> bool:
        """Return ``True`` when *source_config* contains all required keys."""
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """Return ``True`` when the extractor's backing service is reachable."""
        ...

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    def _make_record(
        self,
        data: dict[str, Any],
        source: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> Record:
        """Create a timestamped ``Record`` and bump the internal counter."""
        self._records_extracted += 1
        return Record(
            data=data,
            source=source,
            timestamp=datetime.now(timezone.utc),
            metadata=metadata or {},
        )

    def reset_counters(self) -> None:
        """Reset extraction metrics for a fresh run."""
        self._records_extracted = 0
        self._errors = 0
        self._last_run = datetime.now(timezone.utc)

    @property
    def metrics(self) -> dict[str, Any]:
        """Return a snapshot of the extractor's counters."""
        return {
            "extractor": self.name,
            "records_extracted": self._records_extracted,
            "errors": self._errors,
            "last_run": self._last_run.isoformat() if self._last_run else None,
        }
