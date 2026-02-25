"""QualityEngine — run data quality rules and compute quality scores.

Supports rule types: not_null, range, regex, unique.
Produces a QualityReport with per-field scores and an overall score.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from data_platform.domain.entities import QualityRule
from data_platform.domain.events import QualityChecked
from data_platform.domain.exceptions import QualityCheckError
from data_platform.domain.value_objects import QualityScore


@dataclass(frozen=True, slots=True)
class FieldResult:
    """Result of a single rule evaluation against a dataset."""

    rule_name: str
    field_name: str
    check_type: str
    total_records: int
    passed_records: int
    score: QualityScore

    @property
    def failed_records(self) -> int:
        return self.total_records - self.passed_records


@dataclass(slots=True)
class QualityReport:
    """Aggregated quality evaluation result."""

    field_results: list[FieldResult] = field(default_factory=list)
    overall_score: QualityScore = field(
        default_factory=lambda: QualityScore(value=1.0)
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.overall_score.passed

    @property
    def rule_count(self) -> int:
        return len(self.field_results)


class QualityEngine:
    """Evaluates data against quality rules and produces reports."""

    def __init__(self, threshold: float = 0.8) -> None:
        self._threshold = threshold
        self._events: list[QualityChecked] = []

    def evaluate(
        self, data: list[dict[str, Any]], rules: list[QualityRule]
    ) -> QualityReport:
        """Run each quality rule against the data rows and return a report.

        Args:
            data: List of row dictionaries.
            rules: List of QualityRule definitions to evaluate.

        Returns:
            QualityReport with per-field and overall scores.
        """
        if not data:
            report = QualityReport(
                overall_score=QualityScore(value=1.0, threshold=self._threshold),
                metadata={"record_count": 0, "rule_count": len(rules)},
            )
            self._emit_event(report)
            return report

        field_results: list[FieldResult] = []

        for rule in rules:
            try:
                result = self._evaluate_rule(data, rule)
                field_results.append(result)
            except Exception as exc:
                raise QualityCheckError(
                    f"Rule '{rule.name}' evaluation failed: {exc}",
                    rule_name=rule.name,
                ) from exc

        # Compute overall score as the average of all field scores
        if field_results:
            avg = sum(r.score.value for r in field_results) / len(field_results)
        else:
            avg = 1.0

        overall = QualityScore(value=round(avg, 6), threshold=self._threshold)

        report = QualityReport(
            field_results=field_results,
            overall_score=overall,
            metadata={
                "record_count": len(data),
                "rule_count": len(rules),
            },
        )

        self._emit_event(report)
        return report

    def _evaluate_rule(
        self, data: list[dict[str, Any]], rule: QualityRule
    ) -> FieldResult:
        """Evaluate a single rule against all rows."""
        total = len(data)
        check_type = rule.check_type.lower()

        if check_type == "not_null":
            passed = self._check_not_null(data, rule.field)
        elif check_type == "range":
            passed = self._check_range(data, rule)
        elif check_type == "regex":
            passed = self._check_regex(data, rule)
        elif check_type == "unique":
            passed = self._check_unique(data, rule.field)
        else:
            raise QualityCheckError(
                f"Unknown check type: {rule.check_type}",
                rule_name=rule.name,
            )

        score_value = passed / total if total > 0 else 1.0

        return FieldResult(
            rule_name=rule.name,
            field_name=rule.field,
            check_type=check_type,
            total_records=total,
            passed_records=passed,
            score=QualityScore(value=round(score_value, 6), threshold=self._threshold),
        )

    def _check_not_null(self, data: list[dict[str, Any]], field_name: str) -> int:
        """Count rows where field is present and not None/empty."""
        count = 0
        for row in data:
            value = row.get(field_name)
            if value is not None and value != "":
                count += 1
        return count

    def _check_range(self, data: list[dict[str, Any]], rule: QualityRule) -> int:
        """Count rows where field value falls within [min, max] range."""
        min_val = rule.parameters.get("min", float("-inf"))
        max_val = rule.parameters.get("max", float("inf"))
        count = 0
        for row in data:
            value = row.get(rule.field)
            if value is not None:
                try:
                    num = float(value)
                    if min_val <= num <= max_val:
                        count += 1
                except (TypeError, ValueError):
                    pass  # non-numeric values fail the check
        return count

    def _check_regex(self, data: list[dict[str, Any]], rule: QualityRule) -> int:
        """Count rows where field value matches the regex pattern."""
        pattern_str = rule.parameters.get("pattern", "")
        if not pattern_str:
            raise QualityCheckError(
                f"Regex rule '{rule.name}' missing 'pattern' parameter",
                rule_name=rule.name,
            )
        pattern = re.compile(pattern_str)
        count = 0
        for row in data:
            value = row.get(rule.field)
            if value is not None and pattern.search(str(value)):
                count += 1
        return count

    def _check_unique(self, data: list[dict[str, Any]], field_name: str) -> int:
        """Count of records, minus duplicates. Returns number of unique values.

        Unique check: total records pass if ALL values are unique.
        Score = unique_count / total_count.
        """
        values: list[Any] = []
        for row in data:
            value = row.get(field_name)
            if value is not None:
                values.append(value)

        if not values:
            return len(data)

        unique_count = len(set(values))
        # All rows pass if unique, proportional otherwise
        # Return number of records that "pass" — i.e. unique_count
        return unique_count

    def _emit_event(self, report: QualityReport) -> None:
        self._events.append(
            QualityChecked(
                rule_count=report.rule_count,
                overall_score=report.overall_score.value,
                passed=report.passed,
                details={
                    r.rule_name: {
                        "score": r.score.value,
                        "passed": r.score.passed,
                        "total": r.total_records,
                        "passed_records": r.passed_records,
                    }
                    for r in report.field_results
                },
            )
        )

    @property
    def events(self) -> list[QualityChecked]:
        return list(self._events)
