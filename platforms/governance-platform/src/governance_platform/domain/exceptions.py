"""Governance-specific exceptions."""

from __future__ import annotations

from platform_shared.domain.errors import PlatformError


class GovernanceError(PlatformError):
    """Base error for all governance platform failures."""

    def __init__(self, message: str, **kw):
        super().__init__(message, code="GOVERNANCE_ERROR", **kw)


class PolicyEvaluationError(GovernanceError):
    """Failed to evaluate a policy."""

    def __init__(self, message: str, *, policy_id: str = "", **kw):
        super().__init__(message, **kw)
        self.code = "POLICY_EVALUATION_ERROR"
        self.policy_id = policy_id


class QualityGateError(GovernanceError):
    """Failed to run a quality gate."""

    def __init__(self, message: str, *, gate_id: str = "", **kw):
        super().__init__(message, **kw)
        self.code = "QUALITY_GATE_ERROR"
        self.gate_id = gate_id


class ReasoningError(GovernanceError):
    """Failed during reasoning query."""

    def __init__(self, message: str, *, query_id: str = "", **kw):
        super().__init__(message, **kw)
        self.code = "REASONING_ERROR"
        self.query_id = query_id


class SandboxPolicyError(GovernanceError):
    """Failed during sandboxed policy evaluation."""

    def __init__(self, message: str, *, sandbox_id: str = "", **kw):
        super().__init__(message, **kw)
        self.code = "SANDBOX_POLICY_ERROR"
        self.sandbox_id = sandbox_id
