"""Data Platform exceptions."""

from __future__ import annotations

from platform_shared.domain.errors import PlatformError


class DataPlatformError(PlatformError):
    """Root error for all data platform failures."""

    def __init__(self, message: str, **kw):
        super().__init__(message, code="DATA_PLATFORM_ERROR", **kw)


class EvidenceChainError(DataPlatformError):
    """The evidence hash chain has been broken or is invalid."""

    def __init__(self, message: str, *, record_id: str = "", **kw):
        super().__init__(message, **kw)
        self.code = "EVIDENCE_CHAIN_ERROR"
        self.record_id = record_id


class QualityCheckError(DataPlatformError):
    """A quality rule evaluation failed unexpectedly."""

    def __init__(self, message: str, *, rule_name: str = "", **kw):
        super().__init__(message, **kw)
        self.code = "QUALITY_CHECK_ERROR"
        self.rule_name = rule_name


class ReplayError(DataPlatformError):
    """Replay session encountered an error."""

    def __init__(self, message: str, *, session_id: str = "", **kw):
        super().__init__(message, **kw)
        self.code = "REPLAY_ERROR"
        self.session_id = session_id
