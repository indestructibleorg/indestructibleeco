"""Comprehensive tests for the AnalysisWorkflow orchestrator.

Covers the full state-machine lifecycle, phase execution, error handling,
cancellation, and integration with scanner/analyzer/enforcer subsystems.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from engine.orchestrator.analysis_workflow import (
    AnalysisWorkflow,
    CyclePhase,
    InvalidTransitionError,
    PhaseResult,
    WorkflowCancelledError,
    WorkflowConfig,
    WorkflowResult,
    WorkflowState,
    _TRANSITIONS,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def basic_config() -> WorkflowConfig:
    """Minimal workflow config for testing."""
    return WorkflowConfig(name="test-cycle")


@pytest.fixture
def full_config() -> WorkflowConfig:
    """Config with all enforcement/remediation enabled."""
    return WorkflowConfig(
        name="full-cycle",
        description="Full governance cycle",
        modules=["mod-a", "mod-b", "mod-c"],
        auto_enforce=True,
        auto_remediate=True,
        severity_threshold="error",
        max_duration_seconds=1800,
        tags={"env": "test"},
    )


@pytest.fixture
def mock_scan_report() -> MagicMock:
    """Fake scan report returned by ModuleScanner.scan_all()."""
    summary = MagicMock()
    summary.passed = 8
    summary.failed = 1
    summary.warnings = 1
    summary.pass_rate = 80.0

    report = MagicMock()
    report.scan_id = "SCAN-TEST-001"
    report.total_modules = 10
    report.summary = summary
    report.violations = [MagicMock()]
    report.drift_detected = [MagicMock(), MagicMock()]
    report.semantic_findings = [MagicMock(), MagicMock(), MagicMock()]
    return report


@pytest.fixture
def mock_scanner(mock_scan_report: MagicMock) -> AsyncMock:
    """Scanner that returns the fake scan report."""
    scanner = AsyncMock()
    scanner.scan_all = AsyncMock(return_value=mock_scan_report)
    return scanner


@pytest.fixture
def mock_compliance_report() -> MagicMock:
    """Fake compliance report returned by ComplianceAnalyzer.generate_report()."""
    dist = MagicMock()
    dist.total_modules = 10
    dist.compliance_rate = 85.0

    report = MagicMock()
    report.distribution = dist
    report.hotspots = [MagicMock(), MagicMock()]
    report.trend = [MagicMock()]
    report.summary = {"worst_layer": "GL30-39"}
    return report


@pytest.fixture
def mock_analyzer(mock_compliance_report: MagicMock) -> AsyncMock:
    """Analyzer that returns the fake compliance report."""
    analyzer = AsyncMock()
    analyzer.generate_report = AsyncMock(return_value=mock_compliance_report)
    return analyzer


@pytest.fixture
def mock_enforcement_result() -> MagicMock:
    """Fake enforcement result returned by PolicyEnforcer.enforce()."""
    violation = MagicMock()
    violation.severity = MagicMock()
    violation.severity.is_blocking = True

    result = MagicMock()
    result.enforcement_id = "ENF-TEST-001"
    result.total_rules = 5
    result.passed_rules = [MagicMock(), MagicMock(), MagicMock()]
    result.violations = [violation]
    result.skipped_rules = [MagicMock()]
    result.gate_blocked = True
    result.enforcement_actions = [{"action": "block"}]
    return result


@pytest.fixture
def mock_enforcer(mock_enforcement_result: MagicMock) -> AsyncMock:
    """Enforcer that returns the fake enforcement result."""
    rule = MagicMock()
    rule.auto_fix = True
    rule.apply_fix = AsyncMock()

    enforcer = AsyncMock()
    enforcer.enforce = AsyncMock(return_value=mock_enforcement_result)
    enforcer.rules = [rule, rule]
    return enforcer


# ===================================================================
# WorkflowConfig tests
# ===================================================================


class TestWorkflowConfig:
    """Test WorkflowConfig validation and defaults."""

    def test_minimal_config(self) -> None:
        config = WorkflowConfig(name="my-cycle")
        assert config.name == "my-cycle"
        assert config.description == ""
        assert config.modules == []
        assert config.auto_enforce is False
        assert config.auto_remediate is False
        assert config.severity_threshold == "warning"
        assert config.max_duration_seconds == 3600
        assert config.tags == {}

    def test_full_config(self) -> None:
        config = WorkflowConfig(
            name="full",
            description="desc",
            modules=["a", "b"],
            auto_enforce=True,
            auto_remediate=True,
            severity_threshold="critical",
            max_duration_seconds=7200,
            tags={"k": "v"},
        )
        assert config.auto_enforce is True
        assert config.auto_remediate is True
        assert len(config.modules) == 2

    def test_name_required(self) -> None:
        with pytest.raises(Exception):
            WorkflowConfig(name="")

    def test_duration_bounds(self) -> None:
        with pytest.raises(Exception):
            WorkflowConfig(name="x", max_duration_seconds=10)  # < 60

        with pytest.raises(Exception):
            WorkflowConfig(name="x", max_duration_seconds=100_000)  # > 86400


# ===================================================================
# WorkflowState tests
# ===================================================================


class TestWorkflowState:
    """Test state enum values and transition table."""

    def test_all_states_exist(self) -> None:
        expected = {
            "pending", "scanning", "analysing", "enforcing",
            "remediating", "reporting", "completed", "failed", "cancelled",
        }
        actual = {s.value for s in WorkflowState}
        assert actual == expected

    def test_terminal_states_have_no_transitions(self) -> None:
        for state in (WorkflowState.COMPLETED, WorkflowState.FAILED, WorkflowState.CANCELLED):
            assert _TRANSITIONS[state] == frozenset()

    def test_all_states_in_transition_table(self) -> None:
        for state in WorkflowState:
            assert state in _TRANSITIONS

    def test_happy_path_transitions_are_valid(self) -> None:
        """The standard happy path: pending → scanning → analysing → enforcing → remediating → reporting → completed."""
        path = [
            (WorkflowState.PENDING, WorkflowState.SCANNING),
            (WorkflowState.SCANNING, WorkflowState.ANALYSING),
            (WorkflowState.ANALYSING, WorkflowState.ENFORCING),
            (WorkflowState.ENFORCING, WorkflowState.REMEDIATING),
            (WorkflowState.REMEDIATING, WorkflowState.REPORTING),
            (WorkflowState.REPORTING, WorkflowState.COMPLETED),
        ]
        for from_state, to_state in path:
            assert to_state in _TRANSITIONS[from_state], (
                f"{from_state.value} → {to_state.value} should be valid"
            )

    def test_every_non_terminal_state_can_fail(self) -> None:
        for state, targets in _TRANSITIONS.items():
            if state in (WorkflowState.COMPLETED, WorkflowState.FAILED, WorkflowState.CANCELLED):
                continue
            assert WorkflowState.FAILED in targets, (
                f"State {state.value} should allow transition to FAILED"
            )


# ===================================================================
# PhaseResult tests
# ===================================================================


class TestPhaseResult:
    """Test PhaseResult model."""

    def test_defaults(self) -> None:
        pr = PhaseResult(phase=CyclePhase.SCAN)
        assert pr.phase == CyclePhase.SCAN
        assert pr.status == "completed"
        assert pr.error == ""
        assert pr.output == {}
        assert isinstance(pr.started_at, datetime)

    def test_failed_phase(self) -> None:
        pr = PhaseResult(
            phase=CyclePhase.ENFORCE,
            status="failed",
            error="connection timeout",
            duration_seconds=5.5,
        )
        assert pr.status == "failed"
        assert "timeout" in pr.error
        assert pr.duration_seconds == 5.5


# ===================================================================
# WorkflowResult tests
# ===================================================================


class TestWorkflowResult:
    """Test WorkflowResult model and summary method."""

    def test_summary_fields(self) -> None:
        result = WorkflowResult(
            cycle_id="CYC-001",
            config=WorkflowConfig(name="test"),
            state=WorkflowState.COMPLETED,
            modules_scanned=10,
            findings_count=3,
            violations_count=1,
            compliance_rate=85.0,
            phases=[
                PhaseResult(phase=CyclePhase.SCAN),
                PhaseResult(phase=CyclePhase.ANALYSE),
            ],
        )
        summary = result.summary()
        assert summary["cycle_id"] == "CYC-001"
        assert summary["name"] == "test"
        assert summary["state"] == "completed"
        assert summary["modules_scanned"] == 10
        assert summary["findings_count"] == 3
        assert summary["violations_count"] == 1
        assert summary["compliance_rate"] == 85.0
        assert summary["phases_completed"] == 2
        assert summary["phases_total"] == 2


# ===================================================================
# AnalysisWorkflow creation tests
# ===================================================================


class TestWorkflowCreation:
    """Test workflow construction and initial state."""

    def test_default_creation(self, basic_config: WorkflowConfig) -> None:
        wf = AnalysisWorkflow(basic_config)
        assert wf.state == WorkflowState.PENDING
        assert wf.config.name == "test-cycle"
        assert wf.cycle_id.startswith("CYCLE-")
        assert wf.phases == []
        assert wf.is_terminal is False

    def test_custom_cycle_id(self, basic_config: WorkflowConfig) -> None:
        wf = AnalysisWorkflow(basic_config, cycle_id="MY-CYCLE-42")
        assert wf.cycle_id == "MY-CYCLE-42"

    def test_properties_readonly(self, basic_config: WorkflowConfig) -> None:
        wf = AnalysisWorkflow(basic_config)
        assert isinstance(wf.cycle_id, str)
        assert isinstance(wf.state, WorkflowState)
        assert isinstance(wf.config, WorkflowConfig)
        assert isinstance(wf.phases, list)


# ===================================================================
# State transition tests
# ===================================================================


class TestStateTransitions:
    """Test the state machine transition logic."""

    def test_valid_transition(self, basic_config: WorkflowConfig) -> None:
        wf = AnalysisWorkflow(basic_config)
        wf._transition(WorkflowState.SCANNING)
        assert wf.state == WorkflowState.SCANNING

    def test_invalid_transition_raises(self, basic_config: WorkflowConfig) -> None:
        wf = AnalysisWorkflow(basic_config)
        with pytest.raises(InvalidTransitionError, match="Cannot transition"):
            wf._transition(WorkflowState.ENFORCING)  # Can't skip scanning

    def test_completed_is_terminal(self, basic_config: WorkflowConfig) -> None:
        wf = AnalysisWorkflow(basic_config)
        wf._state = WorkflowState.COMPLETED
        assert wf.is_terminal is True

    def test_failed_is_terminal(self, basic_config: WorkflowConfig) -> None:
        wf = AnalysisWorkflow(basic_config)
        wf._state = WorkflowState.FAILED
        assert wf.is_terminal is True

    def test_cancelled_is_terminal(self, basic_config: WorkflowConfig) -> None:
        wf = AnalysisWorkflow(basic_config)
        wf._state = WorkflowState.CANCELLED
        assert wf.is_terminal is True


# ===================================================================
# Workflow execution — happy path (no subsystems)
# ===================================================================


class TestWorkflowRunBasic:
    """Test running the workflow without real subsystems (uses defaults)."""

    @pytest.mark.asyncio
    async def test_basic_run_completes(self, basic_config: WorkflowConfig) -> None:
        wf = AnalysisWorkflow(basic_config)
        result = await wf.run()

        assert result.state == WorkflowState.COMPLETED
        assert result.cycle_id == wf.cycle_id
        assert result.started_at is not None
        assert result.completed_at is not None
        assert result.duration_seconds >= 0
        assert result.config.name == "test-cycle"

    @pytest.mark.asyncio
    async def test_basic_run_has_scan_and_analysis_phases(
        self, basic_config: WorkflowConfig
    ) -> None:
        wf = AnalysisWorkflow(basic_config)
        result = await wf.run()

        phase_names = [p.phase for p in result.phases]
        assert CyclePhase.SCAN in phase_names
        assert CyclePhase.ANALYSE in phase_names
        assert CyclePhase.REPORT in phase_names

    @pytest.mark.asyncio
    async def test_basic_run_skips_enforcement_by_default(
        self, basic_config: WorkflowConfig
    ) -> None:
        """Without auto_enforce, enforcement and remediation are skipped."""
        wf = AnalysisWorkflow(basic_config)
        result = await wf.run()

        phase_names = [p.phase for p in result.phases]
        assert CyclePhase.ENFORCE not in phase_names
        assert CyclePhase.REMEDIATE not in phase_names

    @pytest.mark.asyncio
    async def test_basic_run_all_phases_completed(
        self, basic_config: WorkflowConfig
    ) -> None:
        wf = AnalysisWorkflow(basic_config)
        result = await wf.run()

        for phase in result.phases:
            assert phase.status == "completed"
            assert phase.completed_at is not None
            assert phase.duration_seconds >= 0


# ===================================================================
# Workflow execution — with mock subsystems
# ===================================================================


class TestWorkflowRunWithMocks:
    """Test running the workflow with mock scanner/analyzer/enforcer."""

    @pytest.mark.asyncio
    async def test_scan_phase_uses_scanner(
        self,
        basic_config: WorkflowConfig,
        mock_scanner: AsyncMock,
    ) -> None:
        wf = AnalysisWorkflow(basic_config)
        result = await wf.run(scanner=mock_scanner)

        mock_scanner.scan_all.assert_awaited_once()
        scan_phase = next(p for p in result.phases if p.phase == CyclePhase.SCAN)
        assert scan_phase.output["scan_id"] == "SCAN-TEST-001"
        assert scan_phase.output["total_modules"] == 10
        assert scan_phase.output["pass_rate"] == 80.0

    @pytest.mark.asyncio
    async def test_analysis_phase_uses_analyzer(
        self,
        basic_config: WorkflowConfig,
        mock_analyzer: AsyncMock,
    ) -> None:
        wf = AnalysisWorkflow(basic_config)
        result = await wf.run(analyzer=mock_analyzer)

        mock_analyzer.generate_report.assert_awaited_once()
        analyse_phase = next(p for p in result.phases if p.phase == CyclePhase.ANALYSE)
        assert analyse_phase.output["compliance_rate"] == 85.0
        assert analyse_phase.output["hotspot_count"] == 2

    @pytest.mark.asyncio
    async def test_full_cycle_with_all_subsystems(
        self,
        full_config: WorkflowConfig,
        mock_scanner: AsyncMock,
        mock_analyzer: AsyncMock,
        mock_enforcer: AsyncMock,
    ) -> None:
        wf = AnalysisWorkflow(full_config)
        result = await wf.run(
            scanner=mock_scanner,
            analyzer=mock_analyzer,
            enforcer=mock_enforcer,
        )

        assert result.state == WorkflowState.COMPLETED
        mock_scanner.scan_all.assert_awaited_once()
        mock_analyzer.generate_report.assert_awaited_once()
        mock_enforcer.enforce.assert_awaited_once()

        phase_names = [p.phase for p in result.phases]
        assert CyclePhase.SCAN in phase_names
        assert CyclePhase.ANALYSE in phase_names
        assert CyclePhase.ENFORCE in phase_names
        assert CyclePhase.REMEDIATE in phase_names
        assert CyclePhase.REPORT in phase_names

    @pytest.mark.asyncio
    async def test_enforcement_output_recorded(
        self,
        full_config: WorkflowConfig,
        mock_enforcer: AsyncMock,
    ) -> None:
        wf = AnalysisWorkflow(full_config)
        result = await wf.run(enforcer=mock_enforcer)

        enforce_phase = next(p for p in result.phases if p.phase == CyclePhase.ENFORCE)
        assert enforce_phase.output["total_rules"] == 5
        assert enforce_phase.output["violations"] == 1
        assert enforce_phase.output["gate_blocked"] is True

    @pytest.mark.asyncio
    async def test_remediation_counts_auto_fix_rules(
        self,
        full_config: WorkflowConfig,
        mock_enforcer: AsyncMock,
    ) -> None:
        wf = AnalysisWorkflow(full_config)
        result = await wf.run(enforcer=mock_enforcer)

        remediate_phase = next(p for p in result.phases if p.phase == CyclePhase.REMEDIATE)
        assert remediate_phase.output["remediations_applied"] == 2

    @pytest.mark.asyncio
    async def test_result_aggregates_correctly(
        self,
        full_config: WorkflowConfig,
        mock_scanner: AsyncMock,
        mock_analyzer: AsyncMock,
        mock_enforcer: AsyncMock,
    ) -> None:
        wf = AnalysisWorkflow(full_config)
        result = await wf.run(
            scanner=mock_scanner,
            analyzer=mock_analyzer,
            enforcer=mock_enforcer,
        )

        assert result.modules_scanned == 10
        assert result.findings_count == 4  # 3 semantic + 1 violation
        assert result.violations_count == 1
        assert result.remediations_applied == 2
        assert result.gate_blocked is True
        assert result.compliance_rate == 85.0


# ===================================================================
# Workflow execution — skip remediation when no violations
# ===================================================================


class TestWorkflowRemediationLogic:
    """Test remediation phase skip/execute logic."""

    @pytest.mark.asyncio
    async def test_remediation_skipped_when_no_violations(self) -> None:
        """When auto_remediate is True but enforcement has 0 violations,
        the remediation phase should be skipped."""
        config = WorkflowConfig(
            name="no-violations",
            auto_enforce=True,
            auto_remediate=True,
        )

        enforcer = AsyncMock()
        result_mock = MagicMock()
        result_mock.enforcement_id = "ENF-001"
        result_mock.total_rules = 3
        result_mock.passed_rules = [MagicMock(), MagicMock(), MagicMock()]
        result_mock.violations = []
        result_mock.skipped_rules = []
        result_mock.gate_blocked = False
        result_mock.enforcement_actions = []
        enforcer.enforce = AsyncMock(return_value=result_mock)

        wf = AnalysisWorkflow(config)
        result = await wf.run(enforcer=enforcer)

        phase_names = [p.phase for p in result.phases]
        assert CyclePhase.ENFORCE in phase_names
        assert CyclePhase.REMEDIATE not in phase_names


# ===================================================================
# Workflow execution — error handling
# ===================================================================


class TestWorkflowErrorHandling:
    """Test error handling in each phase."""

    @pytest.mark.asyncio
    async def test_scanner_failure_results_in_failed_state(
        self, basic_config: WorkflowConfig
    ) -> None:
        failing_scanner = AsyncMock()
        failing_scanner.scan_all = AsyncMock(side_effect=RuntimeError("disk full"))

        wf = AnalysisWorkflow(basic_config)
        result = await wf.run(scanner=failing_scanner)

        assert result.state == WorkflowState.FAILED
        scan_phase = next(p for p in result.phases if p.phase == CyclePhase.SCAN)
        assert scan_phase.status == "failed"
        assert "disk full" in scan_phase.error

    @pytest.mark.asyncio
    async def test_analyzer_failure_results_in_failed_state(
        self, basic_config: WorkflowConfig
    ) -> None:
        failing_analyzer = AsyncMock()
        failing_analyzer.generate_report = AsyncMock(
            side_effect=ValueError("corrupt index")
        )

        wf = AnalysisWorkflow(basic_config)
        result = await wf.run(analyzer=failing_analyzer)

        assert result.state == WorkflowState.FAILED

    @pytest.mark.asyncio
    async def test_enforcer_failure_results_in_failed_state(self) -> None:
        config = WorkflowConfig(name="enf-fail", auto_enforce=True)
        failing_enforcer = AsyncMock()
        failing_enforcer.enforce = AsyncMock(
            side_effect=ConnectionError("redis down")
        )

        wf = AnalysisWorkflow(config)
        result = await wf.run(enforcer=failing_enforcer)

        assert result.state == WorkflowState.FAILED

    @pytest.mark.asyncio
    async def test_failed_workflow_has_completed_at(
        self, basic_config: WorkflowConfig
    ) -> None:
        failing_scanner = AsyncMock()
        failing_scanner.scan_all = AsyncMock(side_effect=RuntimeError("boom"))

        wf = AnalysisWorkflow(basic_config)
        result = await wf.run(scanner=failing_scanner)

        assert result.completed_at is not None
        assert result.duration_seconds >= 0


# ===================================================================
# Cancellation tests
# ===================================================================


class TestWorkflowCancellation:
    """Test workflow cancellation behaviour."""

    @pytest.mark.asyncio
    async def test_cancel_before_run_raises(self, basic_config: WorkflowConfig) -> None:
        wf = AnalysisWorkflow(basic_config)
        with pytest.raises(WorkflowCancelledError):
            await wf.cancel()

    @pytest.mark.asyncio
    async def test_cancel_on_terminal_state_is_noop(
        self, basic_config: WorkflowConfig
    ) -> None:
        wf = AnalysisWorkflow(basic_config)
        wf._state = WorkflowState.COMPLETED
        # Should not raise
        await wf.cancel()
        assert wf.state == WorkflowState.COMPLETED


# ===================================================================
# Report phase tests
# ===================================================================


class TestReportPhase:
    """Test the report generation phase."""

    @pytest.mark.asyncio
    async def test_report_contains_all_summaries(
        self,
        full_config: WorkflowConfig,
        mock_scanner: AsyncMock,
        mock_analyzer: AsyncMock,
        mock_enforcer: AsyncMock,
    ) -> None:
        wf = AnalysisWorkflow(full_config)
        result = await wf.run(
            scanner=mock_scanner,
            analyzer=mock_analyzer,
            enforcer=mock_enforcer,
        )

        report_phase = next(p for p in result.phases if p.phase == CyclePhase.REPORT)
        output = report_phase.output

        assert "cycle_id" in output
        assert "scan_summary" in output
        assert "analysis_summary" in output
        assert "enforcement_summary" in output
        assert "remediation_summary" in output
        assert "generated_at" in output

    @pytest.mark.asyncio
    async def test_report_scan_summary_values(
        self,
        basic_config: WorkflowConfig,
        mock_scanner: AsyncMock,
    ) -> None:
        wf = AnalysisWorkflow(basic_config)
        result = await wf.run(scanner=mock_scanner)

        report_phase = next(p for p in result.phases if p.phase == CyclePhase.REPORT)
        scan_summary = report_phase.output["scan_summary"]
        assert scan_summary["total_modules"] == 10
        assert scan_summary["pass_rate"] == 80.0


# ===================================================================
# Edge cases
# ===================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_empty_modules_list(self) -> None:
        config = WorkflowConfig(name="empty")
        wf = AnalysisWorkflow(config)
        result = await wf.run()
        assert result.state == WorkflowState.COMPLETED
        assert result.modules_scanned == 0

    @pytest.mark.asyncio
    async def test_workflow_result_summary_on_empty(self) -> None:
        config = WorkflowConfig(name="empty")
        wf = AnalysisWorkflow(config)
        result = await wf.run()
        summary = result.summary()
        assert summary["phases_completed"] == 3  # scan, analyse, report
        assert summary["gate_blocked"] is False

    @pytest.mark.asyncio
    async def test_auto_enforce_without_auto_remediate(self) -> None:
        """auto_enforce=True, auto_remediate=False: enforce phase runs but
        remediation phase is skipped."""
        config = WorkflowConfig(
            name="enforce-only",
            auto_enforce=True,
            auto_remediate=False,
        )
        enforcer = AsyncMock()
        result_mock = MagicMock()
        result_mock.enforcement_id = "ENF-X"
        result_mock.total_rules = 2
        result_mock.passed_rules = [MagicMock()]
        result_mock.violations = [MagicMock()]
        result_mock.skipped_rules = []
        result_mock.gate_blocked = False
        result_mock.enforcement_actions = []
        enforcer.enforce = AsyncMock(return_value=result_mock)

        wf = AnalysisWorkflow(config)
        result = await wf.run(enforcer=enforcer)

        phase_names = [p.phase for p in result.phases]
        assert CyclePhase.ENFORCE in phase_names
        assert CyclePhase.REMEDIATE not in phase_names


# ===================================================================
# Evidence chain tests
# ===================================================================


class TestEvidenceChain:
    """Test evidence chain hash generation and integrity."""

    @pytest.mark.asyncio
    async def test_completed_workflow_has_evidence_hash(self) -> None:
        wf = AnalysisWorkflow(WorkflowConfig(name="evidence-test"))
        result = await wf.run()

        assert result.evidence_chain_hash != ""
        assert len(result.evidence_chain_hash) == 64  # SHA-256 hex

    @pytest.mark.asyncio
    async def test_evidence_hash_changes_with_more_phases(self) -> None:
        """A full-phase workflow should produce a different hash than a basic one."""
        basic = AnalysisWorkflow(WorkflowConfig(name="basic"))
        basic_result = await basic.run()

        config = WorkflowConfig(name="full", auto_enforce=True)
        enforcer = AsyncMock()
        result_mock = MagicMock()
        result_mock.enforcement_id = "E-1"
        result_mock.total_rules = 1
        result_mock.passed_rules = [MagicMock()]
        result_mock.violations = []
        result_mock.skipped_rules = []
        result_mock.gate_blocked = False
        result_mock.enforcement_actions = []
        enforcer.enforce = AsyncMock(return_value=result_mock)

        full = AnalysisWorkflow(config)
        full_result = await full.run(enforcer=enforcer)

        assert basic_result.evidence_chain_hash != full_result.evidence_chain_hash

    @pytest.mark.asyncio
    async def test_evidence_hashes_accumulated_per_transition(self) -> None:
        wf = AnalysisWorkflow(WorkflowConfig(name="hashes"))
        await wf.run()
        # Basic run: PENDING→SCANNING→ANALYSING→REPORTING→COMPLETED = 4 transitions
        assert len(wf._evidence_hashes) == 4

    @pytest.mark.asyncio
    async def test_failed_workflow_still_has_evidence(self) -> None:
        failing_scanner = AsyncMock()
        failing_scanner.scan_all = AsyncMock(side_effect=RuntimeError("fail"))

        wf = AnalysisWorkflow(WorkflowConfig(name="fail-evidence"))
        result = await wf.run(scanner=failing_scanner)

        assert result.state == WorkflowState.FAILED
        # PENDING→SCANNING = 1 transition recorded before failure
        assert len(wf._evidence_hashes) >= 1
        assert result.evidence_chain_hash != ""


# ===================================================================
# Timeout enforcement tests
# ===================================================================


class TestTimeoutEnforcement:
    """Test max_duration_seconds timeout enforcement."""

    @pytest.mark.asyncio
    async def test_timeout_results_in_failed_state(self) -> None:
        """A workflow that exceeds max_duration_seconds should fail."""
        config = WorkflowConfig(name="slow-cycle", max_duration_seconds=60)

        slow_scanner = AsyncMock()

        async def slow_scan():
            await asyncio.sleep(120)  # way longer than timeout
            return MagicMock()

        slow_scanner.scan_all = slow_scan

        wf = AnalysisWorkflow(config)
        # Use a very short timeout for testing
        wf._config = WorkflowConfig(
            name="slow-cycle",
            max_duration_seconds=60,
        )
        # Monkey-patch config for fast test
        object.__setattr__(wf._config, "max_duration_seconds", 0.1)

        result = await wf.run(scanner=slow_scanner)
        assert result.state == WorkflowState.FAILED
        assert result.completed_at is not None

    @pytest.mark.asyncio
    async def test_normal_workflow_does_not_timeout(self) -> None:
        """A fast workflow should complete normally even with timeout."""
        config = WorkflowConfig(name="fast-cycle", max_duration_seconds=60)
        wf = AnalysisWorkflow(config)
        result = await wf.run()

        assert result.state == WorkflowState.COMPLETED


# ===================================================================
# Remediation tracking tests
# ===================================================================


class TestRemediationTracking:
    """Test remediation phase tracks attempted vs applied vs failed."""

    @pytest.mark.asyncio
    async def test_successful_remediations(self) -> None:
        config = WorkflowConfig(name="remed", auto_enforce=True, auto_remediate=True)

        rule_ok = MagicMock()
        rule_ok.auto_fix = True
        rule_ok.apply_fix = AsyncMock()

        enforcer = AsyncMock()
        enf_result = MagicMock()
        enf_result.enforcement_id = "E-1"
        enf_result.total_rules = 2
        enf_result.passed_rules = [MagicMock()]
        enf_result.violations = [MagicMock()]
        enf_result.skipped_rules = []
        enf_result.gate_blocked = False
        enf_result.enforcement_actions = []
        enforcer.enforce = AsyncMock(return_value=enf_result)
        enforcer.rules = [rule_ok, rule_ok]

        wf = AnalysisWorkflow(config)
        result = await wf.run(enforcer=enforcer)

        remediate_phase = next(p for p in result.phases if p.phase == CyclePhase.REMEDIATE)
        assert remediate_phase.output["remediations_attempted"] == 2
        assert remediate_phase.output["remediations_applied"] == 2
        assert remediate_phase.output["remediations_failed"] == 0

    @pytest.mark.asyncio
    async def test_failed_remediations_tracked(self) -> None:
        config = WorkflowConfig(name="remed-fail", auto_enforce=True, auto_remediate=True)

        rule_fail = MagicMock()
        rule_fail.auto_fix = True
        rule_fail.apply_fix = AsyncMock(side_effect=RuntimeError("cannot fix"))

        rule_ok = MagicMock()
        rule_ok.auto_fix = True
        rule_ok.apply_fix = AsyncMock()

        enforcer = AsyncMock()
        enf_result = MagicMock()
        enf_result.enforcement_id = "E-2"
        enf_result.total_rules = 2
        enf_result.passed_rules = []
        enf_result.violations = [MagicMock(), MagicMock()]
        enf_result.skipped_rules = []
        enf_result.gate_blocked = False
        enf_result.enforcement_actions = []
        enforcer.enforce = AsyncMock(return_value=enf_result)
        enforcer.rules = [rule_fail, rule_ok]

        wf = AnalysisWorkflow(config)
        result = await wf.run(enforcer=enforcer)

        remediate_phase = next(p for p in result.phases if p.phase == CyclePhase.REMEDIATE)
        assert remediate_phase.output["remediations_attempted"] == 2
        assert remediate_phase.output["remediations_applied"] == 1
        assert remediate_phase.output["remediations_failed"] == 1

    @pytest.mark.asyncio
    async def test_rules_without_apply_fix_still_count(self) -> None:
        """Rules with auto_fix=True but no apply_fix method should still be counted as applied."""
        config = WorkflowConfig(name="remed-nomethod", auto_enforce=True, auto_remediate=True)

        rule = MagicMock(spec=["auto_fix"])
        rule.auto_fix = True

        enforcer = AsyncMock()
        enf_result = MagicMock()
        enf_result.enforcement_id = "E-3"
        enf_result.total_rules = 1
        enf_result.passed_rules = []
        enf_result.violations = [MagicMock()]
        enf_result.skipped_rules = []
        enf_result.gate_blocked = False
        enf_result.enforcement_actions = []
        enforcer.enforce = AsyncMock(return_value=enf_result)
        enforcer.rules = [rule]

        wf = AnalysisWorkflow(config)
        result = await wf.run(enforcer=enforcer)

        remediate_phase = next(p for p in result.phases if p.phase == CyclePhase.REMEDIATE)
        assert remediate_phase.output["remediations_attempted"] == 1
        assert remediate_phase.output["remediations_applied"] == 1
        assert remediate_phase.output["remediations_failed"] == 0
