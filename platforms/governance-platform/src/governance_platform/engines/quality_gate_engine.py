"""QualityGateEngine — multi-gate pipeline for compliance verification.

Evaluates all checks in a quality gate, computes a score, and returns a
ComplianceReport with PASS/FAIL verdict based on the gate's threshold.
"""

from __future__ import annotations

from typing import Any

from platform_shared.protocols.engine import Engine, EngineStatus

from governance_platform.domain.entities import (
    CheckResult,
    ComplianceReport,
    GateCheck,
    QualityGate,
)
from governance_platform.domain.events import GateFailed, GatePassed
from governance_platform.domain.exceptions import QualityGateError
from governance_platform.domain.value_objects import ComplianceLevel, GateVerdict


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
    def __repr__(self) -> str:
        return "<MISSING>"


_MISSING = _MissingSentinel()


def _evaluate_check(check: GateCheck, actual: Any) -> CheckResult:
    """Evaluate a single gate check. Returns a CheckResult."""
    if isinstance(actual, _MissingSentinel):
        return CheckResult(
            check_name=check.name,
            passed=False,
            actual=None,
            expected=check.expected,
            message=f"Field '{check.field}' is missing",
        )

    op = check.operator.lower()
    passed = False

    try:
        if op == "eq":
            passed = actual == check.expected
        elif op == "ne":
            passed = actual != check.expected
        elif op == "gt":
            passed = float(actual) > float(check.expected)
        elif op == "lt":
            passed = float(actual) < float(check.expected)
        elif op == "gte":
            passed = float(actual) >= float(check.expected)
        elif op == "lte":
            passed = float(actual) <= float(check.expected)
        elif op == "contains":
            if isinstance(actual, str):
                passed = str(check.expected) in actual
            elif isinstance(actual, (list, tuple, set)):
                passed = check.expected in actual
        elif op == "not_empty":
            if isinstance(actual, str):
                passed = len(actual.strip()) > 0
            elif isinstance(actual, (list, tuple, dict)):
                passed = len(actual) > 0
            else:
                passed = actual is not None
        else:
            return CheckResult(
                check_name=check.name,
                passed=False,
                actual=actual,
                expected=check.expected,
                message=f"Unknown operator: {check.operator}",
            )
    except (TypeError, ValueError) as exc:
        return CheckResult(
            check_name=check.name,
            passed=False,
            actual=actual,
            expected=check.expected,
            message=f"Comparison error: {exc}",
        )

    message = "Check passed" if passed else (
        f"Expected {check.field} {check.operator} {check.expected!r}, got {actual!r}"
    )

    return CheckResult(
        check_name=check.name,
        passed=passed,
        actual=actual,
        expected=check.expected,
        message=message,
    )


class QualityGateEngine:
    """Runs quality gates against data and produces compliance reports.

    Implements the shared Engine protocol for lifecycle integration.
    """

    def __init__(self) -> None:
        self._status = EngineStatus.IDLE
        self._events: list[GatePassed | GateFailed] = []

    # -- Engine protocol -------------------------------------------------------

    @property
    def name(self) -> str:
        return "quality-gate-engine"

    @property
    def status(self) -> EngineStatus:
        return self._status

    async def start(self) -> None:
        self._status = EngineStatus.RUNNING

    async def stop(self) -> None:
        self._status = EngineStatus.STOPPED

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Engine protocol entry point — expects {gate, data}."""
        gate_raw = payload.get("gate", {})
        data = payload.get("data", {})
        gate = self._dict_to_gate(gate_raw) if isinstance(gate_raw, dict) else gate_raw
        report = self.run_gate(gate, data)
        return {
            "gate_id": report.gate_id,
            "gate_name": report.gate_name,
            "passed": report.passed,
            "score": report.score,
            "verdict": report.verdict.value,
            "compliance_level": report.compliance_level.value,
            "results": [
                {
                    "check_name": r.check_name,
                    "passed": r.passed,
                    "actual": r.actual,
                    "expected": r.expected,
                    "message": r.message,
                }
                for r in report.results
            ],
        }

    # -- Core API --------------------------------------------------------------

    def run_gate(self, gate: QualityGate, data: dict[str, Any]) -> ComplianceReport:
        """Evaluate all checks in a gate, compute score, return ComplianceReport."""
        if not gate.checks:
            report = ComplianceReport(
                gate_id=gate.id,
                gate_name=gate.name,
                results=[],
                passed=True,
                score=1.0,
                verdict=GateVerdict.SKIP,
                compliance_level=ComplianceLevel.FULL,
            )
            return report

        results: list[CheckResult] = []
        for check in gate.checks:
            actual = _get_nested(data, check.field)
            result = _evaluate_check(check, actual)
            results.append(result)

        checks_passed = sum(1 for r in results if r.passed)
        total = len(results)
        score = checks_passed / total if total > 0 else 0.0

        passed = score >= gate.threshold
        verdict = GateVerdict.PASS if passed else GateVerdict.FAIL

        # Determine compliance level
        if score >= 1.0:
            compliance = ComplianceLevel.FULL
        elif score > 0.0:
            compliance = ComplianceLevel.PARTIAL
        else:
            compliance = ComplianceLevel.NONE

        report = ComplianceReport(
            gate_id=gate.id,
            gate_name=gate.name,
            results=results,
            passed=passed,
            score=score,
            verdict=verdict,
            compliance_level=compliance,
        )

        # Emit events
        if passed:
            self._events.append(
                GatePassed(
                    gate_id=gate.id,
                    gate_name=gate.name,
                    score=score,
                    checks_passed=checks_passed,
                    checks_total=total,
                )
            )
        else:
            failures = [r.check_name for r in results if not r.passed]
            self._events.append(
                GateFailed(
                    gate_id=gate.id,
                    gate_name=gate.name,
                    score=score,
                    checks_passed=checks_passed,
                    checks_total=total,
                    failures=failures,
                )
            )

        return report

    @property
    def event_history(self) -> list[GatePassed | GateFailed]:
        return list(self._events)

    @staticmethod
    def _dict_to_gate(d: dict[str, Any]) -> QualityGate:
        """Convert a plain dict to a QualityGate entity."""
        checks = [
            GateCheck(
                name=c.get("name", ""),
                field=c.get("field", ""),
                operator=c.get("operator", "eq"),
                expected=c.get("expected"),
            )
            for c in d.get("checks", [])
        ]
        return QualityGate(
            id=d.get("id", ""),
            name=d.get("name", ""),
            checks=checks,
            threshold=d.get("threshold", 1.0),
        )
