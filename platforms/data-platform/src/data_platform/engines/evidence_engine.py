"""EvidenceEngine — ingest, validate, and chain evidence records.

Provides an in-memory evidence store with SHA-256 hash chaining
for building auditable evidence trails.
"""

from __future__ import annotations

from typing import Any

from data_platform.domain.entities import EvidenceRecord
from data_platform.domain.events import EvidenceIngested
from data_platform.domain.exceptions import EvidenceChainError
from data_platform.domain.value_objects import EvidenceType


class EvidenceEngine:
    """Manages evidence record ingestion, hash chaining, and querying."""

    def __init__(self) -> None:
        self._store: dict[str, EvidenceRecord] = {}
        self._chain_order: list[str] = []  # insertion order for chain verification
        self._events: list[EvidenceIngested] = []

    def ingest(self, record: EvidenceRecord) -> EvidenceRecord:
        """Ingest an evidence record: compute its hash, chain to parent, and store.

        If the record has a parent_id, the parent must already exist in the store.
        The hash is computed from the record's type, parent_id, and payload.
        """
        # Validate parent exists if referenced
        if record.parent_id is not None:
            if record.parent_id not in self._store:
                raise EvidenceChainError(
                    f"Parent record '{record.parent_id}' not found",
                    record_id=record.id,
                )

        # Compute and set hash
        record.compute_hash()

        # Store
        self._store[record.id] = record
        self._chain_order.append(record.id)

        # Emit domain event
        self._events.append(
            EvidenceIngested(
                evidence_id=record.id,
                evidence_type=record.type.value,
                hash=record.hash,
                parent_id=record.parent_id,
            )
        )

        return record

    def get(self, record_id: str) -> EvidenceRecord | None:
        """Retrieve a single record by id."""
        return self._store.get(record_id)

    def query(self, filters: dict[str, Any] | None = None) -> list[EvidenceRecord]:
        """Query records with optional filters.

        Supported filters:
            - type: EvidenceType or str — filter by evidence type
            - parent_id: str — filter by parent record id
            - has_parent: bool — filter records with/without parents
        """
        results = list(self._store.values())

        if not filters:
            return results

        if "type" in filters:
            target_type = filters["type"]
            if isinstance(target_type, str):
                target_type = EvidenceType(target_type)
            results = [r for r in results if r.type == target_type]

        if "parent_id" in filters:
            pid = filters["parent_id"]
            results = [r for r in results if r.parent_id == pid]

        if "has_parent" in filters:
            has_parent = filters["has_parent"]
            if has_parent:
                results = [r for r in results if r.parent_id is not None]
            else:
                results = [r for r in results if r.parent_id is None]

        return results

    def verify_chain(self) -> bool:
        """Validate the entire hash chain integrity.

        Checks that:
        1. Every record's hash matches a fresh computation.
        2. Every record with a parent_id references an existing record.

        Raises EvidenceChainError on the first violation found.
        Returns True if the chain is fully valid.
        """
        for record_id in self._chain_order:
            record = self._store.get(record_id)
            if record is None:
                raise EvidenceChainError(
                    f"Record '{record_id}' missing from store",
                    record_id=record_id,
                )

            # Verify hash integrity
            if not record.verify_hash():
                raise EvidenceChainError(
                    f"Hash mismatch for record '{record_id}'",
                    record_id=record_id,
                )

            # Verify parent reference
            if record.parent_id is not None:
                if record.parent_id not in self._store:
                    raise EvidenceChainError(
                        f"Broken chain: parent '{record.parent_id}' not found "
                        f"for record '{record_id}'",
                        record_id=record_id,
                    )

        return True

    @property
    def record_count(self) -> int:
        return len(self._store)

    @property
    def events(self) -> list[EvidenceIngested]:
        return list(self._events)
