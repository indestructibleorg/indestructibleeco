"""FastAPI router — /pipelines, /tasks, /agents, /health endpoints.

This module defines the API surface for the automation platform. It can be
mounted into any FastAPI application:

    from automation_platform.presentation.api import router, configure
    app = FastAPI()
    configure(orchestrator=my_orchestrator, engine=my_engine, pool=my_pool)
    app.include_router(router)
"""

from __future__ import annotations

from typing import Any

from automation_platform.domain.entities import Pipeline, Task
from automation_platform.domain.exceptions import PipelineNotFoundError
from automation_platform.domain.value_objects import ExecutionMode, PipelineStatus
from automation_platform.engines.agent_pool import ParallelAgentPool
from automation_platform.engines.execution_engine import InstantExecutionEngine
from automation_platform.engines.pipeline_engine import PipelineOrchestrator

# ---------------------------------------------------------------------------
# Module-level singletons (configured at startup via ``configure()``)
# ---------------------------------------------------------------------------

_orchestrator: PipelineOrchestrator | None = None
_engine: InstantExecutionEngine | None = None
_pool: ParallelAgentPool | None = None


def configure(
    orchestrator: PipelineOrchestrator | None = None,
    engine: InstantExecutionEngine | None = None,
    pool: ParallelAgentPool | None = None,
) -> None:
    """Wire up the shared dependencies used by the router handlers."""
    global _orchestrator, _engine, _pool
    _orchestrator = orchestrator
    _engine = engine
    _pool = pool


def _get_orchestrator() -> PipelineOrchestrator:
    if _orchestrator is None:
        raise RuntimeError("PipelineOrchestrator not configured; call configure() first")
    return _orchestrator


def _get_engine() -> InstantExecutionEngine:
    if _engine is None:
        raise RuntimeError("InstantExecutionEngine not configured; call configure() first")
    return _engine


def _get_pool() -> ParallelAgentPool:
    if _pool is None:
        raise RuntimeError("ParallelAgentPool not configured; call configure() first")
    return _pool


# ---------------------------------------------------------------------------
# Try to use FastAPI if available, otherwise provide a stub router
# ---------------------------------------------------------------------------

try:
    from fastapi import APIRouter, HTTPException
    from pydantic import BaseModel, Field

    router = APIRouter(prefix="/automation", tags=["automation"])

    # -- Request / Response models ---------------------------------------------

    class StageSpec(BaseModel):
        name: str
        agent_type: str = "analyzer"
        timeout_seconds: float = 30.0
        max_retries: int = 1
        tasks: list[dict[str, Any]] = Field(default_factory=list)

    class CreatePipelineRequest(BaseModel):
        name: str
        stages: list[StageSpec]
        metadata: dict[str, Any] = Field(default_factory=dict)

    class DispatchTaskRequest(BaseModel):
        command: str
        input_data: dict[str, Any] = Field(default_factory=dict)
        mode: str = "standard"

    class PipelineResponse(BaseModel):
        id: str
        name: str
        status: str
        stage_count: int
        duration_seconds: float | None = None
        metadata: dict[str, Any] = Field(default_factory=dict)

    class TaskResponse(BaseModel):
        id: str
        command: str
        status: str
        mode: str
        result: dict[str, Any] = Field(default_factory=dict)
        duration_seconds: float | None = None

    class HealthResponse(BaseModel):
        status: str
        engine: str
        pool: dict[str, Any] = Field(default_factory=dict)
        pipelines_count: int = 0

    # -- Helpers ---------------------------------------------------------------

    def _pipeline_to_response(pipe: Pipeline) -> PipelineResponse:
        return PipelineResponse(
            id=pipe.id,
            name=pipe.name,
            status=pipe.status.value,
            stage_count=len(pipe.stages),
            duration_seconds=pipe.duration_seconds,
            metadata=pipe.metadata,
        )

    def _task_to_response(task: Task) -> TaskResponse:
        return TaskResponse(
            id=task.id,
            command=task.command,
            status=task.status.value,
            mode=task.mode.value,
            result=task.result,
            duration_seconds=task.duration_seconds,
        )

    # -- Endpoints -------------------------------------------------------------

    @router.post("/pipelines", response_model=PipelineResponse)
    async def create_and_run_pipeline(req: CreatePipelineRequest) -> PipelineResponse:
        """Create a pipeline from the spec and immediately run it."""
        orch = _get_orchestrator()
        stages = [s.model_dump() for s in req.stages]
        try:
            pipeline = await orch.create_and_run(req.name, stages, req.metadata)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))
        return _pipeline_to_response(pipeline)

    @router.get("/pipelines/{pipeline_id}", response_model=PipelineResponse)
    async def get_pipeline(pipeline_id: str) -> PipelineResponse:
        """Retrieve a pipeline by id."""
        orch = _get_orchestrator()
        try:
            pipeline = orch.get_pipeline(pipeline_id)
        except PipelineNotFoundError:
            raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_id} not found")
        return _pipeline_to_response(pipeline)

    @router.post("/tasks", response_model=TaskResponse)
    async def dispatch_task(req: DispatchTaskRequest) -> TaskResponse:
        """Dispatch a single task for immediate execution."""
        engine = _get_engine()
        task = Task(
            command=req.command,
            input_data=req.input_data,
            mode=ExecutionMode(req.mode),
        )
        try:
            result_task = await engine.execute_task(task)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))
        return _task_to_response(result_task)

    @router.get("/health", response_model=HealthResponse)
    async def health_check() -> HealthResponse:
        """Platform health endpoint."""
        pool_health: dict[str, Any] = {}
        pipelines_count = 0
        engine_status = "not_configured"

        try:
            engine = _get_engine()
            engine_status = engine.status.value
        except RuntimeError:
            pass

        try:
            pool = _get_pool()
            pool_health = pool.health_summary()
        except RuntimeError:
            pass

        try:
            orch = _get_orchestrator()
            pipelines_count = len(orch.pipelines)
        except RuntimeError:
            pass

        return HealthResponse(
            status="healthy",
            engine=engine_status,
            pool=pool_health,
            pipelines_count=pipelines_count,
        )

except ImportError:
    # FastAPI not installed — provide a no-op router for environments without it
    class _StubRouter:  # type: ignore[no-redef]
        """Placeholder when FastAPI is not available."""

        prefix = "/automation"
        tags = ["automation"]

        def post(self, *a: Any, **kw: Any) -> Any:
            def _dec(fn: Any) -> Any:
                return fn
            return _dec

        def get(self, *a: Any, **kw: Any) -> Any:
            def _dec(fn: Any) -> Any:
                return fn
            return _dec

    router = _StubRouter()  # type: ignore[assignment]
