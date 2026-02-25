#!/usr/bin/env python3
"""
Evidence Pipeline Engine v1.0
Ingestion, validation, hash-chain binding, and lifecycle state machine.

This module implements the complete evidence pipeline with cryptographic
hash-chain binding, schema validation, and a strict state machine governing
the lifecycle of every evidence record from ingestion through archival.

Governance Stage: S5-VERIFIED
Status: ENFORCED
"""

import hashlib
import json
import logging
import sys
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# Configure logging with CRITICAL-only default
logging.basicConfig(
    level=logging.CRITICAL,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================
# ENUMS
# ============================================

class EvidenceState(Enum):
    """Lifecycle states for an evidence record."""
    INGESTED = "ingested"
    VALIDATING = "validating"
    VERIFIED = "verified"
    SEALED = "sealed"
    ARCHIVED = "archived"
    REJECTED = "rejected"


class EvidencePipelineStage(Enum):
    """Ordered stages in the evidence pipeline."""
    INGEST = 1
    VALIDATE_SCHEMA = 2
    COMPUTE_HASH = 3
    BIND_CHAIN = 4
    SEAL = 5
    ARCHIVE = 6


# ============================================
# DATA STRUCTURES
# ============================================

@dataclass
class EvidenceTransition:
    """Records a state transition for an evidence record."""
    from_state: EvidenceState
    to_state: EvidenceState
    triggered_by: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class EvidenceRecord:
    """Immutable evidence record with cryptographic binding."""
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    state: EvidenceState = EvidenceState.INGESTED
    hash_value: str = ""
    chain_parent_hash: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    sealed_at: Optional[str] = None
    transitions: List[EvidenceTransition] = field(default_factory=list)

    def to_bytes(self) -> bytes:
        """Convert core fields to bytes for hashing."""
        data = {
            "record_id": self.record_id,
            "payload": self.payload,
        }
        return json.dumps(data, sort_keys=True).encode("utf-8")

    def transition_to(self, new_state: EvidenceState, triggered_by: str) -> None:
        """Execute a state transition and record it."""
        transition = EvidenceTransition(
            from_state=self.state,
            to_state=new_state,
            triggered_by=triggered_by,
        )
        self.transitions.append(transition)
        self.state = new_state


# ============================================
# VALID STATE TRANSITIONS
# ============================================

ALLOWED_TRANSITIONS: Dict[EvidenceState, List[EvidenceState]] = {
    EvidenceState.INGESTED: [EvidenceState.VALIDATING, EvidenceState.REJECTED],
    EvidenceState.VALIDATING: [EvidenceState.VERIFIED, EvidenceState.REJECTED],
    EvidenceState.VERIFIED: [EvidenceState.SEALED, EvidenceState.REJECTED],
    EvidenceState.SEALED: [EvidenceState.ARCHIVED],
    EvidenceState.ARCHIVED: [],
    EvidenceState.REJECTED: [],
}

# Required fields that every evidence payload must contain
REQUIRED_PAYLOAD_FIELDS = {"type", "content", "timestamp"}


# ============================================
# EVIDENCE PIPELINE ENGINE
# ============================================

class EvidencePipelineEngine:
    """Evidence Pipeline Engine -- ingestion, validation, hash-chain binding, lifecycle."""

    def __init__(self) -> None:
        """Initialize the evidence pipeline engine."""
        self.pipeline_stages: List[EvidencePipelineStage] = list(EvidencePipelineStage)
        self.processed_records: List[EvidenceRecord] = []
        self.chain_head: Optional[str] = None
        self._rejected_records: List[EvidenceRecord] = []

        # Initialize genesis chain head
        genesis_data = {"genesis": True, "timestamp": datetime.now(timezone.utc).isoformat()}
        genesis_bytes = json.dumps(genesis_data, sort_keys=True).encode("utf-8")
        self.chain_head = hashlib.sha3_512(genesis_bytes).hexdigest()
        logger.info("EvidencePipelineEngine initialized with genesis hash: %s...", self.chain_head[:16])

    # ------------------------------------------
    # PUBLIC API
    # ------------------------------------------

    def ingest(self, source: str, payload: Dict[str, Any]) -> EvidenceRecord:
        """Ingest a new evidence record and run it through the full pipeline.

        Args:
            source: Origin identifier for this evidence (e.g. system name).
            payload: Evidence data dictionary. Must contain required fields.

        Returns:
            The fully processed EvidenceRecord (state will be SEALED or REJECTED).
        """
        record = EvidenceRecord(source=source, payload=payload)
        logger.info("Ingesting record %s from source '%s'", record.record_id, source)

        # Stage 1 -- INGEST (already done by construction)

        # Stage 2 -- VALIDATE_SCHEMA
        record.transition_to(EvidenceState.VALIDATING, triggered_by="pipeline:validate_schema")
        if not self._validate_schema(record):
            record.transition_to(EvidenceState.REJECTED, triggered_by="pipeline:validate_schema:failed")
            self._rejected_records.append(record)
            logger.warning("Record %s rejected -- schema validation failed", record.record_id)
            return record

        # Stage 3 -- COMPUTE_HASH
        record.hash_value = self._compute_hash(record)
        record.transition_to(EvidenceState.VERIFIED, triggered_by="pipeline:compute_hash")

        # Stage 4 -- BIND_CHAIN
        self._bind_to_chain(record)

        # Stage 5 -- SEAL
        self._seal_record(record)

        # Record processed
        self.processed_records.append(record)
        logger.info("Record %s sealed and added to chain", record.record_id)
        return record

    def verify_chain_integrity(self) -> Tuple[bool, List[str]]:
        """Walk the chain and verify every record's hash and parent linkage.

        Returns:
            Tuple of (is_valid, list_of_error_strings).
        """
        errors: List[str] = []

        if not self.processed_records:
            return True, []

        for idx, record in enumerate(self.processed_records):
            # Re-compute hash and compare
            expected_hash = self._compute_hash(record)
            if record.hash_value != expected_hash:
                errors.append(
                    f"Record {record.record_id} at position {idx}: "
                    f"hash mismatch (stored={record.hash_value[:16]}..., "
                    f"computed={expected_hash[:16]}...)"
                )

            # Verify chain linkage (first record links to genesis)
            if idx == 0:
                # First record's parent should exist (genesis)
                if record.chain_parent_hash is None:
                    errors.append(
                        f"Record {record.record_id} at position 0: missing chain_parent_hash"
                    )
            else:
                expected_parent = self.processed_records[idx - 1].hash_value
                if record.chain_parent_hash != expected_parent:
                    errors.append(
                        f"Record {record.record_id} at position {idx}: "
                        f"chain_parent_hash mismatch "
                        f"(expected={expected_parent[:16]}..., "
                        f"actual={record.chain_parent_hash[:16] if record.chain_parent_hash else 'None'}...)"
                    )

        is_valid = len(errors) == 0
        return is_valid, errors

    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Return aggregate statistics about the pipeline.

        Returns:
            Dictionary with total records, counts by state, chain length, etc.
        """
        all_records = self.processed_records + self._rejected_records
        by_state: Dict[str, int] = {}
        for state in EvidenceState:
            count = sum(1 for r in all_records if r.state == state)
            if count > 0:
                by_state[state.value] = count

        return {
            "total_records": len(all_records),
            "processed_records": len(self.processed_records),
            "rejected_records": len(self._rejected_records),
            "by_state": by_state,
            "chain_length": len(self.processed_records),
            "chain_head": self.chain_head[:32] + "..." if self.chain_head else None,
            "pipeline_stages": [stage.name for stage in self.pipeline_stages],
        }

    def get_record(self, record_id: str) -> Optional[EvidenceRecord]:
        """Retrieve a record by its ID."""
        for record in self.processed_records + self._rejected_records:
            if record.record_id == record_id:
                return record
        return None

    def get_records_by_state(self, state: EvidenceState) -> List[EvidenceRecord]:
        """Return all records currently in the given state."""
        all_records = self.processed_records + self._rejected_records
        return [r for r in all_records if r.state == state]

    # ------------------------------------------
    # INTERNAL PIPELINE STAGES
    # ------------------------------------------

    def _validate_schema(self, record: EvidenceRecord) -> bool:
        """Validate that the record payload contains all required fields.

        Args:
            record: The evidence record to validate.

        Returns:
            True if schema is valid, False otherwise.
        """
        if not isinstance(record.payload, dict):
            logger.warning("Record %s: payload is not a dict", record.record_id)
            return False

        missing = REQUIRED_PAYLOAD_FIELDS - set(record.payload.keys())
        if missing:
            logger.warning(
                "Record %s: missing required fields: %s",
                record.record_id,
                ", ".join(sorted(missing)),
            )
            return False

        # Verify no empty values in required fields
        for field_name in REQUIRED_PAYLOAD_FIELDS:
            value = record.payload.get(field_name)
            if value is None or (isinstance(value, str) and not value.strip()):
                logger.warning(
                    "Record %s: required field '%s' is empty",
                    record.record_id,
                    field_name,
                )
                return False

        return True

    def _compute_hash(self, record: EvidenceRecord) -> str:
        """Compute SHA3-512 hash of record_id + json(payload).

        Args:
            record: The evidence record to hash.

        Returns:
            Hex-encoded SHA3-512 hash string.
        """
        hash_input = record.record_id + json.dumps(record.payload, sort_keys=True)
        return hashlib.sha3_512(hash_input.encode("utf-8")).hexdigest()

    def _bind_to_chain(self, record: EvidenceRecord) -> None:
        """Bind the record to the hash chain by setting parent and updating head.

        Args:
            record: The evidence record to bind.
        """
        record.chain_parent_hash = self.chain_head
        self.chain_head = record.hash_value
        logger.info(
            "Record %s bound to chain (parent=%s..., new_head=%s...)",
            record.record_id,
            record.chain_parent_hash[:16] if record.chain_parent_hash else "None",
            self.chain_head[:16],
        )

    def _seal_record(self, record: EvidenceRecord) -> None:
        """Transition the record to SEALED state and set sealed_at timestamp.

        Args:
            record: The evidence record to seal.
        """
        record.transition_to(EvidenceState.SEALED, triggered_by="pipeline:seal")
        record.sealed_at = datetime.now(timezone.utc).isoformat()

    def _archive_record(self, record: EvidenceRecord) -> bool:
        """Transition a sealed record to ARCHIVED state.

        Args:
            record: The evidence record to archive.

        Returns:
            True if successfully archived, False otherwise.
        """
        if record.state != EvidenceState.SEALED:
            logger.warning(
                "Cannot archive record %s: current state is %s, expected SEALED",
                record.record_id,
                record.state.value,
            )
            return False

        record.transition_to(EvidenceState.ARCHIVED, triggered_by="pipeline:archive")
        return True


# ============================================
# CLI INTERFACE
# ============================================

def main() -> None:
    """Demonstrate evidence pipeline usage."""
    print("=" * 60)
    print("Evidence Pipeline Engine -- Demo")
    print("=" * 60)

    engine = EvidencePipelineEngine()

    # Ingest valid records
    record1 = engine.ingest("system-audit", {
        "type": "audit_log",
        "content": "User login event captured",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "severity": "info",
    })
    print(f"\nRecord 1: {record1.record_id[:8]}... -> {record1.state.value}")

    record2 = engine.ingest("compliance-scanner", {
        "type": "compliance_check",
        "content": "TLS certificate validation passed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "standard": "SOC2",
    })
    print(f"Record 2: {record2.record_id[:8]}... -> {record2.state.value}")

    record3 = engine.ingest("integrity-monitor", {
        "type": "integrity_check",
        "content": "File hash verification completed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "files_checked": 42,
    })
    print(f"Record 3: {record3.record_id[:8]}... -> {record3.state.value}")

    # Ingest invalid record (missing required fields)
    record_bad = engine.ingest("unknown-source", {
        "type": "incomplete",
    })
    print(f"Record Bad: {record_bad.record_id[:8]}... -> {record_bad.state.value}")

    # Verify chain integrity
    print("\n--- Chain Integrity ---")
    is_valid, errors = engine.verify_chain_integrity()
    print(f"Chain valid: {is_valid}")
    if errors:
        for err in errors:
            print(f"  ERROR: {err}")

    # Print pipeline stats
    print("\n--- Pipeline Stats ---")
    stats = engine.get_pipeline_stats()
    print(f"Total records: {stats['total_records']}")
    print(f"Processed: {stats['processed_records']}")
    print(f"Rejected: {stats['rejected_records']}")
    print(f"Chain length: {stats['chain_length']}")
    print(f"Chain head: {stats['chain_head']}")
    print(f"By state: {json.dumps(stats['by_state'], indent=2)}")

    print("\n" + "=" * 60)
    print("Evidence Pipeline Engine -- Demo Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
