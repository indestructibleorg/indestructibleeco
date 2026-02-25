"""Operational gate entity for the Governance Operations Platform.

Gates are decision points in the deployment and governance lifecycle.  They
evaluate a set of conditions against a runtime context and produce a pass/fail
outcome.  Gates can be blocked (halting progress) or overridden by authorised
approvers when business justification is provided.
"""
from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class GateType(str, enum.Enum):
    """Classification of gate purpose within the governance lifecycle."""

    PRE_DEPLOY = "pre_deploy"
    POST_DEPLOY = "post_deploy"
    COMPLIANCE = "compliance"
    SECURITY = "security"


class GateStatus(str, enum.Enum):
    """Current operational state of a gate."""

    OPEN = "open"
    CLOSED = "closed"
    BLOCKED = "blocked"
    OVERRIDDEN = "overridden"

    @property
    def allows_passage(self) -> bool:
        """Return True when the gate permits progress."""
        return self in {GateStatus.OPEN, GateStatus.OVERRIDDEN}


@dataclass(frozen=True, slots=True)
class GateCondition:
    """A single evaluable condition within a gate.

    Attributes:
        field: Dotted key path into the evaluation context (e.g.
            ``"compliance.score"``).
        operator: Comparison operator as a string (``"gte"``, ``"eq"``, etc.).
        value: The threshold or expected value.
        description: Human-readable explanation of what this condition checks.
    """

    field: str
    operator: str
    value: Any
    description: str = ""

    _OPERATORS: dict[str, Any] = field(
        default=None,  # type: ignore[assignment]
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        ops: dict[str, Any] = {
            "eq": lambda a, b: a == b,
            "neq": lambda a, b: a != b,
            "gt": lambda a, b: a > b,
            "gte": lambda a, b: a >= b,
            "lt": lambda a, b: a < b,
            "lte": lambda a, b: a <= b,
            "in": lambda a, b: a in b,
            "not_in": lambda a, b: a not in b,
            "contains": lambda a, b: b in a,
        }
        object.__setattr__(self, "_OPERATORS", ops)

    def evaluate(self, context: dict[str, Any]) -> bool:
        """Evaluate this condition against *context*.

        The *field* is resolved by splitting on ``"."`` and traversing nested
        dicts.  Returns False when the field is missing or the operator is
        unknown.
        """
        actual = self._resolve(context, self.field)
        if actual is _MISSING:
            logger.debug(
                "gate_condition_field_missing",
                field=self.field,
            )
            return False

        op_fn = self._OPERATORS.get(self.operator)
        if op_fn is None:
            logger.warning("gate_condition_unknown_operator", operator=self.operator)
            return False

        try:
            result = op_fn(actual, self.value)
        except TypeError:
            logger.warning(
                "gate_condition_type_error",
                field=self.field,
                actual_type=type(actual).__name__,
                value_type=type(self.value).__name__,
            )
            return False

        logger.debug(
            "gate_condition_evaluated",
            field=self.field,
            operator=self.operator,
            expected=self.value,
            actual=actual,
            result=result,
        )
        return bool(result)

    @staticmethod
    def _resolve(context: dict[str, Any], dotted: str) -> Any:
        """Walk a dotted path through nested dicts."""
        current: Any = context
        for part in dotted.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return _MISSING
        return current


class _MissingSentinel:
    """Sentinel for missing context fields."""

    def __repr__(self) -> str:
        return "<MISSING>"


_MISSING = _MissingSentinel()


class Gate(BaseModel):
    """Domain entity representing an operational governance gate.

    Attributes:
        gate_id: Unique identifier (UUID-4 string).
        name: Human-readable gate name.
        gate_type: Classification of this gate.
        conditions: Ordered list of conditions; all must pass for the gate
            to open.
        approval_matrix: Mapping of role -> required approval count.
        status: Current operational state.
        block_reason: Human-readable reason when status is BLOCKED.
        override_approver: Identity of the person who overrode the gate.
        override_at: Timestamp of the override action.
        evaluated_at: Timestamp of the last evaluation.
    """

    gate_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    gate_type: GateType
    conditions: list[GateCondition] = Field(default_factory=list)
    approval_matrix: dict[str, Any] = Field(default_factory=dict)
    status: GateStatus = GateStatus.CLOSED
    block_reason: str = ""
    override_approver: str = ""
    override_at: datetime | None = None
    evaluated_at: datetime | None = None

    model_config = {"frozen": False, "populate_by_name": True, "arbitrary_types_allowed": True}

    # -- core evaluation ----------------------------------------------------

    def evaluate(self, context: dict[str, Any]) -> bool:
        """Evaluate all conditions against *context*.

        If every condition passes the gate transitions to ``OPEN``;
        otherwise it stays ``CLOSED``.  A ``BLOCKED`` gate always returns
        False regardless of conditions.

        Returns:
            True if the gate is now passable, False otherwise.
        """
        if self.status == GateStatus.BLOCKED:
            logger.info(
                "gate_blocked_skip_eval",
                gate_id=self.gate_id,
                reason=self.block_reason,
            )
            return False

        results = [cond.evaluate(context) for cond in self.conditions]
        all_pass = all(results) if results else True
        self.status = GateStatus.OPEN if all_pass else GateStatus.CLOSED
        self.evaluated_at = datetime.now(timezone.utc)

        logger.info(
            "gate_evaluated",
            gate_id=self.gate_id,
            name=self.name,
            passed=all_pass,
            condition_results=results,
        )
        return all_pass

    def block(self, reason: str) -> None:
        """Block this gate with a human-readable *reason*.

        A blocked gate cannot be opened by evaluation — only by an explicit
        ``override`` call.
        """
        self.status = GateStatus.BLOCKED
        self.block_reason = reason
        logger.warning(
            "gate_blocked",
            gate_id=self.gate_id,
            name=self.name,
            reason=reason,
        )

    def override(self, approver: str) -> None:
        """Override a blocked or closed gate.

        The approver identity is recorded for audit purposes.

        Args:
            approver: Identifier (email, username) of the person approving.
        """
        previous = self.status
        self.status = GateStatus.OVERRIDDEN
        self.override_approver = approver
        self.override_at = datetime.now(timezone.utc)
        self.block_reason = ""
        logger.warning(
            "gate_overridden",
            gate_id=self.gate_id,
            name=self.name,
            previous_status=previous.value,
            approver=approver,
        )

    # -- helpers ------------------------------------------------------------

    def add_condition(self, condition: GateCondition) -> None:
        """Append a condition to this gate."""
        self.conditions.append(condition)
        logger.debug("gate_condition_added", gate_id=self.gate_id, field=condition.field)

    def summary(self) -> dict[str, Any]:
        """Return a concise dictionary summary."""
        return {
            "gate_id": self.gate_id,
            "name": self.name,
            "type": self.gate_type.value,
            "status": self.status.value,
            "condition_count": len(self.conditions),
            "evaluated_at": self.evaluated_at.isoformat() if self.evaluated_at else None,
        }
