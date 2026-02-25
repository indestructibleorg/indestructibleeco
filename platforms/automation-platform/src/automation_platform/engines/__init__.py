"""Engines — execution, pipeline orchestration, and agent pool management."""

from automation_platform.engines.agent_pool import ParallelAgentPool
from automation_platform.engines.execution_engine import InstantExecutionEngine
from automation_platform.engines.pipeline_engine import PipelineOrchestrator

__all__ = [
    "InstantExecutionEngine",
    "PipelineOrchestrator",
    "ParallelAgentPool",
]
