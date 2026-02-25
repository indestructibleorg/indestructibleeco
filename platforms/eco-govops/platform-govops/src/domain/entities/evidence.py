"""Immutable governance evidence entity.

Evidence records are the audit trail of the Governance Operations Platform.
They are append-only — once created, they cannot be modified or deleted.  Each
record optionally links to a previous hash forming a tamper-evident chain
(similar to a blockchain).
"""
from __future__ import annotations

import enum
import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class EvidenceType(str, enum.Enum):
    """Classification of evidence artefacts.

    Each type maps to a different stage or subsystem of the governance
    closed-loop cycle.
    """

    SCAN_RESULT = "scan_result"
    COMPLIANCE_CHECK = "compliance_check"
    REMEDIATION_ACTION = "remediation_action"
    GATE_DECISION = "gate_decision"
    POLICY_CHANGE = "policy_change"
    DRIFT_DETECTION = "drift_detection"
    MANUAL_ATTESTATION = "manual_attestation"
    APPROVAL_RECORD = "approval_record"
    CONFIGURATION_SNAPSHOT = "configuration_snapshot"


class Evidence(BaseModel):
    """Domain entity representing a single immutable evidence record.

    Attributes:
        evidence_id: Globally-unique identifier (UUID-4 string).
        cycle_id: Governance cycle that produced this evidence.
        module_id: The module this evidence pertains to.
        evidence_type: Categorisation of the evidence.
        content_hash: SHA-256 digest of the canonical payload.
        payload: Arbitrary structured content of the evidence.
        created_at: UTC timestamp of creation.
        chain_previous_hash: Hash of the preceding evidence in the chain,
            or None for the genesis record of a cycle.
    """

    evidence_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    cycle_id: str
    module_id: str
    evidence_type: EvidenceType
    content_hash: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    chain_previous_hash: str | None = None

    model_config = {"frozen": True, "populate_by_name": True}

    # -- factory / lifecycle ------------------------------------------------

    @classmethod
    def create(
        cls,
        cycle_id: str,
        module_id: str,
        evidence_type: EvidenceType,
        payload: dict[str, Any],
        previous_hash: str | None = None,
    ) -> Evidence:
        """Factory that auto-computes *content_hash* from *payload*.

        This is the preferred way to construct Evidence records to ensure
        the content hash is always consistent with the payload.
        """
        content_hash = cls._compute_content_hash(payload)
        evidence = cls(
            cycle_id=cycle_id,
            module_id=module_id,
            evidence_type=evidence_type,
            content_hash=content_hash,
            payload=payload,
            chain_previous_hash=previous_hash,
        )
        logger.info(
            "evidence_created",
            evidence_id=evidence.evidence_id,
            cycle_id=cycle_id,
            evidence_type=evidence_type.value,
            content_hash=content_hash[:16] + "...",
        )
        return evidence

    # -- integrity verification ---------------------------------------------

    def verify_integrity(self) -> bool:
        """Recompute the content hash and compare to the stored value.

        Returns True when the payload has not been tampered with.
        """
        expected = self._compute_content_hash(self.payload)
        is_valid = expected == self.content_hash
        if not is_valid:
            logger.error(
                "evidence_integrity_failure",
                evidence_id=self.evidence_id,
                expected=expected[:16] + "...",
                actual=self.content_hash[:16] + "...",
            )
        else:
            logger.debug(
                "evidence_integrity_ok",
                evidence_id=self.evidence_id,
            )
        return is_valid

    # -- chain operations ---------------------------------------------------

    def to_chain_entry(self) -> dict[str, Any]:
        """Serialise this evidence into a dict suitable for chain storage.

        The resulting dictionary contains exactly the fields needed to
        reconstruct and verify the chain link.
        """
        return {
            "evidence_id": self.evidence_id,
            "cycle_id": self.cycle_id,
            "module_id": self.module_id,
            "evidence_type": self.evidence_type.value,
            "content_hash": self.content_hash,
            "created_at": self.created_at.isoformat(),
            "chain_previous_hash": self.chain_previous_hash,
            "chain_hash": self._chain_hash(),
        }

    def _chain_hash(self) -> str:
        """Compute the chain hash for this entry.

        ``chain_hash = SHA-256(content_hash || chain_previous_hash || evidence_id)``
        """
        parts = f"{self.content_hash}|{self.chain_previous_hash or 'genesis'}|{self.evidence_id}"
        return hashlib.sha256(parts.encode("utf-8")).hexdigest()

    # -- helpers ------------------------------------------------------------

    @staticmethod
    def _compute_content_hash(payload: dict[str, Any]) -> str:
        """Deterministic SHA-256 of *payload* via canonical JSON."""
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def summary(self) -> dict[str, Any]:
        """Return a concise representation for logging / dashboards."""
        return {
            "evidence_id": self.evidence_id,
            "cycle_id": self.cycle_id,
            "module_id": self.module_id,
            "type": self.evidence_type.value,
            "created_at": self.created_at.isoformat(),
            "has_chain_link": self.chain_previous_hash is not None,
        }

    @classmethod
    def verify_chain_sequence(cls, records: list[Evidence]) -> bool:
        """Verify an ordered list of evidence records forms a valid chain.

        The first record must have ``chain_previous_hash == None``.  Each
        subsequent record's ``chain_previous_hash`` must equal the
        ``content_hash`` of its predecessor.

        Returns True when the entire chain is intact.
        """
        if not records:
            return True

        if records[0].chain_previous_hash is not None:
            logger.error("chain_genesis_invalid", evidence_id=records[0].evidence_id)
            return False

        for i in range(1, len(records)):
            expected_prev = records[i - 1].content_hash
            actual_prev = records[i].chain_previous_hash
            if actual_prev != expected_prev:
                logger.error(
                    "chain_link_broken",
                    index=i,
                    evidence_id=records[i].evidence_id,
                    expected=expected_prev[:16] + "...",
                    actual=(actual_prev[:16] + "..." if actual_prev else "<none>"),
                )
                return False
            if not records[i].verify_integrity():
                return False

        return True
