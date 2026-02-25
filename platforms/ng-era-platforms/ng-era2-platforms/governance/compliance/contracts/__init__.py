# @ECO-layer: GL60-80
# @ECO-governed
"""
GL Governance Compliance - Contracts Module

This module provides GL contract validation, policy evaluation,
and quality gate enforcement.
"""

from .gl_contract import GLContract, GLContractException
from .gl_policy import GLPolicy, PolicyCondition
from .gl_validator import GLContractValidator, ValidationResult, ValidationError
from .gl_quality_gate import GLQualityGate, QualityGateStatus
from .gl_audit_event import GLAuditEvent

__all__ = [
    'GLContract',
    'GLContractException',
    'GLPolicy',
    'PolicyCondition',
    'GLContractValidator',
    'ValidationResult',
    'ValidationError',
    'GLQualityGate',
    'QualityGateStatus',
    'GLAuditEvent'
]

__version__ = '1.0.0'