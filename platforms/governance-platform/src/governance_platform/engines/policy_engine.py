"""PolicyEngine — evaluate governance policies against operations.

Supports operators: eq, ne, gt, lt, contains, matches_regex.
Returns violations with severity for each policy that fails.
"""

from __future__ import annotations

import re
from typing import Any

from platform_shared.protocols.engine import Engine, EngineStatus

from governance_platform.domain.entities import Policy, PolicyResult, PolicyRule
from governance_platform.domain.events import PolicyEvaluated, ViolationDetected
from governance_platform.domain.exceptions import PolicyEvaluationError
from governance_platform.domain.value_objects import PolicySeverity


def _get_nested(data: dict[str, Any], field_path: str) -> Any:
    """Resolve a dot-separated field path against a nested dict."""
    parts = field_path.split(".")
    current: Any = data
    for part in parts:
        if isinstance(current, dict):
            if part not in current:
                return _MISSING
            current = current[part]
        else:
            return _MISSING
    return current


class _MissingSentinel:
    """Sentinel for missing field values."""

    def __repr__(self) -> str:
        return "<MISSING>"


_MISSING = _MissingSentinel()


def _evaluate_rule(rule: PolicyRule, actual: Any) -> bool:
    """Evaluate a single rule. Returns True if the rule *passes* (no violation)."""
    if isinstance(actual, _MissingSentinel):
        # Missing field is always a violation (unless operator is ne)
        return rule.operator == "ne"

    op = rule.operator.lower()

    if op == "eq":
        return actual == rule.value
    elif op == "ne":
        return actual != rule.value
    elif op == "gt":
        try:
            return float(actual) > float(rule.value)
        except (TypeError, ValueError):
            return False
    elif op == "lt":
        try:
            return float(actual) < float(rule.value)
        except (TypeError, ValueError):
            return False
    elif op == "contains":
        if isinstance(actual, str):
            return str(rule.value) in actual
        if isinstance(actual, (list, tuple, set)):
            return rule.value in actual
        return False
    elif op == "matches_regex":
        if not isinstance(actual, str):
            return False
        try:
            return bool(re.search(str(rule.value), actual))
        except re.error:
            return False
    else:
        raise PolicyEvaluationError(f"Unknown operator: {rule.operator}")


class PolicyEngine:
    """Evaluates governance policies against operations (dict payloads).

    Implements the shared Engine protocol for lifecycle integration.
    """

    def __init__(self) -> None:
        self._status = EngineStatus.IDLE
        self._evaluations: list[PolicyEvaluated] = []
        self._violations: list[ViolationDetected] = []

    # -- Engine protocol -------------------------------------------------------

    @property
    def name(self) -> str:
        return "policy-engine"

    @property
    def status(self) -> EngineStatus:
        return self._status

    async def start(self) -> None:
        self._status = EngineStatus.RUNNING

    async def stop(self) -> None:
        self._status = EngineStatus.STOPPED

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Engine protocol entry point — expects {operation, policies}."""
        operation = payload.get("operation", {})
        policies_raw = payload.get("policies", [])
        policies = [self._dict_to_policy(p) if isinstance(p, dict) else p for p in policies_raw]
        results = self.evaluate(operation, policies)
        return {
            "results": [
                {
                    "policy_id": r.policy_id,
                    "policy_name": r.policy_name,
                    "passed": r.passed,
                    "violations": r.violations,
                    "severity": r.severity.value,
                }
                for r in results
            ],
            "all_passed": all(r.passed for r in results),
        }

    # -- Core API --------------------------------------------------------------

    def evaluate(self, operation: dict[str, Any], policies: list[Policy]) -> list[PolicyResult]:
        """Evaluate all policies against an operation dict. Returns a PolicyResult per policy."""
        results: list[PolicyResult] = []

        for policy in policies:
            if not policy.enabled:
                results.append(
                    PolicyResult(
                        policy_id=policy.id,
                        policy_name=policy.name,
                        passed=True,
                        violations=[],
                        severity=policy.severity,
                    )
                )
                continue

            violations: list[str] = []
            violation_events: list[ViolationDetected] = []

            for rule in policy.rules:
                actual = _get_nested(operation, rule.field)
                if not _evaluate_rule(rule, actual):
                    actual_repr = "<missing>" if isinstance(actual, _MissingSentinel) else actual
                    msg = (
                        f"Rule violated: {rule.field} {rule.operator} {rule.value!r} "
                        f"(actual: {actual_repr!r})"
                    )
                    violations.append(msg)
                    violation_events.append(
                        ViolationDetected(
                            policy_id=policy.id,
                            policy_name=policy.name,
                            rule_field=rule.field,
                            rule_operator=rule.operator,
                            expected=rule.value,
                            actual=actual_repr,
                            severity=policy.severity.value,
                            message=msg,
                        )
                    )

            passed = len(violations) == 0
            result = PolicyResult(
                policy_id=policy.id,
                policy_name=policy.name,
                passed=passed,
                violations=violations,
                severity=policy.severity,
            )
            results.append(result)

            # Record events
            self._evaluations.append(
                PolicyEvaluated(
                    policy_id=policy.id,
                    policy_name=policy.name,
                    passed=passed,
                    violation_count=len(violations),
                    severity=policy.severity.value,
                )
            )
            self._violations.extend(violation_events)

        return results

    @property
    def evaluation_history(self) -> list[PolicyEvaluated]:
        return list(self._evaluations)

    @property
    def violation_history(self) -> list[ViolationDetected]:
        return list(self._violations)

    @staticmethod
    def _dict_to_policy(d: dict[str, Any]) -> Policy:
        """Convert a plain dict to a Policy entity."""
        rules = [
            PolicyRule(field=r["field"], operator=r["operator"], value=r["value"])
            for r in d.get("rules", [])
        ]
        return Policy(
            id=d.get("id", ""),
            name=d.get("name", ""),
            rules=rules,
            severity=PolicySeverity(d.get("severity", "medium")),
            description=d.get("description", ""),
            enabled=d.get("enabled", True),
        )
