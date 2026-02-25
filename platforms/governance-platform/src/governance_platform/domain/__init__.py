"""Governance domain — entities, value objects, events, exceptions."""

from governance_platform.domain.entities import (
    ComplianceReport,
    Policy,
    PolicyRule,
    QualityGate,
    ReasoningQuery,
)
from governance_platform.domain.value_objects import (
    ArbitrationDecision,
    ComplianceLevel,
    GateVerdict,
    PolicySeverity,
    ReasoningConfidence,
)
from governance_platform.domain.events import (
    GateFailed,
    GatePassed,
    PolicyEvaluated,
    ReasoningCompleted,
    ViolationDetected,
)
from governance_platform.domain.exceptions import (
    GovernanceError,
    PolicyEvaluationError,
    QualityGateError,
    ReasoningError,
    SandboxPolicyError,
)

__all__ = [
    # Entities
    "Policy",
    "PolicyRule",
    "QualityGate",
    "ComplianceReport",
    "ReasoningQuery",
    # Value objects
    "PolicySeverity",
    "GateVerdict",
    "ComplianceLevel",
    "ArbitrationDecision",
    "ReasoningConfidence",
    # Events
    "PolicyEvaluated",
    "GatePassed",
    "GateFailed",
    "ViolationDetected",
    "ReasoningCompleted",
    # Exceptions
    "GovernanceError",
    "PolicyEvaluationError",
    "QualityGateError",
    "ReasoningError",
    "SandboxPolicyError",
]
