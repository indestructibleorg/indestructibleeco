"""Tests for the engines layer — execution engine, pipeline orchestrator, agent pool."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from automation_platform.domain.entities import Pipeline, Stage, Task
from automation_platform.domain.events import (
    PipelineCompleted,
    PipelineFailed,
    PipelineStarted,
    StageCompleted,
    StageStarted,
    TaskCompleted,
    TaskDispatched,
)
from automation_platform.domain.exceptions import (
    AgentPoolExhaustedError,
    PipelineNotFoundError,
    StageExecutionError,
    TaskTimeoutError,
)
from automation_platform.domain.value_objects import (
    AgentType,
    ExecutionMode,
    PipelineStatus,
    StageStatus,
    TaskStatus,
)
from automation_platform.engines.agent_pool import ParallelAgentPool
from automation_platform.engines.execution_engine import InstantExecutionEngine
from automation_platform.engines.pipeline_engine import PipelineOrchestrator

from tests.conftest import echo_handler, slow_handler


# =============================================================================
# InstantExecutionEngine
# =============================================================================


class TestInstantExecutionEngine:
    @pytest.mark.asyncio
    async def test_execute_task_basic(self, execution_engine: InstantExecutionEngine) -> None:
        task = Task(command="test-cmd", input_data={"x": 1})
        result = await execution_engine.execute_task(task)
        assert result.status == TaskStatus.COMPLETED
        assert result.result["echo"] == {"x": 1}
        assert result.result["command"] == "test-cmd"

    @pytest.mark.asyncio
    async def test_execute_protocol_payload(
        self, execution_engine: InstantExecutionEngine
    ) -> None:
        await execution_engine.start()
        result = await execution_engine.execute(
            {"command": "hello", "input_data": {"a": 1}, "mode": "standard"}
        )
        assert result["status"] == "completed"
        assert "task_id" in result

    @pytest.mark.asyncio
    async def test_mode_auto_selection(self) -> None:
        engine = InstantExecutionEngine(handler=echo_handler)
        # Small task -> INSTANT mode
        task = Task(command="x", input_data={"a": 1})
        result = await engine.execute_task(task)
        assert result.mode == ExecutionMode.INSTANT

    @pytest.mark.asyncio
    async def test_events_emitted(self, execution_engine: InstantExecutionEngine) -> None:
        task = Task(command="cmd", input_data={})
        await execution_engine.execute_task(task)
        events = execution_engine.events
        assert len(events) == 2
        assert isinstance(events[0], TaskDispatched)
        assert isinstance(events[1], TaskCompleted)
        assert events[1].success is True

    @pytest.mark.asyncio
    async def test_stats_tracking(self, execution_engine: InstantExecutionEngine) -> None:
        assert execution_engine.stats["tasks_run"] == 0
        await execution_engine.execute_task(Task(command="t1"))
        await execution_engine.execute_task(Task(command="t2"))
        assert execution_engine.stats["tasks_run"] == 2

    @pytest.mark.asyncio
    async def test_start_stop(self, execution_engine: InstantExecutionEngine) -> None:
        from platform_shared.protocols.engine import EngineStatus

        assert execution_engine.status == EngineStatus.IDLE
        await execution_engine.start()
        assert execution_engine.status == EngineStatus.RUNNING
        await execution_engine.stop()
        assert execution_engine.status == EngineStatus.STOPPED

    @pytest.mark.asyncio
    async def test_name_property(self, execution_engine: InstantExecutionEngine) -> None:
        assert execution_engine.name == "InstantExecutionEngine"

    @pytest.mark.asyncio
    async def test_handler_failure_marks_task_failed(self) -> None:
        async def failing_handler(task: Task) -> dict[str, Any]:
            raise ValueError("handler exploded")

        engine = InstantExecutionEngine(handler=failing_handler)
        task = Task(command="boom")
        with pytest.raises(ValueError, match="handler exploded"):
            await engine.execute_task(task)
        assert task.status == TaskStatus.FAILED
        assert engine.stats["tasks_failed"] == 1

    @pytest.mark.asyncio
    async def test_concurrent_execution(self) -> None:
        engine = InstantExecutionEngine(handler=echo_handler, max_concurrent=2)
        tasks = [Task(command=f"t{i}", input_data={"i": i}) for i in range(5)]
        results = await asyncio.gather(*(engine.execute_task(t) for t in tasks))
        assert all(r.status == TaskStatus.COMPLETED for r in results)
        assert engine.stats["tasks_run"] == 5


# =============================================================================
# ParallelAgentPool
# =============================================================================


class TestParallelAgentPool:
    @pytest.mark.asyncio
    async def test_dispatch_single_task(self, agent_pool: ParallelAgentPool) -> None:
        task = Task(command="analyze-data", input_data={"data": [1, 2, 3]})
        result = await agent_pool.dispatch_task(task)
        assert result.status == TaskStatus.COMPLETED
        assert result.result["echo"] == {"data": [1, 2, 3]}

    @pytest.mark.asyncio
    async def test_pool_properties(self, agent_pool: ParallelAgentPool) -> None:
        assert agent_pool.pool_size == 4
        assert agent_pool.available_count == 4
        assert agent_pool.active_count == 0
        assert agent_pool.is_draining is False

    @pytest.mark.asyncio
    async def test_dispatch_many_tasks(self, agent_pool: ParallelAgentPool) -> None:
        tasks = [Task(command=f"task-{i}") for i in range(6)]
        results = await agent_pool.dispatch_many(tasks)
        assert len(results) == 6
        completed = [r for r in results if r.status == TaskStatus.COMPLETED]
        assert len(completed) == 6

    @pytest.mark.asyncio
    async def test_events_emitted(self, agent_pool: ParallelAgentPool) -> None:
        await agent_pool.dispatch_task(Task(command="test"))
        events = agent_pool.events
        assert len(events) == 2
        assert isinstance(events[0], TaskDispatched)
        assert isinstance(events[1], TaskCompleted)

    @pytest.mark.asyncio
    async def test_agent_completion_tracking(self, agent_pool: ParallelAgentPool) -> None:
        await agent_pool.dispatch_task(Task(command="job1"))
        await agent_pool.dispatch_task(Task(command="job2"))
        total = sum(a.tasks_completed for a in agent_pool.agents)
        assert total == 2

    @pytest.mark.asyncio
    async def test_drain(self, agent_pool: ParallelAgentPool) -> None:
        from automation_platform.domain.value_objects import AgentStatus

        await agent_pool.drain(timeout=5.0)
        assert agent_pool.is_draining is True
        for agent in agent_pool.agents:
            assert agent.status == AgentStatus.OFFLINE

    @pytest.mark.asyncio
    async def test_drain_rejects_new_tasks(self, agent_pool: ParallelAgentPool) -> None:
        await agent_pool.drain(timeout=5.0)
        with pytest.raises(AgentPoolExhaustedError):
            await agent_pool.dispatch_task(Task(command="rejected"))

    @pytest.mark.asyncio
    async def test_reset_after_drain(self, agent_pool: ParallelAgentPool) -> None:
        await agent_pool.drain(timeout=5.0)
        agent_pool.reset()
        assert agent_pool.is_draining is False
        # Should accept tasks again
        result = await agent_pool.dispatch_task(Task(command="after-reset"))
        assert result.status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_health_summary(self, agent_pool: ParallelAgentPool) -> None:
        summary = agent_pool.health_summary()
        assert summary["pool_size"] == 4
        assert summary["agent_type"] == "analyzer"
        assert summary["available"] == 4
        assert summary["draining"] is False
        assert len(summary["agents"]) == 4

    @pytest.mark.asyncio
    async def test_executor_failure_marks_task_failed(self) -> None:
        async def failing_exec(task: Task) -> dict[str, Any]:
            raise RuntimeError("agent crashed")

        pool = ParallelAgentPool(pool_size=2, executor=failing_exec)
        task = Task(command="crash")
        with pytest.raises(RuntimeError, match="agent crashed"):
            await pool.dispatch_task(task)
        assert task.status == TaskStatus.FAILED

    @pytest.mark.asyncio
    async def test_concurrent_respects_pool_size(self) -> None:
        max_concurrent_seen = 0
        current_concurrent = 0
        lock = asyncio.Lock()

        async def tracking_executor(task: Task) -> dict[str, Any]:
            nonlocal max_concurrent_seen, current_concurrent
            async with lock:
                current_concurrent += 1
                if current_concurrent > max_concurrent_seen:
                    max_concurrent_seen = current_concurrent
            await asyncio.sleep(0.02)
            async with lock:
                current_concurrent -= 1
            return {"ok": True}

        pool = ParallelAgentPool(pool_size=2, executor=tracking_executor)
        tasks = [Task(command=f"t{i}") for i in range(6)]
        await pool.dispatch_many(tasks)
        assert max_concurrent_seen <= 2


# =============================================================================
# PipelineOrchestrator
# =============================================================================


class TestPipelineOrchestrator:
    @pytest.mark.asyncio
    async def test_create_pipeline(
        self, pipeline_orchestrator: PipelineOrchestrator
    ) -> None:
        pipe = pipeline_orchestrator.create_pipeline(
            name="my-pipe",
            stages=[
                {"name": "analyze", "agent_type": "analyzer"},
                {"name": "generate", "agent_type": "generator"},
            ],
        )
        assert pipe.name == "my-pipe"
        assert len(pipe.stages) == 2
        assert pipe.status == PipelineStatus.PENDING

    @pytest.mark.asyncio
    async def test_get_pipeline(
        self, pipeline_orchestrator: PipelineOrchestrator
    ) -> None:
        pipe = pipeline_orchestrator.create_pipeline(
            name="find-me", stages=[{"name": "s1"}]
        )
        found = pipeline_orchestrator.get_pipeline(pipe.id)
        assert found.name == "find-me"

    @pytest.mark.asyncio
    async def test_get_pipeline_not_found(
        self, pipeline_orchestrator: PipelineOrchestrator
    ) -> None:
        with pytest.raises(PipelineNotFoundError):
            pipeline_orchestrator.get_pipeline("nonexistent-id")

    @pytest.mark.asyncio
    async def test_run_pipeline_single_stage(
        self, pipeline_orchestrator: PipelineOrchestrator
    ) -> None:
        pipe = pipeline_orchestrator.create_pipeline(
            name="simple", stages=[{"name": "step1"}]
        )
        result = await pipeline_orchestrator.run_pipeline(pipe.id)
        assert result.status == PipelineStatus.COMPLETED
        assert len(result.completed_stages) == 1
        assert result.duration_seconds is not None

    @pytest.mark.asyncio
    async def test_run_pipeline_multi_stage(
        self, pipeline_orchestrator: PipelineOrchestrator
    ) -> None:
        pipe = pipeline_orchestrator.create_pipeline(
            name="multi",
            stages=[
                {"name": "analyze"},
                {"name": "generate"},
                {"name": "validate"},
            ],
        )
        result = await pipeline_orchestrator.run_pipeline(pipe.id)
        assert result.status == PipelineStatus.COMPLETED
        assert len(result.completed_stages) == 3

    @pytest.mark.asyncio
    async def test_run_pipeline_with_tasks(
        self, pipeline_orchestrator: PipelineOrchestrator
    ) -> None:
        pipe = pipeline_orchestrator.create_pipeline(
            name="with-tasks",
            stages=[
                {
                    "name": "process",
                    "tasks": [
                        {"command": "cmd1", "input_data": {"a": 1}},
                        {"command": "cmd2", "input_data": {"b": 2}},
                    ],
                },
            ],
        )
        result = await pipeline_orchestrator.run_pipeline(pipe.id)
        assert result.status == PipelineStatus.COMPLETED
        assert len(result.stages[0].tasks) == 2

    @pytest.mark.asyncio
    async def test_pipeline_events(
        self, pipeline_orchestrator: PipelineOrchestrator
    ) -> None:
        pipe = pipeline_orchestrator.create_pipeline(
            name="evt-test", stages=[{"name": "s1"}]
        )
        await pipeline_orchestrator.run_pipeline(pipe.id)
        events = pipeline_orchestrator.events
        types = [type(e).__name__ for e in events]
        assert "PipelineStarted" in types
        assert "StageStarted" in types
        assert "StageCompleted" in types
        assert "PipelineCompleted" in types

    @pytest.mark.asyncio
    async def test_pipeline_failure_events(self) -> None:
        async def failing_executor(task: Task) -> dict[str, Any]:
            raise RuntimeError("stage blew up")

        pool = ParallelAgentPool(pool_size=2, executor=failing_executor)
        orch = PipelineOrchestrator(default_pool=pool)
        pipe = orch.create_pipeline(name="fail-pipe", stages=[{"name": "bad-stage"}])

        with pytest.raises(StageExecutionError):
            await orch.run_pipeline(pipe.id)

        assert pipe.status == PipelineStatus.FAILED
        event_types = [type(e).__name__ for e in orch.events]
        assert "PipelineFailed" in event_types

    @pytest.mark.asyncio
    async def test_create_and_run_shortcut(
        self, pipeline_orchestrator: PipelineOrchestrator
    ) -> None:
        result = await pipeline_orchestrator.create_and_run(
            name="shortcut",
            stages=[{"name": "quick"}],
            metadata={"env": "test"},
        )
        assert result.status == PipelineStatus.COMPLETED
        assert result.metadata == {"env": "test"}

    @pytest.mark.asyncio
    async def test_pipelines_dict(
        self, pipeline_orchestrator: PipelineOrchestrator
    ) -> None:
        pipeline_orchestrator.create_pipeline(name="p1", stages=[{"name": "s"}])
        pipeline_orchestrator.create_pipeline(name="p2", stages=[{"name": "s"}])
        assert len(pipeline_orchestrator.pipelines) == 2

    @pytest.mark.asyncio
    async def test_stage_with_custom_agent_type(self) -> None:
        async def handler(task: Task) -> dict[str, Any]:
            return {"done": True}

        deployer_pool = ParallelAgentPool(
            pool_size=2, agent_type=AgentType.DEPLOYER, executor=handler
        )
        orch = PipelineOrchestrator(
            agent_pools={AgentType.DEPLOYER: deployer_pool},
            default_pool=ParallelAgentPool(pool_size=2, executor=handler),
        )
        pipe = orch.create_pipeline(
            name="deploy-pipe",
            stages=[
                {"name": "prep"},
                {"name": "deploy", "agent_type": "deployer"},
            ],
        )
        result = await orch.run_pipeline(pipe.id)
        assert result.status == PipelineStatus.COMPLETED
