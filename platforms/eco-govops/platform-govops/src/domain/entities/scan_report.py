"""Scan report entity for the Governance Operations Platform.

A scan report captures the full results of a governance scan cycle — which
modules were analysed, what issues were found, and their severities.  The
report aggregates individual Finding records and exposes convenience methods
for severity-based analysis.
"""
from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import structlog
from pydantic import BaseModel, Field

from domain.value_objects.severity import Severity

logger = structlog.get_logger(__name__)


class ScanStatus(str, enum.Enum):
    """Lifecycle status of a scan report."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(slots=True)
class Finding:
    """A single issue discovered during a governance scan.

    Attributes:
        finding_id: Unique identifier for this finding.
        module_id: Module in which the issue was detected.
        rule_id: The governance rule that was violated.
        severity: Severity classification.
        title: Short one-line summary.
        description: Full description of the issue.
        location: File path, line number, or resource locator.
        remediation_hint: Suggested fix or documentation link.
        auto_fixable: Whether the platform can remediate automatically.
        fixed: Whether the finding has already been remediated.
        metadata: Arbitrary extension data.
    """

    finding_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    module_id: str = ""
    rule_id: str = ""
    severity: Severity = Severity.INFO
    title: str = ""
    description: str = ""
    location: str = ""
    remediation_hint: str = ""
    auto_fixable: bool = False
    fixed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def mark_fixed(self) -> None:
        """Flag this finding as remediated."""
        self.fixed = True
        logger.debug(
            "finding_fixed",
            finding_id=self.finding_id,
            rule_id=self.rule_id,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        return {
            "finding_id": self.finding_id,
            "module_id": self.module_id,
            "rule_id": self.rule_id,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "location": self.location,
            "remediation_hint": self.remediation_hint,
            "auto_fixable": self.auto_fixable,
            "fixed": self.fixed,
            "metadata": self.metadata,
        }


class ScanReport(BaseModel):
    """Domain entity representing the output of a governance scan.

    Attributes:
        report_id: Unique identifier (UUID-4 string).
        cycle_id: Governance cycle that initiated this scan.
        scanner_type: Identifier of the scanner engine used.
        started_at: UTC timestamp when the scan began.
        completed_at: UTC timestamp when the scan finished (None while running).
        modules_scanned: Count of modules analysed.
        issues_found: Total findings discovered.
        issues_fixed: Findings remediated automatically during the scan.
        findings: Ordered list of individual Finding records.
        status: Current lifecycle status.
    """

    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    cycle_id: str = ""
    scanner_type: str = ""
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    modules_scanned: int = 0
    issues_found: int = 0
    issues_fixed: int = 0
    findings: list[Finding] = Field(default_factory=list)
    status: ScanStatus = ScanStatus.PENDING

    model_config = {"frozen": False, "populate_by_name": True, "arbitrary_types_allowed": True}

    # -- mutators -----------------------------------------------------------

    def add_finding(self, finding: Finding) -> None:
        """Append a finding to the report and update counters.

        Args:
            finding: The Finding to add.
        """
        self.findings.append(finding)
        self.issues_found = len(self.findings)
        self.issues_fixed = sum(1 for f in self.findings if f.fixed)
        logger.debug(
            "finding_added",
            report_id=self.report_id,
            finding_id=finding.finding_id,
            severity=finding.severity.value,
            total_findings=self.issues_found,
        )

    def mark_running(self) -> None:
        """Transition the report to RUNNING status."""
        self.status = ScanStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)
        logger.info("scan_running", report_id=self.report_id)

    def mark_completed(self) -> None:
        """Transition the report to COMPLETED and record the end timestamp."""
        self.status = ScanStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        self.issues_found = len(self.findings)
        self.issues_fixed = sum(1 for f in self.findings if f.fixed)
        logger.info(
            "scan_completed",
            report_id=self.report_id,
            modules_scanned=self.modules_scanned,
            issues_found=self.issues_found,
            issues_fixed=self.issues_fixed,
        )

    def mark_failed(self, reason: str = "") -> None:
        """Transition the report to FAILED status."""
        self.status = ScanStatus.FAILED
        self.completed_at = datetime.now(timezone.utc)
        logger.error("scan_failed", report_id=self.report_id, reason=reason)

    # -- queries ------------------------------------------------------------

    def severity_counts(self) -> dict[Severity, int]:
        """Return a mapping of severity -> count of open (unfixed) findings."""
        counts: dict[Severity, int] = {sev: 0 for sev in Severity}
        for finding in self.findings:
            if not finding.fixed:
                counts[finding.severity] = counts.get(finding.severity, 0) + 1
        return counts

    def findings_by_severity(self, severity: Severity) -> list[Finding]:
        """Return all findings matching *severity* (including fixed ones)."""
        return [f for f in self.findings if f.severity == severity]

    def open_findings(self) -> list[Finding]:
        """Return all findings that have not yet been remediated."""
        return [f for f in self.findings if not f.fixed]

    def auto_fixable_findings(self) -> list[Finding]:
        """Return unfixed findings that the platform can remediate."""
        return [f for f in self.findings if f.auto_fixable and not f.fixed]

    def has_blocking_findings(self) -> bool:
        """Return True if any unfixed finding is CRITICAL or HIGH."""
        return any(
            f.severity.is_blocking and not f.fixed
            for f in self.findings
        )

    def summary(self) -> dict[str, Any]:
        """Return a concise dictionary summary for dashboards and logging."""
        sev_counts = self.severity_counts()
        duration_seconds: float | None = None
        if self.completed_at and self.started_at:
            duration_seconds = (self.completed_at - self.started_at).total_seconds()

        return {
            "report_id": self.report_id,
            "cycle_id": self.cycle_id,
            "scanner_type": self.scanner_type,
            "status": self.status.value,
            "modules_scanned": self.modules_scanned,
            "issues_found": self.issues_found,
            "issues_fixed": self.issues_fixed,
            "open_issues": self.issues_found - self.issues_fixed,
            "severity_counts": {s.value: c for s, c in sev_counts.items()},
            "has_blockers": self.has_blocking_findings(),
            "duration_seconds": duration_seconds,
        }

    def merge(self, other: ScanReport) -> None:
        """Merge findings from *other* report into this one.

        Useful when aggregating results from multiple scanner engines into a
        single consolidated report.
        """
        for finding in other.findings:
            self.add_finding(finding)
        self.modules_scanned += other.modules_scanned
        logger.info(
            "scan_reports_merged",
            target_id=self.report_id,
            source_id=other.report_id,
            new_total_findings=self.issues_found,
        )
