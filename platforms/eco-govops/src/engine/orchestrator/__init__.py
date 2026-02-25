"""Orchestrator subsystem — analysis workflow and closed-loop governance engine.

Coordinates the full governance cycle: scan → analyse → enforce → remediate →
report.  Integrates with the Scanner, Enforcer, Executor, and Analyzer
subsystems to deliver end-to-end governance automation.

Exports:
    AnalysisWorkflow   -- Single-cycle workflow with state-machine lifecycle.
    ClosedLoopEngine   -- Continuous governance engine running cycles on demand.
    WorkflowState      -- Lifecycle states for a governance cycle.
    WorkflowConfig     -- Configuration for a workflow cycle.
    WorkflowResult     -- Aggregated outcome of a completed cycle.
    CyclePhase         -- Individual phase within a workflow (scan, analyse, …).
    PhaseResult        -- Outcome of a single phase.

@GL-governed
@GL-layer: GL30-49
@GL-semantic: governance-orchestration
"""

from engine.orchestrator.analysis_workflow import (
    AnalysisWorkflow,
    CyclePhase,
    PhaseResult,
    WorkflowConfig,
    WorkflowResult,
    WorkflowState,
)
from engine.orchestrator.closed_loop import ClosedLoopEngine

__all__ = [
    "AnalysisWorkflow",
    "ClosedLoopEngine",
    "CyclePhase",
    "PhaseResult",
    "WorkflowConfig",
    "WorkflowResult",
    "WorkflowState",
]
