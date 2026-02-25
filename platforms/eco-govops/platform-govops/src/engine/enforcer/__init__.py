"""Enforcer subsystem -- policy enforcement against scan results.

Exports:
    PolicyEnforcer     -- Evaluates governance policies and enforces compliance.
    PolicyRule         -- Pydantic model describing a single governance rule.
    EnforcementResult  -- Aggregated result of a policy enforcement run.
    EnforcementAction  -- Actions the enforcer can take on violation.
    RuleOutcome        -- Result of evaluating a single rule.
"""

from engine.enforcer.policy_enforcer import (
    EnforcementAction,
    EnforcementResult,
    PolicyEnforcer,
    PolicyRule,
    RuleOutcome,
)

__all__ = [
    "EnforcementAction",
    "EnforcementResult",
    "PolicyEnforcer",
    "PolicyRule",
    "RuleOutcome",
]
