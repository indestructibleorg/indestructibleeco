"""Governance Module entity — the core unit being governed.

Each module represents a discrete component (service, library, config bundle)
within the ecosystem that is subject to governance scanning, compliance
enforcement, and evidence collection.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any

import structlog
from pydantic import BaseModel, Field

from domain.value_objects.compliance_status import ComplianceScore, ComplianceStatus

logger = structlog.get_logger(__name__)


class GovernanceModule(BaseModel):
    """Domain entity representing a governed module.

    Attributes:
        module_id: Globally-unique identifier (UUID-4 string).
        name: Human-readable module name (e.g. ``"auth-service"``).
        path: Filesystem or repository path to the module root.
        gl_layer: Governance Layer designation (e.g. ``"GL30-49"``).
        ng_era: Naming-generation era tag (e.g. ``"Era-2"``).
        compliance_status: Current compliance posture.
        last_scan_at: Timestamp of the most recent scan (UTC).
        hash_signature: SHA-256 content hash of the module's governed artefacts.
        bindings: List of binding identifiers linking this module to policies.
        metadata: Free-form metadata bag for extensibility.
    """

    module_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    path: str
    gl_layer: str = Field(pattern=r"^GL\d{1,3}(-\d{1,3})?$")
    ng_era: str = Field(pattern=r"^Era-\d+$")
    compliance_status: ComplianceStatus = ComplianceStatus.UNKNOWN
    last_scan_at: datetime | None = None
    hash_signature: str = ""
    bindings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": False, "populate_by_name": True}

    # -- domain logic -------------------------------------------------------

    def is_compliant(self) -> bool:
        """Return True when the module's current status is acceptable.

        Both ``COMPLIANT`` and ``EXEMPT`` are considered passing states.
        """
        passing = self.compliance_status.is_passing
        logger.debug(
            "compliance_check",
            module_id=self.module_id,
            status=self.compliance_status.value,
            passing=passing,
        )
        return passing

    def needs_remediation(self) -> bool:
        """Return True if the module requires corrective action.

        Modules that are ``NON_COMPLIANT`` or ``PARTIALLY_COMPLIANT``
        trigger this flag.
        """
        return self.compliance_status.requires_action

    def update_hash(self, new_hash: str) -> None:
        """Replace the current hash signature and log the change.

        This method also validates the hash format (must be 64 hex chars for
        SHA-256) and records the previous value in metadata for auditability.

        Args:
            new_hash: The new SHA-256 hex-digest to store.

        Raises:
            ValueError: If *new_hash* is not a valid 64-character hex string.
        """
        if len(new_hash) != 64 or not all(c in "0123456789abcdef" for c in new_hash.lower()):
            raise ValueError(
                f"Invalid SHA-256 hash: expected 64 hex characters, got '{new_hash}'"
            )
        previous = self.hash_signature
        self.hash_signature = new_hash.lower()
        self.metadata["_previous_hash"] = previous
        logger.info(
            "module_hash_updated",
            module_id=self.module_id,
            previous_hash=previous[:12] + "..." if previous else "<none>",
            new_hash=new_hash[:12] + "...",
        )

    # -- additional helpers --------------------------------------------------

    def mark_scanned(
        self,
        status: ComplianceStatus,
        score: ComplianceScore | None = None,
        scanned_at: datetime | None = None,
    ) -> None:
        """Update the module after a governance scan completes.

        Args:
            status: Resulting compliance status from the scan.
            score: Optional quantitative score from the scan.
            scanned_at: Explicit timestamp; defaults to ``utcnow``.
        """
        self.compliance_status = status
        self.last_scan_at = scanned_at or datetime.now(timezone.utc)
        if score is not None:
            self.metadata["last_score"] = score.to_dict()
        logger.info(
            "module_scanned",
            module_id=self.module_id,
            name=self.name,
            new_status=status.value,
        )

    def add_binding(self, binding_id: str) -> None:
        """Attach a policy binding to this module (idempotent)."""
        if binding_id not in self.bindings:
            self.bindings.append(binding_id)
            logger.debug("binding_added", module_id=self.module_id, binding=binding_id)

    def remove_binding(self, binding_id: str) -> bool:
        """Remove a policy binding. Returns True if it was present."""
        if binding_id in self.bindings:
            self.bindings.remove(binding_id)
            logger.debug("binding_removed", module_id=self.module_id, binding=binding_id)
            return True
        return False

    def compute_hash(self, content: bytes) -> str:
        """Compute a SHA-256 hash for *content* and store it.

        Convenience wrapper that both computes and persists the new hash.

        Returns:
            The computed hex-digest string.
        """
        digest = hashlib.sha256(content).hexdigest()
        self.update_hash(digest)
        return digest

    def summary(self) -> dict[str, Any]:
        """Return a concise dictionary summary suitable for dashboards."""
        return {
            "module_id": self.module_id,
            "name": self.name,
            "gl_layer": self.gl_layer,
            "ng_era": self.ng_era,
            "compliance": self.compliance_status.value,
            "last_scan": self.last_scan_at.isoformat() if self.last_scan_at else None,
            "binding_count": len(self.bindings),
        }
