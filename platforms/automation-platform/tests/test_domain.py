"""Tests for the domain layer — entities, value objects, events, exceptions."""

from __future__ import annotations

import time

import pytest

from automation_platform.domain.entities import Agent, Pipeline, Stage, Task
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
    AgentStatus,
    AgentType,
    ExecutionMode,
    PipelineStatus,
    StageBudget,
    StageStatus,
    TaskStatus,
)


# =============================================================================
# Value Objects
# =============================================================================


class TestExecutionMode:
    def test_all_modes_exist(self) -> None:
        assert ExecutionMode.INSTANT == "instant"
        assert ExecutionMode.FAST == "fast"
        assert ExecutionMode.STANDARD == "standard"
        assert ExecutionMode.BACKGROUND == "background"

    def test_mode_from_string(self) -> None:
        assert ExecutionMode("instant") is ExecutionMode.INSTANT


class TestPipelineStatus:
    def test_all_statuses(self) -> None:
        assert PipelineStatus.PENDING == "pending"
        assert PipelineStatus.RUNNING == "running"
        assert PipelineStatus.COMPLETED == "completed"
        assert PipelineStatus.FAILED == "failed"
        assert PipelineStatus.ROLLED_BACK == "rolled_back"


class TestStageBudget:
    def test_defaults(self) -> None:
        budget = StageBudget()
        assert budget.timeout_seconds == 30.0
        assert budget.max_retries == 1
        assert budget.mode == ExecutionMode.STANDARD

    def test_sla_seconds(self) -> None:
        assert StageBudget(mode=ExecutionMode.INSTANT).sla_seconds == 0.1
        assert StageBudget(mode=ExecutionMode.FAST).sla_seconds == 0.5
        assert StageBudget(mode=ExecutionMode.STANDARD).sla_seconds == 5.0
        assert StageBudget(mode=ExecutionMode.BACKGROUND).sla_seconds == float("inf")

    def test_frozen(self) -> None:
        budget = StageBudget()
        with pytest.raises(AttributeError):
            budget.timeout_seconds = 999  # type: ignore[misc]


# =============================================================================
# Entities
# =============================================================================


class TestTask:
    def test_creation(self, sample_task: Task) -> None:
        assert sample_task.command == "echo hello"
        assert sample_task.input_data == {"key": "value"}
        assert sample_task.status == TaskStatus.PENDING
        assert sample_task.id.startswith("task-")

    def test_lifecycle(self) -> None:
        task = Task(command="test")
        assert task.duration_seconds is None

        task.mark_running()
        assert task.status == TaskStatus.RUNNING
        assert task.started_at is not None
        assert task.duration_seconds is not None

        task.mark_completed({"output": "ok"})
        assert task.status == TaskStatus.COMPLETED
        assert task.result == {"output": "ok"}
        assert task.completed_at is not None

    def test_failure(self) -> None:
        task = Task(command="fail")
        task.mark_running()
        task.mark_failed("something broke")
        assert task.status == TaskStatus.FAILED
        assert task.error == "something broke"

    def test_timeout(self) -> None:
        task = Task(command="slow")
        task.mark_running()
        task.mark_timed_out()
        assert task.status == TaskStatus.TIMED_OUT
        assert "timed out" in (task.error or "").lower()


class TestStage:
    def test_creation(self, sample_stage: Stage) -> None:
        assert sample_stage.name == "analyze"
        assert sample_stage.agent_type == AgentType.ANALYZER
        assert sample_stage.status == StageStatus.PENDING

    def test_lifecycle(self) -> None:
        stage = Stage(name="test")
        stage.mark_running()
        assert stage.status == StageStatus.RUNNING
        assert stage.started_at is not None

        stage.mark_completed()
        assert stage.status == StageStatus.COMPLETED
        assert stage.duration_seconds is not None
        assert stage.duration_seconds >= 0

    def test_failure(self) -> None:
        stage = Stage(name="fail-stage")
        stage.mark_running()
        stage.mark_failed("bad input")
        assert stage.status == StageStatus.FAILED
        assert stage.error == "bad input"


class TestAgent:
    def test_creation(self) -> None:
        agent = Agent(type=AgentType.GENERATOR)
        assert agent.type == AgentType.GENERATOR
        assert agent.status == AgentStatus.IDLE
        assert agent.is_available is True
        assert agent.tasks_completed == 0

    def test_assign_and_complete(self) -> None:
        agent = Agent()
        agent.assign_task("task-123")
        assert agent.status == AgentStatus.BUSY
        assert agent.current_task_id == "task-123"
        assert agent.is_available is False

        agent.complete_task()
        assert agent.status == AgentStatus.IDLE
        assert agent.current_task_id is None
        assert agent.tasks_completed == 1

    def test_fail_task(self) -> None:
        agent = Agent()
        agent.assign_task("task-456")
        agent.fail_task()
        assert agent.status == AgentStatus.IDLE
        assert agent.tasks_failed == 1

    def test_heartbeat(self) -> None:
        agent = Agent()
        first_hb = agent.last_heartbeat
        time.sleep(0.01)
        agent.heartbeat()
        assert agent.last_heartbeat > first_hb


class TestPipeline:
    def test_creation(self, sample_pipeline: Pipeline) -> None:
        assert sample_pipeline.name == "test-pipeline"
        assert len(sample_pipeline.stages) == 3
        assert sample_pipeline.status == PipelineStatus.PENDING
        assert sample_pipeline.id.startswith("pipe-")

    def test_lifecycle(self) -> None:
        pipe = Pipeline(name="lc-test", stages=[Stage(name="s1")])
        assert pipe.duration_seconds is None

        pipe.mark_running()
        assert pipe.status == PipelineStatus.RUNNING
        assert pipe.started_at is not None

        pipe.stages[0].mark_completed()
        pipe.mark_completed()
        assert pipe.status == PipelineStatus.COMPLETED
        assert pipe.duration_seconds is not None
        assert len(pipe.completed_stages) == 1

    def test_failure(self) -> None:
        pipe = Pipeline(name="fail-test")
        pipe.mark_running()
        pipe.mark_failed()
        assert pipe.status == PipelineStatus.FAILED

    def test_rollback(self) -> None:
        pipe = Pipeline(name="rb-test")
        pipe.mark_running()
        pipe.mark_rolled_back()
        assert pipe.status == PipelineStatus.ROLLED_BACK

    def test_current_stage(self) -> None:
        stages = [Stage(name="s1"), Stage(name="s2")]
        pipe = Pipeline(name="cs-test", stages=stages)
        assert pipe.current_stage is None

        stages[0].mark_running()
        assert pipe.current_stage is stages[0]

        stages[0].mark_completed()
        assert pipe.current_stage is None


# =============================================================================
# Events
# =============================================================================


class TestEvents:
    def test_pipeline_started(self) -> None:
        e = PipelineStarted(pipeline_id="p1", pipeline_name="test", stage_count=3)
        assert e.pipeline_id == "p1"
        assert e.stage_count == 3
        assert e.event_id  # auto-generated
        assert e.timestamp > 0

    def test_pipeline_completed(self) -> None:
        e = PipelineCompleted(
            pipeline_id="p1",
            pipeline_name="test",
            duration_seconds=1.5,
            stages_completed=3,
        )
        assert e.duration_seconds == 1.5
        assert e.stages_completed == 3

    def test_pipeline_failed(self) -> None:
        e = PipelineFailed(
            pipeline_id="p1",
            pipeline_name="test",
            failed_stage="validate",
            error="bad data",
        )
        assert e.failed_stage == "validate"

    def test_stage_started(self) -> None:
        e = StageStarted(pipeline_id="p1", stage_name="analyze", agent_type="analyzer")
        assert e.stage_name == "analyze"

    def test_stage_completed(self) -> None:
        e = StageCompleted(
            pipeline_id="p1", stage_name="analyze", duration_seconds=0.5, task_count=2
        )
        assert e.task_count == 2

    def test_task_dispatched(self) -> None:
        e = TaskDispatched(
            task_id="t1", command="echo", agent_id="a1", mode="instant"
        )
        assert e.command == "echo"

    def test_task_completed(self) -> None:
        e = TaskCompleted(task_id="t1", success=True, duration_seconds=0.1)
        assert e.success is True

    def test_events_are_frozen(self) -> None:
        e = PipelineStarted(pipeline_id="p1", pipeline_name="test", stage_count=1)
        with pytest.raises(AttributeError):
            e.pipeline_id = "p2"  # type: ignore[misc]


# =============================================================================
# Exceptions
# =============================================================================


class TestExceptions:
    def test_pipeline_not_found(self) -> None:
        exc = PipelineNotFoundError("pipe-abc")
        assert "pipe-abc" in str(exc)
        assert exc.pipeline_id == "pipe-abc"
        assert exc.code == "PIPELINE_NOT_FOUND"

    def test_stage_execution_error(self) -> None:
        exc = StageExecutionError("validate", "bad input")
        assert "validate" in str(exc)
        assert exc.stage_name == "validate"
        assert exc.reason == "bad input"

    def test_agent_pool_exhausted(self) -> None:
        exc = AgentPoolExhaustedError("analyzer", 4)
        assert "analyzer" in str(exc)
        assert exc.pool_size == 4

    def test_task_timeout(self) -> None:
        exc = TaskTimeoutError("task-123", 5.0)
        assert "task-123" in str(exc)
        assert exc.timeout_seconds == 5.0
