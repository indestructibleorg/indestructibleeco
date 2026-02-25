"""PipelineOrchestrator — creates Pipeline entities, iterates stages sequentially,
dispatches work to the agent pool, tracks timing per stage, and emits domain events.
"""

from __future__ import annotations

import time
from typing import Any

from automation_platform.domain.entities import Pipeline, Stage, Task
from automation_platform.domain.events import (
    PipelineCompleted,
    PipelineFailed,
    PipelineStarted,
    StageCompleted,
    StageStarted,
)
from automation_platform.domain.exceptions import PipelineNotFoundError, StageExecutionError
from automation_platform.domain.value_objects import (
    AgentType,
    PipelineStatus,
    StageBudget,
    StageStatus,
    TaskStatus,
)
from automation_platform.engines.agent_pool import ParallelAgentPool


class PipelineOrchestrator:
    """Orchestrates multi-stage pipelines, dispatching stage work to agent pools."""

    def __init__(
        self,
        agent_pools: dict[AgentType, ParallelAgentPool] | None = None,
        default_pool: ParallelAgentPool | None = None,
    ) -> None:
        self._pools: dict[AgentType, ParallelAgentPool] = agent_pools or {}
        self._default_pool = default_pool
        self._pipelines: dict[str, Pipeline] = {}
        self._events: list[Any] = []

    # -- Pipeline CRUD ---------------------------------------------------------

    def create_pipeline(
        self,
        name: str,
        stages: list[dict[str, Any]],
        metadata: dict[str, Any] | None = None,
    ) -> Pipeline:
        """Create a new Pipeline entity from a list of stage specs.

        Each stage dict supports:
          - name (str, required)
          - agent_type (str, default "analyzer")
          - timeout_seconds (float, default 30)
          - max_retries (int, default 1)
          - tasks (list[dict], optional) — pre-loaded tasks
        """
        built_stages: list[Stage] = []
        for spec in stages:
            agent_type = AgentType(spec.get("agent_type", "analyzer"))
            budget = StageBudget(
                timeout_seconds=spec.get("timeout_seconds", 30.0),
                max_retries=spec.get("max_retries", 1),
            )
            tasks: list[Task] = []
            for td in spec.get("tasks", []):
                tasks.append(
                    Task(
                        command=td.get("command", ""),
                        input_data=td.get("input_data", {}),
                    )
                )
            built_stages.append(
                Stage(
                    name=spec["name"],
                    agent_type=agent_type,
                    budget=budget,
                    tasks=tasks,
                )
            )

        pipeline = Pipeline(name=name, stages=built_stages, metadata=metadata or {})
        self._pipelines[pipeline.id] = pipeline
        return pipeline

    def get_pipeline(self, pipeline_id: str) -> Pipeline:
        pipe = self._pipelines.get(pipeline_id)
        if pipe is None:
            raise PipelineNotFoundError(pipeline_id)
        return pipe

    @property
    def pipelines(self) -> dict[str, Pipeline]:
        return dict(self._pipelines)

    @property
    def events(self) -> list[Any]:
        return list(self._events)

    # -- Execution -------------------------------------------------------------

    def _get_pool(self, agent_type: AgentType) -> ParallelAgentPool:
        pool = self._pools.get(agent_type) or self._default_pool
        if pool is None:
            raise StageExecutionError(
                agent_type.value,
                f"No agent pool configured for type '{agent_type.value}'",
            )
        return pool

    async def run_pipeline(self, pipeline_id: str) -> Pipeline:
        """Run all stages of a pipeline sequentially. Returns the completed pipeline."""
        pipeline = self.get_pipeline(pipeline_id)
        pipeline.mark_running()

        self._events.append(
            PipelineStarted(
                pipeline_id=pipeline.id,
                pipeline_name=pipeline.name,
                stage_count=len(pipeline.stages),
            )
        )

        for stage in pipeline.stages:
            try:
                await self._run_stage(pipeline, stage)
            except Exception as exc:
                stage.mark_failed(str(exc))
                pipeline.mark_failed()

                self._events.append(
                    PipelineFailed(
                        pipeline_id=pipeline.id,
                        pipeline_name=pipeline.name,
                        failed_stage=stage.name,
                        error=str(exc),
                    )
                )
                raise StageExecutionError(stage.name, str(exc))

        pipeline.mark_completed()
        self._events.append(
            PipelineCompleted(
                pipeline_id=pipeline.id,
                pipeline_name=pipeline.name,
                duration_seconds=pipeline.duration_seconds or 0.0,
                stages_completed=len(pipeline.completed_stages),
            )
        )
        return pipeline

    async def _run_stage(self, pipeline: Pipeline, stage: Stage) -> None:
        """Execute a single stage by dispatching its tasks to the appropriate pool."""
        stage.mark_running()

        self._events.append(
            StageStarted(
                pipeline_id=pipeline.id,
                stage_name=stage.name,
                agent_type=stage.agent_type.value,
            )
        )

        pool = self._get_pool(stage.agent_type)

        if stage.tasks:
            # Dispatch all tasks in this stage concurrently via the pool
            completed_tasks = await pool.dispatch_many(stage.tasks)
            # Check for failures
            failures = [t for t in completed_tasks if t.status == TaskStatus.FAILED]
            if failures:
                error_msgs = [f"{t.id}: {t.error}" for t in failures]
                raise StageExecutionError(stage.name, "; ".join(error_msgs))
        else:
            # Stage with no pre-loaded tasks: create and dispatch a default task
            default_task = Task(command=f"run-stage-{stage.name}")
            stage.tasks.append(default_task)
            await pool.dispatch_task(default_task)
            if default_task.status == TaskStatus.FAILED:
                raise StageExecutionError(stage.name, default_task.error or "unknown error")

        stage.mark_completed()

        self._events.append(
            StageCompleted(
                pipeline_id=pipeline.id,
                stage_name=stage.name,
                duration_seconds=stage.duration_seconds or 0.0,
                task_count=len(stage.tasks),
            )
        )

    # -- Convenience -----------------------------------------------------------

    async def create_and_run(
        self,
        name: str,
        stages: list[dict[str, Any]],
        metadata: dict[str, Any] | None = None,
    ) -> Pipeline:
        """Shortcut: create a pipeline and immediately run it."""
        pipeline = self.create_pipeline(name, stages, metadata)
        return await self.run_pipeline(pipeline.id)
