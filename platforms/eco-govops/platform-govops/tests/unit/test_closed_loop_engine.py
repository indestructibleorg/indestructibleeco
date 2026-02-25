"""Comprehensive tests for the ClosedLoopEngine governance orchestrator.

Covers engine lifecycle, cycle submission/execution, queue management,
cancellation, status reporting, and multi-cycle sequences.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from engine.orchestrator.analysis_workflow import (
    WorkflowConfig,
    WorkflowResult,
    WorkflowState,
)
from engine.orchestrator.closed_loop import (
    ClosedLoopEngine,
    CycleRecord,
    EngineStatus,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def engine() -> ClosedLoopEngine:
    """Plain engine with no subsystems."""
    return ClosedLoopEngine()


@pytest.fixture
def running_engine() -> ClosedLoopEngine:
    """Engine already in running state."""
    eng = ClosedLoopEngine()
    eng.start()
    return eng


@pytest.fixture
def config_a() -> WorkflowConfig:
    return WorkflowConfig(name="cycle-alpha", modules=["mod-a"])


@pytest.fixture
def config_b() -> WorkflowConfig:
    return WorkflowConfig(name="cycle-beta", modules=["mod-b"])


@pytest.fixture
def config_full() -> WorkflowConfig:
    return WorkflowConfig(
        name="full-scan",
        auto_enforce=True,
        auto_remediate=True,
    )


# ===================================================================
# EngineStatus model tests
# ===================================================================


class TestEngineStatus:
    """Test EngineStatus model."""

    def test_defaults(self) -> None:
        status = EngineStatus()
        assert status.engine_status == "stopped"
        assert status.active_cycle is None
        assert status.queued_cycles == 0
        assert status.completed_count == 0
        assert status.failed_count == 0
        assert status.uptime_seconds == 0.0
        assert status.last_cycle_at is None

    def test_custom_values(self) -> None:
        status = EngineStatus(
            engine_status="running",
            active_cycle="CYCLE-001",
            queued_cycles=3,
            completed_count=10,
            failed_count=2,
        )
        assert status.engine_status == "running"
        assert status.active_cycle == "CYCLE-001"
        assert status.queued_cycles == 3


# ===================================================================
# CycleRecord model tests
# ===================================================================


class TestCycleRecord:
    """Test CycleRecord model."""

    def test_defaults(self) -> None:
        record = CycleRecord(cycle_id="CYC-001", name="test", state="completed")
        assert record.duration_seconds == 0.0
        assert record.modules_scanned == 0
        assert record.findings_count == 0
        assert record.compliance_rate == 0.0

    def test_full_record(self) -> None:
        now = datetime.now(timezone.utc)
        record = CycleRecord(
            cycle_id="CYC-002",
            name="full",
            state="completed",
            started_at=now,
            completed_at=now,
            duration_seconds=12.5,
            modules_scanned=15,
            findings_count=3,
            violations_count=1,
            compliance_rate=87.5,
        )
        assert record.modules_scanned == 15
        assert record.compliance_rate == 87.5


# ===================================================================
# Engine lifecycle tests
# ===================================================================


class TestEngineLifecycle:
    """Test start/stop/pause/resume transitions."""

    def test_initial_state_is_stopped(self, engine: ClosedLoopEngine) -> None:
        status = engine.status()
        assert status.engine_status == "stopped"

    def test_start(self, engine: ClosedLoopEngine) -> None:
        engine.start()
        status = engine.status()
        assert status.engine_status == "running"
        assert status.uptime_seconds >= 0

    def test_stop(self, running_engine: ClosedLoopEngine) -> None:
        running_engine.stop()
        status = running_engine.status()
        assert status.engine_status == "stopped"

    def test_pause(self, running_engine: ClosedLoopEngine) -> None:
        running_engine.pause()
        status = running_engine.status()
        assert status.engine_status == "paused"

    def test_resume(self, running_engine: ClosedLoopEngine) -> None:
        running_engine.pause()
        running_engine.resume()
        status = running_engine.status()
        assert status.engine_status == "running"

    def test_double_start_is_noop(self, running_engine: ClosedLoopEngine) -> None:
        running_engine.start()
        assert running_engine.status().engine_status == "running"

    def test_pause_when_stopped_is_noop(self, engine: ClosedLoopEngine) -> None:
        engine.pause()
        assert engine.status().engine_status == "stopped"

    def test_resume_when_running_is_noop(
        self, running_engine: ClosedLoopEngine
    ) -> None:
        running_engine.resume()
        assert running_engine.status().engine_status == "running"


# ===================================================================
# Cycle submission tests
# ===================================================================


class TestCycleSubmission:
    """Test submitting cycles to the engine."""

    @pytest.mark.asyncio
    async def test_submit_returns_cycle_id(
        self, running_engine: ClosedLoopEngine, config_a: WorkflowConfig
    ) -> None:
        cycle_id = await running_engine.submit_cycle(config_a)
        assert cycle_id.startswith("CYCLE-")
        assert running_engine.queue_depth == 1

    @pytest.mark.asyncio
    async def test_submit_multiple(
        self,
        running_engine: ClosedLoopEngine,
        config_a: WorkflowConfig,
        config_b: WorkflowConfig,
    ) -> None:
        await running_engine.submit_cycle(config_a)
        await running_engine.submit_cycle(config_b)
        assert running_engine.queue_depth == 2

    @pytest.mark.asyncio
    async def test_submit_to_stopped_engine_raises(
        self, engine: ClosedLoopEngine, config_a: WorkflowConfig
    ) -> None:
        with pytest.raises(RuntimeError, match="engine is stopped"):
            await engine.submit_cycle(config_a)

    @pytest.mark.asyncio
    async def test_submit_to_paused_engine_succeeds(
        self, running_engine: ClosedLoopEngine, config_a: WorkflowConfig
    ) -> None:
        running_engine.pause()
        cycle_id = await running_engine.submit_cycle(config_a)
        assert cycle_id.startswith("CYCLE-")
        assert running_engine.queue_depth == 1


# ===================================================================
# Cycle execution tests
# ===================================================================


class TestCycleExecution:
    """Test executing pending cycles."""

    @pytest.mark.asyncio
    async def test_run_pending_executes_all(
        self,
        running_engine: ClosedLoopEngine,
        config_a: WorkflowConfig,
        config_b: WorkflowConfig,
    ) -> None:
        await running_engine.submit_cycle(config_a)
        await running_engine.submit_cycle(config_b)

        results = await running_engine.run_pending()

        assert len(results) == 2
        assert all(r.state == WorkflowState.COMPLETED for r in results)
        assert running_engine.queue_depth == 0

    @pytest.mark.asyncio
    async def test_run_pending_empty_queue(
        self, running_engine: ClosedLoopEngine
    ) -> None:
        results = await running_engine.run_pending()
        assert results == []

    @pytest.mark.asyncio
    async def test_run_one_executes_single(
        self,
        running_engine: ClosedLoopEngine,
        config_a: WorkflowConfig,
        config_b: WorkflowConfig,
    ) -> None:
        await running_engine.submit_cycle(config_a)
        await running_engine.submit_cycle(config_b)

        result = await running_engine.run_one()
        assert result is not None
        assert result.state == WorkflowState.COMPLETED
        assert running_engine.queue_depth == 1

    @pytest.mark.asyncio
    async def test_run_one_empty_queue_returns_none(
        self, running_engine: ClosedLoopEngine
    ) -> None:
        result = await running_engine.run_one()
        assert result is None

    @pytest.mark.asyncio
    async def test_run_pending_stops_when_paused(
        self,
        running_engine: ClosedLoopEngine,
        config_a: WorkflowConfig,
        config_b: WorkflowConfig,
    ) -> None:
        await running_engine.submit_cycle(config_a)
        await running_engine.submit_cycle(config_b)

        # Pause before running — no cycles should execute
        running_engine.pause()
        results = await running_engine.run_pending()
        assert results == []
        assert running_engine.queue_depth == 2

    @pytest.mark.asyncio
    async def test_fifo_execution_order(
        self, running_engine: ClosedLoopEngine
    ) -> None:
        configs = [WorkflowConfig(name=f"cycle-{i}") for i in range(5)]
        for c in configs:
            await running_engine.submit_cycle(c)

        results = await running_engine.run_pending()
        names = [r.config.name for r in results]
        assert names == ["cycle-0", "cycle-1", "cycle-2", "cycle-3", "cycle-4"]


# ===================================================================
# History and status reporting tests
# ===================================================================


class TestHistoryAndStatus:
    """Test history tracking and engine status."""

    @pytest.mark.asyncio
    async def test_history_populated_after_run(
        self, running_engine: ClosedLoopEngine, config_a: WorkflowConfig
    ) -> None:
        await running_engine.submit_cycle(config_a)
        await running_engine.run_pending()

        history = running_engine.history
        assert len(history) == 1
        assert history[0].name == "cycle-alpha"
        assert history[0].state == "completed"

    @pytest.mark.asyncio
    async def test_status_counts_after_runs(
        self, running_engine: ClosedLoopEngine
    ) -> None:
        for i in range(3):
            await running_engine.submit_cycle(WorkflowConfig(name=f"c-{i}"))

        await running_engine.run_pending()

        status = running_engine.status()
        assert status.completed_count == 3
        assert status.failed_count == 0
        assert status.queued_cycles == 0
        assert status.active_cycle is None

    @pytest.mark.asyncio
    async def test_get_cycle_returns_record(
        self, running_engine: ClosedLoopEngine, config_a: WorkflowConfig
    ) -> None:
        cycle_id = await running_engine.submit_cycle(config_a)
        await running_engine.run_pending()

        record = running_engine.get_cycle(cycle_id)
        assert record is not None
        assert record.cycle_id == cycle_id
        assert record.name == "cycle-alpha"

    @pytest.mark.asyncio
    async def test_get_cycle_unknown_returns_none(
        self, running_engine: ClosedLoopEngine
    ) -> None:
        assert running_engine.get_cycle("CYCLE-nonexistent") is None

    @pytest.mark.asyncio
    async def test_last_cycle_at_updated(
        self, running_engine: ClosedLoopEngine, config_a: WorkflowConfig
    ) -> None:
        await running_engine.submit_cycle(config_a)
        await running_engine.run_pending()

        status = running_engine.status()
        assert status.last_cycle_at is not None


# ===================================================================
# Cancellation tests
# ===================================================================


class TestCycleCancellation:
    """Test cancelling queued and active cycles."""

    @pytest.mark.asyncio
    async def test_cancel_queued_cycle(
        self,
        running_engine: ClosedLoopEngine,
        config_a: WorkflowConfig,
    ) -> None:
        cycle_id = await running_engine.submit_cycle(config_a)
        assert running_engine.queue_depth == 1

        cancelled = await running_engine.cancel_cycle(cycle_id)
        assert cancelled is True
        assert running_engine.queue_depth == 0

        # Should be in history as cancelled
        record = running_engine.get_cycle(cycle_id)
        assert record is not None
        assert record.state == "cancelled"

    @pytest.mark.asyncio
    async def test_cancel_unknown_cycle(
        self, running_engine: ClosedLoopEngine
    ) -> None:
        cancelled = await running_engine.cancel_cycle("CYCLE-nonexistent")
        assert cancelled is False

    @pytest.mark.asyncio
    async def test_cancel_preserves_other_queued_cycles(
        self, running_engine: ClosedLoopEngine
    ) -> None:
        id_a = await running_engine.submit_cycle(WorkflowConfig(name="a"))
        id_b = await running_engine.submit_cycle(WorkflowConfig(name="b"))
        id_c = await running_engine.submit_cycle(WorkflowConfig(name="c"))

        await running_engine.cancel_cycle(id_b)

        assert running_engine.queue_depth == 2
        results = await running_engine.run_pending()
        names = [r.config.name for r in results]
        assert names == ["a", "c"]


# ===================================================================
# Engine with subsystems tests
# ===================================================================


class TestEngineWithSubsystems:
    """Test the engine passes subsystems through to workflows."""

    @pytest.mark.asyncio
    async def test_scanner_passed_to_workflow(self) -> None:
        scanner = AsyncMock()
        report = MagicMock()
        report.scan_id = "S-1"
        report.total_modules = 5
        report.summary = MagicMock(passed=5, failed=0, warnings=0, pass_rate=100.0)
        report.violations = []
        report.drift_detected = []
        report.semantic_findings = []
        scanner.scan_all = AsyncMock(return_value=report)

        engine = ClosedLoopEngine(scanner=scanner)
        engine.start()
        await engine.submit_cycle(WorkflowConfig(name="scan-test"))
        results = await engine.run_pending()

        scanner.scan_all.assert_awaited_once()
        assert results[0].modules_scanned == 5

    @pytest.mark.asyncio
    async def test_full_subsystem_integration(self) -> None:
        # Scanner
        scanner = AsyncMock()
        scan_report = MagicMock()
        scan_report.scan_id = "S-2"
        scan_report.total_modules = 3
        scan_report.summary = MagicMock(passed=2, failed=1, warnings=0, pass_rate=66.7)
        scan_report.violations = [MagicMock()]
        scan_report.drift_detected = []
        scan_report.semantic_findings = [MagicMock()]
        scanner.scan_all = AsyncMock(return_value=scan_report)

        # Analyzer
        analyzer = AsyncMock()
        dist = MagicMock(total_modules=3, compliance_rate=66.7)
        comp_report = MagicMock()
        comp_report.distribution = dist
        comp_report.hotspots = [MagicMock()]
        comp_report.trend = []
        comp_report.summary = {"worst_layer": "GL10-19"}
        analyzer.generate_report = AsyncMock(return_value=comp_report)

        # Enforcer
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
        enforcer.rules = []

        engine = ClosedLoopEngine(
            scanner=scanner, analyzer=analyzer, enforcer=enforcer
        )
        engine.start()

        config = WorkflowConfig(
            name="full-integration",
            auto_enforce=True,
            auto_remediate=True,
        )
        await engine.submit_cycle(config)
        results = await engine.run_pending()

        assert len(results) == 1
        result = results[0]
        assert result.state == WorkflowState.COMPLETED
        assert result.modules_scanned == 3
        assert result.compliance_rate == 66.7
        assert result.violations_count == 1

        scanner.scan_all.assert_awaited_once()
        analyzer.generate_report.assert_awaited_once()
        enforcer.enforce.assert_awaited_once()


# ===================================================================
# Multi-cycle sequence tests
# ===================================================================


class TestMultiCycleSequences:
    """Test running multiple cycles in sequence."""

    @pytest.mark.asyncio
    async def test_sequential_cycles_accumulate_history(
        self, running_engine: ClosedLoopEngine
    ) -> None:
        for i in range(5):
            await running_engine.submit_cycle(WorkflowConfig(name=f"seq-{i}"))

        results = await running_engine.run_pending()

        assert len(results) == 5
        assert len(running_engine.history) == 5
        assert running_engine.status().completed_count == 5

    @pytest.mark.asyncio
    async def test_interleaved_submit_and_run(
        self, running_engine: ClosedLoopEngine
    ) -> None:
        """Submit 2, run 1, submit 1 more, run all remaining."""
        await running_engine.submit_cycle(WorkflowConfig(name="batch-1a"))
        await running_engine.submit_cycle(WorkflowConfig(name="batch-1b"))

        r1 = await running_engine.run_one()
        assert r1 is not None
        assert r1.config.name == "batch-1a"

        await running_engine.submit_cycle(WorkflowConfig(name="batch-2"))

        remaining = await running_engine.run_pending()
        names = [r.config.name for r in remaining]
        assert names == ["batch-1b", "batch-2"]

        assert len(running_engine.history) == 3
