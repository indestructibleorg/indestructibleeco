"""Exception hierarchy for the Governance Operations Platform.

Provides a structured, domain-driven exception taxonomy covering governance
cycles, compliance enforcement, evidence chains, ETL pipelines, and gate
management.  Every exception carries a machine-readable ``error_code``, a
``severity`` indicator, and an arbitrary ``context`` dict for downstream
logging / observability.

The presentation layer maps these exceptions to appropriate HTTP status
codes via global exception handlers.
"""
from __future__ import annotations

from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Severity levels
# ---------------------------------------------------------------------------

class Severity(str, Enum):
    """Severity levels for governance exceptions."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ---------------------------------------------------------------------------
# Base exception
# ---------------------------------------------------------------------------

class GovOpsError(Exception):
    """Root exception for every Governance Operations failure.

    Attributes:
        message:    Human-readable description.
        error_code: Machine-readable code (e.g. ``"GOV_001"``).
        severity:   Impact severity.
        context:    Arbitrary key-value context for structured logging.
    """

    def __init__(
        self,
        message: str = "Governance operations error",
        error_code: str = "GOVOPS_ERROR",
        severity: Severity = Severity.MEDIUM,
        context: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.error_code = error_code
        self.severity = severity
        self.context: dict[str, Any] = context or {}
        super().__init__(message)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}("
            f"error_code={self.error_code!r}, "
            f"severity={self.severity.value!r}, "
            f"message={self.message!r})"
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialise the exception for API error responses."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "severity": self.severity.value,
            "context": self.context,
        }


# ---------------------------------------------------------------------------
# Governance exceptions
# ---------------------------------------------------------------------------

class GovernanceError(GovOpsError):
    """Raised when a governance cycle or policy operation fails."""

    def __init__(self, message: str = "Governance operation failed", **kwargs: Any) -> None:
        super().__init__(message, error_code=kwargs.pop("error_code", "GOV_GOVERNANCE_ERROR"), **kwargs)


class ComplianceError(GovernanceError):
    """Raised when a compliance check detects a violation."""

    def __init__(self, message: str = "Compliance violation detected", **kwargs: Any) -> None:
        super().__init__(
            message,
            error_code=kwargs.pop("error_code", "GOV_COMPLIANCE_ERROR"),
            severity=kwargs.pop("severity", Severity.HIGH),
            **kwargs,
        )


class EnforcementError(GovernanceError):
    """Raised when an enforcement action cannot be carried out."""

    def __init__(self, message: str = "Enforcement action failed", **kwargs: Any) -> None:
        super().__init__(
            message,
            error_code=kwargs.pop("error_code", "GOV_ENFORCEMENT_ERROR"),
            severity=kwargs.pop("severity", Severity.HIGH),
            **kwargs,
        )


# ---------------------------------------------------------------------------
# Scanning exceptions
# ---------------------------------------------------------------------------

class ScanError(GovOpsError):
    """Raised when a governance scan encounters an irrecoverable problem."""

    def __init__(self, message: str = "Scan failed", **kwargs: Any) -> None:
        super().__init__(message, error_code=kwargs.pop("error_code", "GOV_SCAN_ERROR"), **kwargs)


class ExecutionError(ScanError):
    """Raised when a scan executor (plugin / agent) fails."""

    def __init__(self, message: str = "Scan execution failed", **kwargs: Any) -> None:
        super().__init__(message, error_code=kwargs.pop("error_code", "GOV_EXECUTION_ERROR"), **kwargs)


class RemediationError(ScanError):
    """Raised when an automated remediation step fails."""

    def __init__(self, message: str = "Remediation failed", **kwargs: Any) -> None:
        super().__init__(
            message,
            error_code=kwargs.pop("error_code", "GOV_REMEDIATION_ERROR"),
            severity=kwargs.pop("severity", Severity.HIGH),
            **kwargs,
        )


# ---------------------------------------------------------------------------
# Evidence chain exceptions
# ---------------------------------------------------------------------------

class EvidenceError(GovOpsError):
    """Raised when evidence collection or retrieval fails."""

    def __init__(self, message: str = "Evidence operation failed", **kwargs: Any) -> None:
        super().__init__(message, error_code=kwargs.pop("error_code", "GOV_EVIDENCE_ERROR"), **kwargs)


class ChainIntegrityError(EvidenceError):
    """Raised when the evidence chain's cryptographic integrity is broken."""

    def __init__(self, message: str = "Evidence chain integrity violation", **kwargs: Any) -> None:
        super().__init__(
            message,
            error_code=kwargs.pop("error_code", "GOV_CHAIN_INTEGRITY_ERROR"),
            severity=kwargs.pop("severity", Severity.CRITICAL),
            **kwargs,
        )


class SealError(EvidenceError):
    """Raised when an evidence seal cannot be created or verified."""

    def __init__(self, message: str = "Evidence seal failure", **kwargs: Any) -> None:
        super().__init__(
            message,
            error_code=kwargs.pop("error_code", "GOV_SEAL_ERROR"),
            severity=kwargs.pop("severity", Severity.CRITICAL),
            **kwargs,
        )


# ---------------------------------------------------------------------------
# ETL exceptions
# ---------------------------------------------------------------------------

class ETLError(GovOpsError):
    """Raised when an ETL pipeline encounters a general failure."""

    def __init__(self, message: str = "ETL pipeline error", **kwargs: Any) -> None:
        super().__init__(message, error_code=kwargs.pop("error_code", "GOV_ETL_ERROR"), **kwargs)


class ExtractionError(ETLError):
    """Raised when the extraction phase of an ETL pipeline fails."""

    def __init__(self, message: str = "ETL extraction failed", **kwargs: Any) -> None:
        super().__init__(message, error_code=kwargs.pop("error_code", "GOV_EXTRACTION_ERROR"), **kwargs)


class TransformError(ETLError):
    """Raised when the transformation phase of an ETL pipeline fails."""

    def __init__(self, message: str = "ETL transformation failed", **kwargs: Any) -> None:
        super().__init__(message, error_code=kwargs.pop("error_code", "GOV_TRANSFORM_ERROR"), **kwargs)


class LoadError(ETLError):
    """Raised when the load phase of an ETL pipeline fails."""

    def __init__(self, message: str = "ETL load failed", **kwargs: Any) -> None:
        super().__init__(message, error_code=kwargs.pop("error_code", "GOV_LOAD_ERROR"), **kwargs)


# ---------------------------------------------------------------------------
# Gate exceptions
# ---------------------------------------------------------------------------

class GateError(GovOpsError):
    """Raised when a governance gate evaluation fails."""

    def __init__(self, message: str = "Gate evaluation error", **kwargs: Any) -> None:
        super().__init__(message, error_code=kwargs.pop("error_code", "GOV_GATE_ERROR"), **kwargs)


class GateBlockedError(GateError):
    """Raised when a governance gate blocks progression."""

    def __init__(self, message: str = "Gate blocked — criteria not met", **kwargs: Any) -> None:
        super().__init__(
            message,
            error_code=kwargs.pop("error_code", "GOV_GATE_BLOCKED"),
            severity=kwargs.pop("severity", Severity.HIGH),
            **kwargs,
        )


# ---------------------------------------------------------------------------
# Configuration / validation exceptions
# ---------------------------------------------------------------------------

class ConfigurationError(GovOpsError):
    """Raised when the platform encounters an invalid or missing configuration."""

    def __init__(self, message: str = "Configuration error", **kwargs: Any) -> None:
        super().__init__(message, error_code=kwargs.pop("error_code", "GOV_CONFIG_ERROR"), **kwargs)


class ValidationError(GovOpsError):
    """Raised when input data fails validation."""

    def __init__(self, message: str = "Validation error", **kwargs: Any) -> None:
        super().__init__(
            message,
            error_code=kwargs.pop("error_code", "GOV_VALIDATION_ERROR"),
            severity=kwargs.pop("severity", Severity.LOW),
            **kwargs,
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__ = [
    "Severity",
    "GovOpsError",
    "GovernanceError",
    "ComplianceError",
    "EnforcementError",
    "ScanError",
    "ExecutionError",
    "RemediationError",
    "EvidenceError",
    "ChainIntegrityError",
    "SealError",
    "ETLError",
    "ExtractionError",
    "TransformError",
    "LoadError",
    "GateError",
    "GateBlockedError",
    "ConfigurationError",
    "ValidationError",
]
