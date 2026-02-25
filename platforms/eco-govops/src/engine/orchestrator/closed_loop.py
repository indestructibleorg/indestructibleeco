"""Closed-loop governance engine — continuous cycle orchestrator.

Manages a queue of governance analysis cycles, executing them sequentially or
on a schedule.  Provides an operational status dashboard and supports
graceful shutdown.

Mirrors the 7-layer GQS (Governance Quantum Stack) model from the CI/CD
closed-loop-governance workflow:

    L1: Collect State  → scan phase
    L2: Validate       → analyse phase
    L3: Verify         → enforce phase
    L4: Generate Proof → evidence chain
    L5: Enforce        → remediation phase
    L6: Arbitrate      → gate decision
    L7: Report         → report phase

@GL-governed
@GL-layer: GL30-49
@GL-semantic: governance-closed-loop
"""
from __future__ import annotations

import asyncio
import uuid
from collections import deque
from datetime import datetime, timezone
from typing import Any

import structlog
from pydantic import BaseModel, Field

from engine.orchestrator.analysis_workflow import (
    AnalysisWorkflow,
    WorkflowConfig,
    WorkflowResult,
    WorkflowState,
)

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Engine status model
# ---------------------------------------------------------------------------


class EngineStatus(BaseModel):
    """Snapshot of the closed-loop engine's operational status.

    Attributes:
        engine_status: Current engine state (running | paused | stopped).
        active_cycle: Cycle ID of the currently executing workflow (if any).
        queued_cycles: Number of cycles waiting to execute.
        completed_count: Total cycles completed since engine start.
        failed_count: Total cycles that failed since engine start.
        uptime_seconds: Seconds since the engine was started.
        last_cycle_at: Timestamp of the last completed cycle.
        workers_available: Available worker slots.
        workers_total: Total configured worker slots.
    """

    engine_status: str = "stopped"
    active_cycle: str | None = None
    queued_cycles: int = 0
    completed_count: int = 0
    failed_count: int = 0
    uptime_seconds: float = 0.0
    last_cycle_at: datetime | None = None
    workers_available: int = 1
    workers_total: int = 1


class CycleRecord(BaseModel):
    """Immutable record of a completed governance cycle."""

    cycle_id: str
    name: str
    state: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_seconds: float = 0.0
    modules_scanned: int = 0
    findings_count: int = 0
    violations_count: int = 0
    compliance_rate: float = 0.0


# ---------------------------------------------------------------------------
# ClosedLoopEngine
# ---------------------------------------------------------------------------


class ClosedLoopEngine:
    """Continuous governance engine running analysis cycles on demand.

    Usage::

        engine = ClosedLoopEngine()
        engine.start()
        cycle_id = await engine.submit_cycle(
            WorkflowConfig(name="nightly-scan")
        )
        await engine.run_pending()
        status = engine.status()
        engine.stop()

    The engine maintains a FIFO queue of pending cycles and processes them
    one at a time.  It records the outcome of each cycle for status reporting.
    """

    def __init__(
        self,
        *,
        scanner: Any = None,
        analyzer: Any = None,
        enforcer: Any = None,
    ) -> None:
        self._scanner = scanner
        self._analyzer = analyzer
        self._enforcer = enforcer

        self._engine_status: str = "stopped"
        self._queue: deque[tuple[str, WorkflowConfig]] = deque()
        self._active_workflow: AnalysisWorkflow | None = None
        self._history: list[CycleRecord] = []
        self._started_at: datetime | None = None

        logger.info("closed_loop_engine_init")

    # -- lifecycle ----------------------------------------------------------

    def start(self) -> None:
        """Start the engine, allowing cycles to be submitted and executed."""
        if self._engine_status == "running":
            logger.warning("engine_already_running")
            return
        self._engine_status = "running"
        self._started_at = datetime.now(timezone.utc)
        logger.info("engine_started")

    def stop(self) -> None:
        """Stop the engine. Pending cycles remain in the queue but will not
        execute until the engine is started again."""
        self._engine_status = "stopped"
        self._active_workflow = None
        logger.info("engine_stopped", pending=len(self._queue))

    def pause(self) -> None:
        """Pause the engine. Existing active cycle continues but no new cycles
        will be dequeued."""
        if self._engine_status != "running":
            logger.warning("engine_not_running", status=self._engine_status)
            return
        self._engine_status = "paused"
        logger.info("engine_paused")

    def resume(self) -> None:
        """Resume a paused engine."""
        if self._engine_status != "paused":
            logger.warning("engine_not_paused", status=self._engine_status)
            return
        self._engine_status = "running"
        logger.info("engine_resumed")

    # -- cycle submission ---------------------------------------------------

    async def submit_cycle(self, config: WorkflowConfig) -> str:
        """Submit a new governance cycle to the queue.

        Args:
            config: Workflow configuration for the cycle.

        Returns:
            The cycle ID assigned to the submitted cycle.

        Raises:
            RuntimeError: If the engine is stopped.
        """
        if self._engine_status == "stopped":
            raise RuntimeError("Cannot submit cycles while engine is stopped")

        cycle_id = f"CYCLE-{uuid.uuid4().hex[:12]}"
        self._queue.append((cycle_id, config))

        logger.info(
            "cycle_submitted",
            cycle_id=cycle_id,
            name=config.name,
            queue_depth=len(self._queue),
        )
        return cycle_id

    # -- execution ----------------------------------------------------------

    async def run_pending(self) -> list[WorkflowResult]:
        """Execute all pending cycles in FIFO order.

        Returns a list of :class:`WorkflowResult` for each cycle that ran.
        Stops early if the engine is stopped or paused.
        """
        results: list[WorkflowResult] = []

        while self._queue and self._engine_status == "running":
            cycle_id, config = self._queue.popleft()
            result = await self._execute_cycle(cycle_id, config)
            results.append(result)

        logger.info(
            "run_pending_complete",
            cycles_executed=len(results),
            remaining=len(self._queue),
        )
        return results

    async def run_one(self) -> WorkflowResult | None:
        """Execute the next pending cycle (if any).

        Returns the :class:`WorkflowResult` or ``None`` if the queue is empty
        or the engine is not running.
        """
        if not self._queue or self._engine_status != "running":
            return None

        cycle_id, config = self._queue.popleft()
        return await self._execute_cycle(cycle_id, config)

    async def _execute_cycle(
        self,
        cycle_id: str,
        config: WorkflowConfig,
    ) -> WorkflowResult:
        """Run a single analysis workflow cycle."""
        workflow = AnalysisWorkflow(config, cycle_id=cycle_id)
        self._active_workflow = workflow

        logger.info(
            "cycle_execution_started",
            cycle_id=cycle_id,
            name=config.name,
        )

        result = await workflow.run(
            scanner=self._scanner,
            analyzer=self._analyzer,
            enforcer=self._enforcer,
        )

        self._active_workflow = None

        record = CycleRecord(
            cycle_id=cycle_id,
            name=config.name,
            state=result.state.value,
            started_at=result.started_at,
            completed_at=result.completed_at,
            duration_seconds=result.duration_seconds,
            modules_scanned=result.modules_scanned,
            findings_count=result.findings_count,
            violations_count=result.violations_count,
            compliance_rate=result.compliance_rate,
        )
        self._history.append(record)

        logger.info(
            "cycle_execution_complete",
            cycle_id=cycle_id,
            state=result.state.value,
            duration=result.duration_seconds,
        )
        return result

    # -- cancellation -------------------------------------------------------

    async def cancel_cycle(self, cycle_id: str) -> bool:
        """Cancel a queued or active cycle.

        Returns True if the cycle was found and cancelled.
        """
        # Check queue first
        for i, (cid, _config) in enumerate(self._queue):
            if cid == cycle_id:
                del self._queue[i]
                self._history.append(
                    CycleRecord(
                        cycle_id=cycle_id,
                        name=_config.name,
                        state="cancelled",
                    )
                )
                logger.info("queued_cycle_cancelled", cycle_id=cycle_id)
                return True

        # Check active workflow
        if self._active_workflow and self._active_workflow.cycle_id == cycle_id:
            await self._active_workflow.cancel()
            logger.info("active_cycle_cancelled", cycle_id=cycle_id)
            return True

        logger.warning("cycle_not_found_for_cancel", cycle_id=cycle_id)
        return False

    # -- introspection ------------------------------------------------------

    def status(self) -> EngineStatus:
        """Return the current engine status snapshot."""
        uptime = 0.0
        if self._started_at and self._engine_status != "stopped":
            uptime = (datetime.now(timezone.utc) - self._started_at).total_seconds()

        completed = sum(1 for r in self._history if r.state == "completed")
        failed = sum(1 for r in self._history if r.state == "failed")

        last_cycle = None
        if self._history:
            last_cycle = self._history[-1].completed_at

        return EngineStatus(
            engine_status=self._engine_status,
            active_cycle=(
                self._active_workflow.cycle_id if self._active_workflow else None
            ),
            queued_cycles=len(self._queue),
            completed_count=completed,
            failed_count=failed,
            uptime_seconds=round(uptime, 2),
            last_cycle_at=last_cycle,
        )

    @property
    def history(self) -> list[CycleRecord]:
        """Return the full cycle execution history."""
        return list(self._history)

    @property
    def queue_depth(self) -> int:
        """Number of cycles waiting to execute."""
        return len(self._queue)

    def get_cycle(self, cycle_id: str) -> CycleRecord | None:
        """Retrieve a cycle record by ID."""
        for record in self._history:
            if record.cycle_id == cycle_id:
                return record
        return None


# ---------------------------------------------------------------------------
# CLI entry point (govops-engine)
# ---------------------------------------------------------------------------


def main() -> None:
    """Entry point for the ``govops-engine`` console script.

    Starts the closed-loop governance engine, submits a default scan cycle,
    and runs it to completion.
    """
    import sys

    engine = ClosedLoopEngine()
    engine.start()

    config = WorkflowConfig(
        name="cli-governance-scan",
        description="Governance scan triggered from the CLI.",
        auto_enforce=True,
    )

    async def _run() -> int:
        cycle_id = await engine.submit_cycle(config)
        results = await engine.run_pending()
        engine.stop()

        for result in results:
            summary = result.summary()
            logger.info("cycle_result", **summary)

            if result.state.value != "completed":
                return 1
        return 0

    exit_code = asyncio.run(_run())
    sys.exit(exit_code)
