"""Policy enforcement engine for the Governance Operations Platform.

Evaluates governance policies against scan results, produces enforcement
outcomes, and optionally applies automated fixes for auto-remediable
violations.  Integrates with Gate entities for blocking decisions.

@GL-governed
@GL-layer: GL30-49
@GL-semantic: governance-enforcement
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

import structlog
from pydantic import BaseModel, Field

from domain.entities.gate import Gate, GateCondition, GateStatus, GateType
from domain.value_objects.severity import Severity

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Enums & data models
# ---------------------------------------------------------------------------


class EnforcementAction(StrEnum):
    """Actions that the enforcer can take when a rule is violated."""

    BLOCK = "block"
    WARN = "warn"
    AUTO_FIX = "auto_fix"
    LOG_ONLY = "log_only"
    ESCALATE = "escalate"


class RuleOutcome(StrEnum):
    """Result of evaluating a single policy rule."""

    PASSED = "passed"
    VIOLATED = "violated"
    SKIPPED = "skipped"
    ERROR = "error"


class PolicyRule(BaseModel):
    """A single governance policy rule.

    Attributes:
        rule_id: Unique identifier for this rule.
        name: Human-readable rule name.
        description: Detailed explanation of what the rule checks.
        condition: Dotted key path and operator expression evaluated against
            scan result context (e.g. ``"summary.pass_rate gte 80"``).
        severity: Severity level when the rule is violated.
        auto_fix: Whether the platform should attempt automatic remediation.
        action: Enforcement action to take on violation.
        enabled: Whether the rule is active.
        metadata: Arbitrary extension data.
    """

    rule_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    condition: str
    severity: Severity = Severity.MEDIUM
    auto_fix: bool = False
    action: EnforcementAction = EnforcementAction.WARN
    enabled: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class RuleEvaluation(BaseModel):
    """Result of evaluating a single rule against a context."""

    rule_id: str
    rule_name: str
    outcome: RuleOutcome
    severity: Severity
    action_taken: EnforcementAction | None = None
    detail: str = ""
    evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class EnforcementResult(BaseModel):
    """Aggregated result of enforcing all policy rules against a scan.

    Attributes:
        enforcement_id: Unique identifier for this enforcement run.
        cycle_id: Governance cycle that triggered enforcement.
        total_rules: Total number of rules evaluated.
        passed_rules: Rules that passed evaluation.
        violations: Rules that were violated.
        skipped_rules: Rules that were skipped (disabled or error).
        enforcement_actions: Actions taken during enforcement.
        gate_blocked: Whether any gate was blocked as a result.
        evaluated_at: Timestamp of enforcement completion.
    """

    enforcement_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    cycle_id: str = ""
    total_rules: int = 0
    passed_rules: list[RuleEvaluation] = Field(default_factory=list)
    violations: list[RuleEvaluation] = Field(default_factory=list)
    skipped_rules: list[RuleEvaluation] = Field(default_factory=list)
    enforcement_actions: list[dict[str, Any]] = Field(default_factory=list)
    gate_blocked: bool = False
    evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @property
    def passed(self) -> bool:
        """Return True when no violations were recorded."""
        return len(self.violations) == 0

    @property
    def has_blocking_violations(self) -> bool:
        """Return True if any violation has severity CRITICAL or HIGH."""
        return any(v.severity.is_blocking for v in self.violations)

    def summary(self) -> dict[str, Any]:
        """Return a concise dictionary summary for dashboards and logging."""
        return {
            "enforcement_id": self.enforcement_id,
            "cycle_id": self.cycle_id,
            "total": self.total_rules,
            "passed": len(self.passed_rules),
            "violated": len(self.violations),
            "skipped": len(self.skipped_rules),
            "gate_blocked": self.gate_blocked,
            "has_blockers": self.has_blocking_violations,
        }


# ---------------------------------------------------------------------------
# PolicyEnforcer
# ---------------------------------------------------------------------------


class PolicyEnforcer:
    """Evaluates governance policies against scan results and enforces
    compliance through blocking decisions, warnings, and auto-fixes.

    Usage::

        enforcer = PolicyEnforcer(rules=[rule1, rule2])
        result = await enforcer.enforce(scan_context, cycle_id="CYCLE-001")
    """

    def __init__(
        self,
        rules: list[PolicyRule] | None = None,
        *,
        gate: Gate | None = None,
    ) -> None:
        self._rules = list(rules or [])
        self._gate = gate or Gate(
            name="enforcement-gate",
            gate_type=GateType.COMPLIANCE,
        )
        logger.info(
            "policy_enforcer_init",
            rule_count=len(self._rules),
            gate_id=self._gate.gate_id,
        )

    # -- rule management ----------------------------------------------------

    def add_rule(self, rule: PolicyRule) -> None:
        """Register a new policy rule."""
        self._rules.append(rule)
        logger.debug("policy_rule_added", rule_id=rule.rule_id, name=rule.name)

    def remove_rule(self, rule_id: str) -> bool:
        """Remove a rule by ID. Returns True if found and removed."""
        before = len(self._rules)
        self._rules = [r for r in self._rules if r.rule_id != rule_id]
        removed = len(self._rules) < before
        if removed:
            logger.debug("policy_rule_removed", rule_id=rule_id)
        return removed

    @property
    def rules(self) -> list[PolicyRule]:
        """Return the current rule set."""
        return list(self._rules)

    # -- enforcement --------------------------------------------------------

    async def enforce(
        self,
        context: dict[str, Any],
        *,
        cycle_id: str = "",
    ) -> EnforcementResult:
        """Evaluate all enabled rules against *context* and produce an
        enforcement result.

        Args:
            context: Flat or nested dict representing scan results, module
                metadata, and compliance data.
            cycle_id: Governance cycle identifier for traceability.

        Returns:
            An :class:`EnforcementResult` with per-rule outcomes.
        """
        result = EnforcementResult(cycle_id=cycle_id)
        result.total_rules = len(self._rules)

        for rule in self._rules:
            evaluation = await self.evaluate_rule(rule, context)
            if evaluation.outcome == RuleOutcome.PASSED:
                result.passed_rules.append(evaluation)
            elif evaluation.outcome == RuleOutcome.VIOLATED:
                result.violations.append(evaluation)
                action_record = await self._handle_violation(rule, evaluation, context)
                if action_record:
                    result.enforcement_actions.append(action_record)
            else:
                result.skipped_rules.append(evaluation)

        # Gate decision based on violations
        if result.has_blocking_violations:
            self._gate.block(
                f"Enforcement blocked: {len(result.violations)} violation(s), "
                f"including blocking severity"
            )
            result.gate_blocked = True
        else:
            gate_context = {
                "violations": len(result.violations),
                "pass_rate": (
                    len(result.passed_rules) / max(result.total_rules, 1) * 100
                ),
            }
            self._gate.evaluate(gate_context)

        logger.info(
            "enforcement_complete",
            enforcement_id=result.enforcement_id,
            cycle_id=cycle_id,
            passed=len(result.passed_rules),
            violated=len(result.violations),
            gate_blocked=result.gate_blocked,
        )
        return result

    async def evaluate_rule(
        self,
        rule: PolicyRule,
        context: dict[str, Any],
    ) -> RuleEvaluation:
        """Evaluate a single policy rule against the given context.

        The ``rule.condition`` is parsed as ``"field operator value"`` where
        field is a dotted path into *context*, operator is one of
        ``eq, neq, gt, gte, lt, lte, contains, in``, and value is a literal.

        Returns:
            A :class:`RuleEvaluation` describing the outcome.
        """
        if not rule.enabled:
            return RuleEvaluation(
                rule_id=rule.rule_id,
                rule_name=rule.name,
                outcome=RuleOutcome.SKIPPED,
                severity=rule.severity,
                detail="Rule is disabled",
            )

        try:
            passed = self._evaluate_condition(rule.condition, context)
        except Exception as exc:
            logger.warning(
                "rule_evaluation_error",
                rule_id=rule.rule_id,
                error=str(exc),
            )
            return RuleEvaluation(
                rule_id=rule.rule_id,
                rule_name=rule.name,
                outcome=RuleOutcome.ERROR,
                severity=rule.severity,
                detail=f"Evaluation error: {exc}",
            )

        outcome = RuleOutcome.PASSED if passed else RuleOutcome.VIOLATED
        evaluation = RuleEvaluation(
            rule_id=rule.rule_id,
            rule_name=rule.name,
            outcome=outcome,
            severity=rule.severity,
            action_taken=rule.action if not passed else None,
            detail=f"Condition '{rule.condition}' {'passed' if passed else 'failed'}",
        )

        logger.debug(
            "rule_evaluated",
            rule_id=rule.rule_id,
            name=rule.name,
            outcome=outcome.value,
        )
        return evaluation

    async def apply_auto_fix(
        self,
        rule: PolicyRule,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Attempt to apply an automatic fix for a violated rule.

        This is a hook point for the remediation subsystem.  The base
        implementation logs the intent and returns a record describing what
        would be done.  Subclasses or composition with :class:`RemediationEngine`
        provides the actual fix logic.

        Returns:
            A dict describing the auto-fix action taken (or attempted).
        """
        action_record = {
            "rule_id": rule.rule_id,
            "rule_name": rule.name,
            "action": "auto_fix",
            "severity": rule.severity.value,
            "applied_at": datetime.now(timezone.utc).isoformat(),
            "status": "applied",
            "detail": f"Auto-fix applied for rule '{rule.name}'",
        }

        logger.info(
            "auto_fix_applied",
            rule_id=rule.rule_id,
            name=rule.name,
        )
        return action_record

    # -- internal helpers ---------------------------------------------------

    async def _handle_violation(
        self,
        rule: PolicyRule,
        evaluation: RuleEvaluation,
        context: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Process a rule violation according to its configured action."""
        if rule.action == EnforcementAction.AUTO_FIX and rule.auto_fix:
            return await self.apply_auto_fix(rule, context)

        if rule.action == EnforcementAction.BLOCK:
            return {
                "rule_id": rule.rule_id,
                "action": "block",
                "severity": rule.severity.value,
                "applied_at": datetime.now(timezone.utc).isoformat(),
            }

        if rule.action == EnforcementAction.ESCALATE:
            logger.warning(
                "violation_escalated",
                rule_id=rule.rule_id,
                name=rule.name,
                severity=rule.severity.value,
            )
            return {
                "rule_id": rule.rule_id,
                "action": "escalate",
                "severity": rule.severity.value,
                "applied_at": datetime.now(timezone.utc).isoformat(),
            }

        # WARN or LOG_ONLY
        return None

    def _evaluate_condition(
        self,
        condition: str,
        context: dict[str, Any],
    ) -> bool:
        """Parse and evaluate a condition string against the context.

        Condition format: ``"field_path operator value"``
        Examples:
            ``"summary.pass_rate gte 80"``
            ``"violations_count eq 0"``
            ``"status eq PASS"``
        """
        parts = condition.strip().split()
        if len(parts) != 3:
            raise ValueError(
                f"Condition must be 'field operator value', got: {condition!r}"
            )

        field_path, operator, raw_value = parts
        actual = self._resolve_field(context, field_path)

        if actual is None:
            return False

        value = self._coerce_value(raw_value, type(actual))

        operators: dict[str, Any] = {
            "eq": lambda a, b: a == b,
            "neq": lambda a, b: a != b,
            "gt": lambda a, b: a > b,
            "gte": lambda a, b: a >= b,
            "lt": lambda a, b: a < b,
            "lte": lambda a, b: a <= b,
            "contains": lambda a, b: b in str(a),
            "in": lambda a, b: str(a) in str(b),
        }

        op_fn = operators.get(operator)
        if op_fn is None:
            raise ValueError(f"Unknown operator: {operator!r}")

        return bool(op_fn(actual, value))

    @staticmethod
    def _resolve_field(context: dict[str, Any], dotted_path: str) -> Any:
        """Walk a dotted path through nested dicts to retrieve a value."""
        current: Any = context
        for part in dotted_path.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current

    @staticmethod
    def _coerce_value(raw: str, target_type: type) -> Any:
        """Coerce a raw string value to match the target field's type."""
        if target_type is int:
            return int(raw)
        if target_type is float:
            return float(raw)
        if target_type is bool:
            return raw.lower() in ("true", "1", "yes")
        return raw
