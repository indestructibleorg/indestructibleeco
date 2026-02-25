"""Test fixtures for the automation platform test suite."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from automation_platform.domain.entities import Agent, Pipeline, Stage, Task
from automation_platform.domain.value_objects import (
    AgentType,
    ExecutionMode,
    StageBudget,
)
from automation_platform.engines.agent_pool import ParallelAgentPool
from automation_platform.engines.execution_engine import InstantExecutionEngine
from automation_platform.engines.pipeline_engine import PipelineOrchestrator


# -- Simple task handler for tests ---------------------------------------------


async def echo_handler(task: Task) -> dict[str, Any]:
    """Test handler that echoes input data back."""
    await asyncio.sleep(0)
    return {"echo": task.input_data, "command": task.command}


async def slow_handler(task: Task) -> dict[str, Any]:
    """Test handler that takes a configurable time."""
    delay = task.input_data.get("delay", 0.01)
    await asyncio.sleep(delay)
    return {"delayed": True, "delay": delay}


# -- Fixtures ------------------------------------------------------------------


@pytest.fixture
def sample_task() -> Task:
    return Task(command="echo hello", input_data={"key": "value"})


@pytest.fixture
def sample_stage() -> Stage:
    return Stage(
        name="analyze",
        agent_type=AgentType.ANALYZER,
        budget=StageBudget(timeout_seconds=10.0),
    )


@pytest.fixture
def sample_pipeline() -> Pipeline:
    stages = [
        Stage(name="analyze", agent_type=AgentType.ANALYZER),
        Stage(name="generate", agent_type=AgentType.GENERATOR),
        Stage(name="validate", agent_type=AgentType.VALIDATOR),
    ]
    return Pipeline(name="test-pipeline", stages=stages)


@pytest.fixture
def agent_pool() -> ParallelAgentPool:
    return ParallelAgentPool(
        pool_size=4,
        agent_type=AgentType.ANALYZER,
        executor=echo_handler,
    )


@pytest.fixture
def execution_engine() -> InstantExecutionEngine:
    return InstantExecutionEngine(handler=echo_handler)


@pytest.fixture
def pipeline_orchestrator(agent_pool: ParallelAgentPool) -> PipelineOrchestrator:
    return PipelineOrchestrator(default_pool=agent_pool)
