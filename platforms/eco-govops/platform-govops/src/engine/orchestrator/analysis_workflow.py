"""Analysis workflow — state-machine-driven governance cycle orchestrator.

Coordinates the full lifecycle of a governance analysis cycle through
well-defined phases:

    PENDING → SCANNING → ANALYSING → ENFORCING → REMEDIATING → REPORTING → COMPLETED

Each phase delegates to the appropriate engine subsystem (Scanner, Analyzer,
Enforcer) and records structured evidence at every transition.

@GL-governed
@GL-layer: GL30-49
@GL-semantic: governance-orchestration
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import uuid
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class WorkflowState(StrEnum):
    """Lifecycle states for a governance analysis workflow."""

    PENDING = "pending"
    SCANNING = "scanning"
    ANALYSING = "analysing"
    ENFORCING = "enforcing"
    REMEDIATING = "remediating"
    REPORTING = "reporting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Valid state transitions
_TRANSITIONS: dict[WorkflowState, frozenset[WorkflowState]] = {
    WorkflowState.PENDING: frozenset(
        {WorkflowState.SCANNING, WorkflowState.CANCELLED, WorkflowState.FAILED}
    ),
    WorkflowState.SCANNING: frozenset(
        {WorkflowState.ANALYSING, WorkflowState.FAILED, WorkflowState.CANCELLED}
    ),
    WorkflowState.ANALYSING: frozenset(
        {WorkflowState.ENFORCING, WorkflowState.REPORTING, WorkflowState.FAILED, WorkflowState.CANCELLED}
    ),
    WorkflowState.ENFORCING: frozenset(
        {WorkflowState.REMEDIATING, WorkflowState.REPORTING, WorkflowState.FAILED, WorkflowState.CANCELLED}
    ),
    WorkflowState.REMEDIATING: frozenset(
        {WorkflowState.REPORTING, WorkflowState.FAILED, WorkflowState.CANCELLED}
    ),
    WorkflowState.REPORTING: frozenset(
        {WorkflowState.COMPLETED, WorkflowState.FAILED}
    ),
    WorkflowState.COMPLETED: frozenset(),
    WorkflowState.FAILED: frozenset(),
    WorkflowState.CANCELLED: frozenset(),
}


class CyclePhase(StrEnum):
    """Individual phases within the analysis workflow."""

    SCAN = "scan"
    ANALYSE = "analyse"
    ENFORCE = "enforce"
    REMEDIATE = "remediate"
    REPORT = "report"


# ---------------------------------------------------------------------------
# Configuration & result models
# ---------------------------------------------------------------------------


class WorkflowConfig(BaseModel):
    """Configuration for a single governance analysis cycle.

    Attributes:
        name: Human-readable cycle name.
        description: Optional extended description.
        modules: Module IDs to include (empty = all).
        auto_enforce: Automatically enforce findings above threshold.
        auto_remediate: Attempt automatic remediation of fixable violations.
        severity_threshold: Minimum severity for enforcement (info|warning|error|critical).
        max_duration_seconds: Hard timeout for the entire cycle.
        tags: Free-form key-value metadata.
    """

    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    modules: list[str] = Field(default_factory=list)
    auto_enforce: bool = False
    auto_remediate: bool = False
    severity_threshold: str = Field(default="warning")
    max_duration_seconds: int = Field(default=3600, ge=60, le=86400)
    tags: dict[str, str] = Field(default_factory=dict)


class PhaseResult(BaseModel):
    """Outcome of a single workflow phase.

    Attributes:
        phase: Which phase ran.
        status: Terminal status of the phase (completed | failed | skipped).
        started_at: When the phase started.
        completed_at: When the phase finished.
        duration_seconds: Wall-clock time for the phase.
        output: Arbitrary structured output from the phase.
        error: Error message if the phase failed.
    """

    phase: CyclePhase
    status: str = "completed"
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    duration_seconds: float = 0.0
    output: dict[str, Any] = Field(default_factory=dict)
    error: str = ""


class WorkflowResult(BaseModel):
    """Aggregated outcome of a completed analysis workflow.

    Attributes:
        cycle_id: Unique cycle identifier.
        config: Configuration the cycle was run with.
        state: Terminal lifecycle state.
        phases: Results from each executed phase.
        started_at: Cycle start time.
        completed_at: Cycle completion time.
        duration_seconds: Total wall-clock time.
        modules_scanned: Count of modules that were scanned.
        findings_count: Total findings discovered.
        violations_count: Policy violations detected.
        remediations_applied: Auto-remediations that succeeded.
        gate_blocked: Whether any gate blocked progression.
        compliance_rate: Overall compliance rate (0-100).
        evidence_chain_hash: Final evidence chain hash for integrity verification.
    """

    cycle_id: str
    config: WorkflowConfig
    state: WorkflowState
    phases: list[PhaseResult] = Field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_seconds: float = 0.0
    modules_scanned: int = 0
    findings_count: int = 0
    violations_count: int = 0
    remediations_applied: int = 0
    gate_blocked: bool = False
    compliance_rate: float = 0.0
    evidence_chain_hash: str = ""

    def summary(self) -> dict[str, Any]:
        """Return a concise summary for dashboards and logging."""
        return {
            "cycle_id": self.cycle_id,
            "name": self.config.name,
            "state": self.state.value,
            "duration_seconds": self.duration_seconds,
            "modules_scanned": self.modules_scanned,
            "findings_count": self.findings_count,
            "violations_count": self.violations_count,
            "remediations_applied": self.remediations_applied,
            "gate_blocked": self.gate_blocked,
            "compliance_rate": self.compliance_rate,
            "phases_completed": sum(
                1 for p in self.phases if p.status == "completed"
            ),
            "phases_total": len(self.phases),
        }


# ---------------------------------------------------------------------------
# AnalysisWorkflow
# ---------------------------------------------------------------------------


class AnalysisWorkflow:
    """State-machine-driven governance analysis workflow.

    Orchestrates the full cycle of scan → analyse → enforce → remediate →
    report, delegating to engine subsystems and recording evidence at each
    transition.

    Usage::

        config = WorkflowConfig(name="nightly-governance")
        workflow = AnalysisWorkflow(config)
        result = await workflow.run(
            scanner=module_scanner,
            analyzer=compliance_analyzer,
            enforcer=policy_enforcer,
        )
    """

    def __init__(
        self,
        config: WorkflowConfig,
        *,
        cycle_id: str | None = None,
    ) -> None:
        self._cycle_id = cycle_id or f"CYCLE-{uuid.uuid4().hex[:12]}"
        self._config = config
        self._state = WorkflowState.PENDING
        self._phases: list[PhaseResult] = []
        self._started_at: datetime | None = None
        self._completed_at: datetime | None = None
        self._evidence_hashes: list[str] = []
        self._scan_output: dict[str, Any] = {}
        self._analysis_output: dict[str, Any] = {}
        self._enforcement_output: dict[str, Any] = {}
        self._remediation_output: dict[str, Any] = {}
        self._report_output: dict[str, Any] = {}

        logger.info(
            "workflow_created",
            cycle_id=self._cycle_id,
            name=config.name,
            modules=len(config.modules),
        )

    # -- properties ---------------------------------------------------------

    @property
    def cycle_id(self) -> str:
        return self._cycle_id

    @property
    def state(self) -> WorkflowState:
        return self._state

    @property
    def config(self) -> WorkflowConfig:
        return self._config

    @property
    def phases(self) -> list[PhaseResult]:
        return list(self._phases)

    @property
    def is_terminal(self) -> bool:
        """True if the workflow has reached a terminal state."""
        return self._state in {
            WorkflowState.COMPLETED,
            WorkflowState.FAILED,
            WorkflowState.CANCELLED,
        }

    # -- state transitions --------------------------------------------------

    def _transition(self, target: WorkflowState) -> None:
        """Validate and perform a state transition, recording evidence."""
        allowed = _TRANSITIONS.get(self._state, frozenset())
        if target not in allowed:
            raise InvalidTransitionError(
                f"Cannot transition from {self._state.value} to {target.value}. "
                f"Allowed: {', '.join(s.value for s in allowed) or 'none'}"
            )
        previous = self._state
        self._state = target
        # Record evidence hash for the transition
        evidence_payload = json.dumps(
            {
                "cycle_id": self._cycle_id,
                "from": previous.value,
                "to": target.value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "parent_hash": self._evidence_hashes[-1] if self._evidence_hashes else "",
            },
            sort_keys=True,
        )
        self._evidence_hashes.append(
            hashlib.sha256(evidence_payload.encode()).hexdigest()
        )
        logger.info(
            "workflow_state_transition",
            cycle_id=self._cycle_id,
            from_state=previous.value,
            to_state=target.value,
        )

    # -- main execution -----------------------------------------------------

    async def run(
        self,
        *,
        scanner: Any = None,
        analyzer: Any = None,
        enforcer: Any = None,
    ) -> WorkflowResult:
        """Execute the full analysis workflow.

        Each phase is run in sequence.  If ``auto_enforce`` is False the
        enforcing phase is skipped; likewise ``auto_remediate`` controls the
        remediation phase.

        Args:
            scanner: A ``ModuleScanner`` instance (or compatible).
            analyzer: A ``ComplianceAnalyzer`` instance (or compatible).
            enforcer: A ``PolicyEnforcer`` instance (or compatible).

        Returns:
            A :class:`WorkflowResult` summarising the entire cycle.
        """
        self._started_at = datetime.now(timezone.utc)

        try:
            await asyncio.wait_for(
                self._run_phases(scanner=scanner, analyzer=analyzer, enforcer=enforcer),
                timeout=self._config.max_duration_seconds,
            )
            # Terminal
            self._transition(WorkflowState.COMPLETED)

        except asyncio.TimeoutError:
            self._state = WorkflowState.FAILED
            logger.error(
                "workflow_timeout",
                cycle_id=self._cycle_id,
                max_duration=self._config.max_duration_seconds,
            )
        except WorkflowCancelledError:
            self._state = WorkflowState.CANCELLED
            logger.warning("workflow_cancelled", cycle_id=self._cycle_id)
        except Exception as exc:
            self._state = WorkflowState.FAILED
            logger.error(
                "workflow_failed",
                cycle_id=self._cycle_id,
                error=str(exc),
            )

        self._completed_at = datetime.now(timezone.utc)
        return self._build_result()

    async def _run_phases(
        self,
        *,
        scanner: Any = None,
        analyzer: Any = None,
        enforcer: Any = None,
    ) -> None:
        """Execute all workflow phases in sequence."""
        # Phase 1: Scan
        await self._run_scan_phase(scanner)

        # Phase 2: Analyse
        await self._run_analysis_phase(analyzer)

        # Phase 3: Enforce (optional)
        if self._config.auto_enforce:
            await self._run_enforcement_phase(enforcer)

        # Phase 4: Remediate (optional)
        if self._config.auto_remediate and self._enforcement_output.get("violations", 0) > 0:
            await self._run_remediation_phase(enforcer)

        # Phase 5: Report
        await self._run_report_phase()

    # -- phase runners ------------------------------------------------------

    async def _run_scan_phase(self, scanner: Any) -> None:
        """Phase 1: Scan modules for governance compliance."""
        self._transition(WorkflowState.SCANNING)
        phase_start = datetime.now(timezone.utc)

        output: dict[str, Any] = {}
        error = ""
        status = "completed"

        try:
            if scanner is not None and hasattr(scanner, "scan_all"):
                report = await scanner.scan_all()
                output = {
                    "scan_id": report.scan_id,
                    "total_modules": report.total_modules,
                    "passed": report.summary.passed,
                    "failed": report.summary.failed,
                    "warnings": report.summary.warnings,
                    "pass_rate": report.summary.pass_rate,
                    "violations_count": len(report.violations),
                    "drift_count": len(report.drift_detected),
                    "findings_count": len(report.semantic_findings),
                }
            else:
                output = {
                    "scan_id": f"SCAN-{uuid.uuid4().hex[:8]}",
                    "total_modules": len(self._config.modules),
                    "passed": len(self._config.modules),
                    "failed": 0,
                    "warnings": 0,
                    "pass_rate": 100.0,
                    "violations_count": 0,
                    "drift_count": 0,
                    "findings_count": 0,
                }

            self._scan_output = output

        except Exception as exc:
            error = f"Scan phase failed: {exc}"
            status = "failed"
            logger.error("scan_phase_failed", cycle_id=self._cycle_id, error=str(exc))
            raise

        finally:
            phase_end = datetime.now(timezone.utc)
            self._phases.append(
                PhaseResult(
                    phase=CyclePhase.SCAN,
                    status=status,
                    started_at=phase_start,
                    completed_at=phase_end,
                    duration_seconds=(phase_end - phase_start).total_seconds(),
                    output=output,
                    error=error,
                )
            )

    async def _run_analysis_phase(self, analyzer: Any) -> None:
        """Phase 2: Analyse compliance distribution and risk hotspots."""
        self._transition(WorkflowState.ANALYSING)
        phase_start = datetime.now(timezone.utc)

        output: dict[str, Any] = {}
        error = ""
        status = "completed"

        try:
            if analyzer is not None and hasattr(analyzer, "generate_report"):
                report = await analyzer.generate_report()
                output = {
                    "total_modules": report.distribution.total_modules,
                    "compliance_rate": report.distribution.compliance_rate,
                    "hotspot_count": len(report.hotspots),
                    "trend_points": len(report.trend),
                    "worst_layer": report.summary.get("worst_layer", "n/a"),
                }
            else:
                scan = self._scan_output
                output = {
                    "total_modules": scan.get("total_modules", 0),
                    "compliance_rate": scan.get("pass_rate", 0.0),
                    "hotspot_count": 0,
                    "trend_points": 0,
                    "worst_layer": "n/a",
                }

            self._analysis_output = output

        except Exception as exc:
            error = f"Analysis phase failed: {exc}"
            status = "failed"
            logger.error("analysis_phase_failed", cycle_id=self._cycle_id, error=str(exc))
            raise

        finally:
            phase_end = datetime.now(timezone.utc)
            self._phases.append(
                PhaseResult(
                    phase=CyclePhase.ANALYSE,
                    status=status,
                    started_at=phase_start,
                    completed_at=phase_end,
                    duration_seconds=(phase_end - phase_start).total_seconds(),
                    output=output,
                    error=error,
                )
            )

    async def _run_enforcement_phase(self, enforcer: Any) -> None:
        """Phase 3: Enforce governance policies against scan results."""
        self._transition(WorkflowState.ENFORCING)
        phase_start = datetime.now(timezone.utc)

        output: dict[str, Any] = {}
        error = ""
        status = "completed"

        try:
            if enforcer is not None and hasattr(enforcer, "enforce"):
                context = {
                    "summary": self._scan_output,
                    "analysis": self._analysis_output,
                }
                result = await enforcer.enforce(context, cycle_id=self._cycle_id)
                output = {
                    "enforcement_id": result.enforcement_id,
                    "total_rules": result.total_rules,
                    "passed": len(result.passed_rules),
                    "violations": len(result.violations),
                    "skipped": len(result.skipped_rules),
                    "gate_blocked": result.gate_blocked,
                    "actions_taken": len(result.enforcement_actions),
                }
            else:
                output = {
                    "enforcement_id": str(uuid.uuid4()),
                    "total_rules": 0,
                    "passed": 0,
                    "violations": 0,
                    "skipped": 0,
                    "gate_blocked": False,
                    "actions_taken": 0,
                }

            self._enforcement_output = output

        except Exception as exc:
            error = f"Enforcement phase failed: {exc}"
            status = "failed"
            logger.error("enforcement_phase_failed", cycle_id=self._cycle_id, error=str(exc))
            raise

        finally:
            phase_end = datetime.now(timezone.utc)
            self._phases.append(
                PhaseResult(
                    phase=CyclePhase.ENFORCE,
                    status=status,
                    started_at=phase_start,
                    completed_at=phase_end,
                    duration_seconds=(phase_end - phase_start).total_seconds(),
                    output=output,
                    error=error,
                )
            )

    async def _run_remediation_phase(self, enforcer: Any) -> None:
        """Phase 4: Attempt automatic remediation of fixable violations."""
        self._transition(WorkflowState.REMEDIATING)
        phase_start = datetime.now(timezone.utc)

        output: dict[str, Any] = {}
        error = ""
        status = "completed"

        try:
            remediations_attempted = 0
            remediations_applied = 0
            remediations_failed = 0

            if enforcer is not None and hasattr(enforcer, "rules"):
                for rule in enforcer.rules:
                    if rule.auto_fix:
                        remediations_attempted += 1
                        try:
                            if hasattr(rule, "apply_fix"):
                                await rule.apply_fix()
                            remediations_applied += 1
                        except Exception as fix_exc:
                            remediations_failed += 1
                            logger.warning(
                                "remediation_failed",
                                cycle_id=self._cycle_id,
                                error=str(fix_exc),
                            )

            output = {
                "remediations_attempted": remediations_attempted,
                "remediations_applied": remediations_applied,
                "remediations_failed": remediations_failed,
            }
            self._remediation_output = output

        except Exception as exc:
            error = f"Remediation phase failed: {exc}"
            status = "failed"
            logger.error("remediation_phase_failed", cycle_id=self._cycle_id, error=str(exc))
            raise

        finally:
            phase_end = datetime.now(timezone.utc)
            self._phases.append(
                PhaseResult(
                    phase=CyclePhase.REMEDIATE,
                    status=status,
                    started_at=phase_start,
                    completed_at=phase_end,
                    duration_seconds=(phase_end - phase_start).total_seconds(),
                    output=output,
                    error=error,
                )
            )

    async def _run_report_phase(self) -> None:
        """Phase 5: Compile final governance report."""
        self._transition(WorkflowState.REPORTING)
        phase_start = datetime.now(timezone.utc)

        output: dict[str, Any] = {}
        error = ""
        status = "completed"

        try:
            scan = self._scan_output
            analysis = self._analysis_output
            enforcement = self._enforcement_output
            remediation = self._remediation_output

            output = {
                "cycle_id": self._cycle_id,
                "scan_summary": {
                    "total_modules": scan.get("total_modules", 0),
                    "pass_rate": scan.get("pass_rate", 0.0),
                    "violations": scan.get("violations_count", 0),
                    "drift_detected": scan.get("drift_count", 0),
                },
                "analysis_summary": {
                    "compliance_rate": analysis.get("compliance_rate", 0.0),
                    "hotspot_count": analysis.get("hotspot_count", 0),
                },
                "enforcement_summary": {
                    "total_rules": enforcement.get("total_rules", 0),
                    "violations": enforcement.get("violations", 0),
                    "gate_blocked": enforcement.get("gate_blocked", False),
                },
                "remediation_summary": {
                    "applied": remediation.get("remediations_applied", 0),
                    "failed": remediation.get("remediations_failed", 0),
                },
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
            self._report_output = output

        except Exception as exc:
            error = f"Report phase failed: {exc}"
            status = "failed"
            logger.error("report_phase_failed", cycle_id=self._cycle_id, error=str(exc))
            raise

        finally:
            phase_end = datetime.now(timezone.utc)
            self._phases.append(
                PhaseResult(
                    phase=CyclePhase.REPORT,
                    status=status,
                    started_at=phase_start,
                    completed_at=phase_end,
                    duration_seconds=(phase_end - phase_start).total_seconds(),
                    output=output,
                    error=error,
                )
            )

    # -- cancellation -------------------------------------------------------

    async def cancel(self) -> None:
        """Request cancellation of the running workflow."""
        if self.is_terminal:
            logger.warning(
                "workflow_cancel_ignored",
                cycle_id=self._cycle_id,
                state=self._state.value,
            )
            return
        raise WorkflowCancelledError(f"Cycle {self._cycle_id} cancelled by user")

    # -- result builder -----------------------------------------------------

    def _build_result(self) -> WorkflowResult:
        """Assemble the final WorkflowResult from accumulated phase data."""
        duration = 0.0
        if self._started_at and self._completed_at:
            duration = (self._completed_at - self._started_at).total_seconds()

        scan = self._scan_output
        enforcement = self._enforcement_output
        remediation = self._remediation_output
        analysis = self._analysis_output

        # Build final evidence chain hash from accumulated transition hashes
        evidence_chain_hash = ""
        if self._evidence_hashes:
            chain_payload = json.dumps(self._evidence_hashes, sort_keys=True)
            evidence_chain_hash = hashlib.sha256(chain_payload.encode()).hexdigest()

        return WorkflowResult(
            cycle_id=self._cycle_id,
            config=self._config,
            state=self._state,
            phases=list(self._phases),
            started_at=self._started_at,
            completed_at=self._completed_at,
            duration_seconds=round(duration, 4),
            modules_scanned=scan.get("total_modules", 0),
            findings_count=(
                scan.get("findings_count", 0)
                + scan.get("violations_count", 0)
            ),
            violations_count=enforcement.get("violations", 0),
            remediations_applied=remediation.get("remediations_applied", 0),
            gate_blocked=enforcement.get("gate_blocked", False),
            compliance_rate=analysis.get("compliance_rate", 0.0),
            evidence_chain_hash=evidence_chain_hash,
        )


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class InvalidTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""


class WorkflowCancelledError(Exception):
    """Raised to signal workflow cancellation."""
