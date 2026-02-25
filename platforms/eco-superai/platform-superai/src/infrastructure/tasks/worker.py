"""Celery worker — distributed task processing for quantum, AI, and scientific workloads."""
from __future__ import annotations

import json
import time
from typing import Any

import structlog
from celery import Celery, Task
from celery.schedules import crontab
from celery.signals import task_failure, task_postrun, task_prerun

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Celery Application
# ---------------------------------------------------------------------------


def _create_celery_app() -> Celery:
    """Create and configure the Celery application."""
    try:
        from src.infrastructure.config import get_settings
        settings = get_settings()
        broker = settings.celery.broker_url
        backend = settings.celery.result_backend
    except Exception:
        broker = "amqp://superai:superai_secret@localhost:5672//"
        backend = "redis://localhost:6379/1"

    app = Celery(
        "superai",
        broker=broker,
        backend=backend,
    )

    app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=3600,
        task_soft_time_limit=3300,
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=1000,
        task_default_queue="default",
        task_queues={
            "default": {"exchange": "default", "routing_key": "default"},
            "quantum": {"exchange": "quantum", "routing_key": "quantum"},
            "ai": {"exchange": "ai", "routing_key": "ai"},
            "scientific": {"exchange": "scientific", "routing_key": "scientific"},
        },
        task_routes={
            "src.infrastructure.tasks.worker.run_quantum_job": {"queue": "quantum"},
            "src.infrastructure.tasks.worker.run_ai_task": {"queue": "ai"},
            "src.infrastructure.tasks.worker.run_scientific_pipeline": {"queue": "scientific"},
        },
        beat_schedule={
            "health-check-every-5m": {
                "task": "src.infrastructure.tasks.worker.periodic_health_check",
                "schedule": crontab(minute="*/5"),
            },
            "cleanup-expired-jobs-hourly": {
                "task": "src.infrastructure.tasks.worker.cleanup_expired_jobs",
                "schedule": crontab(minute=0),
            },
            "metrics-snapshot-every-minute": {
                "task": "src.infrastructure.tasks.worker.collect_metrics_snapshot",
                "schedule": 60.0,
            },
        },
    )

    return app


celery_app = _create_celery_app()


# ---------------------------------------------------------------------------
# Signal Handlers
# ---------------------------------------------------------------------------

@task_prerun.connect
def on_task_prerun(sender: Task | None = None, task_id: str | None = None, **kwargs: Any) -> None:
    logger.info("celery_task_started", task=sender.name if sender else "unknown", task_id=task_id)


@task_postrun.connect
def on_task_postrun(
    sender: Task | None = None,
    task_id: str | None = None,
    retval: Any = None,
    state: str | None = None,
    **kwargs: Any,
) -> None:
    logger.info("celery_task_finished", task=sender.name if sender else "unknown", task_id=task_id, state=state)


@task_failure.connect
def on_task_failure(
    sender: Task | None = None,
    task_id: str | None = None,
    exception: Exception | None = None,
    **kwargs: Any,
) -> None:
    logger.error(
        "celery_task_failed",
        task=sender.name if sender else "unknown",
        task_id=task_id,
        error=str(exception),
    )


# ---------------------------------------------------------------------------
# Quantum Tasks
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, name="src.infrastructure.tasks.worker.run_quantum_job", max_retries=2)
def run_quantum_job(
    self: Task,
    user_id: str,
    algorithm: str,
    num_qubits: int = 2,
    shots: int = 1024,
    backend: str = "aer_simulator",
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute a quantum circuit as a background task."""
    import asyncio

    async def _execute() -> dict[str, Any]:
        from src.application.use_cases.quantum_management import SubmitQuantumJobUseCase
        uc = SubmitQuantumJobUseCase(repo=None)
        return await uc.execute(
            user_id=user_id,
            algorithm=algorithm,
            num_qubits=num_qubits,
            shots=shots,
            backend=backend,
            parameters=parameters,
        )

    try:
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(_execute())
        loop.close()
        return result
    except Exception as exc:
        logger.error("quantum_task_error", error=str(exc))
        raise self.retry(exc=exc, countdown=10)


# ---------------------------------------------------------------------------
# AI Tasks
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, name="src.infrastructure.tasks.worker.run_ai_task", max_retries=2)
def run_ai_task(
    self: Task,
    agent_type: str,
    task: str,
    context: dict[str, Any] | None = None,
    constraints: list[str] | None = None,
    output_format: str = "markdown",
) -> dict[str, Any]:
    """Execute an AI agent task in the background."""
    import asyncio

    async def _execute() -> dict[str, Any]:
        from src.application.use_cases.ai_management import ExecuteAgentTaskUseCase
        uc = ExecuteAgentTaskUseCase()
        return await uc.execute(
            agent_type=agent_type,
            task=task,
            context=context,
            constraints=constraints,
            output_format=output_format,
        )

    try:
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(_execute())
        loop.close()
        return result
    except Exception as exc:
        logger.error("ai_task_error", error=str(exc))
        raise self.retry(exc=exc, countdown=10)


# ---------------------------------------------------------------------------
# Scientific Tasks
# ---------------------------------------------------------------------------

@celery_app.task(bind=True, name="src.infrastructure.tasks.worker.run_scientific_pipeline", max_retries=1)
def run_scientific_pipeline(
    self: Task,
    pipeline_name: str,
    data: Any,
    steps: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Execute a scientific data pipeline in the background."""
    start = time.perf_counter()
    try:
        from src.scientific.pipelines import DataPipeline, normalize, remove_outliers, fill_missing

        pipeline = DataPipeline(name=pipeline_name)

        step_registry = {
            "normalize": normalize,
            "remove_outliers": remove_outliers,
            "fill_missing": fill_missing,
        }

        for step_def in (steps or []):
            func_name = step_def.get("name", "")
            func = step_registry.get(func_name)
            if func:
                pipeline.add_step(name=func_name, func=func, params=step_def.get("params", {}))

        result = pipeline.execute(data)
        elapsed = (time.perf_counter() - start) * 1000
        result["task_execution_time_ms"] = round(elapsed, 2)
        return result
    except Exception as exc:
        logger.error("scientific_pipeline_error", error=str(exc))
        raise self.retry(exc=exc, countdown=5)


# ---------------------------------------------------------------------------
# Periodic / Maintenance Tasks
# ---------------------------------------------------------------------------

@celery_app.task(name="src.infrastructure.tasks.worker.periodic_health_check")
def periodic_health_check() -> dict[str, Any]:
    """Periodic system health check."""
    import platform
    from datetime import datetime, timezone

    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hostname": platform.node(),
        "python_version": platform.python_version(),
    }


@celery_app.task(name="src.infrastructure.tasks.worker.cleanup_expired_jobs")
def cleanup_expired_jobs() -> dict[str, Any]:
    """Clean up stale quantum jobs and expired cache entries."""
    logger.info("cleanup_expired_jobs_started")
    # In production: query DB for jobs stuck in 'running' > 1h, mark as failed
    return {"status": "completed", "cleaned": 0}


@celery_app.task(name="src.infrastructure.tasks.worker.collect_metrics_snapshot")
def collect_metrics_snapshot() -> dict[str, Any]:
    """Collect and store a metrics snapshot for monitoring."""
    import os

    return {
        "status": "collected",
        "pid": os.getpid(),
        "memory_mb": _get_process_memory_mb(),
    }


def _get_process_memory_mb() -> float:
    try:
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF)
        return round(usage.ru_maxrss / 1024, 2)
    except Exception:
        return 0.0


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main() -> None:
    """CLI entry point for the Celery worker."""
    celery_app.worker_main(
        argv=[
            "worker",
            "--loglevel=info",
            "--concurrency=4",
            "--pool=prefork",
            "-Q", "default,quantum,ai,scientific",
        ]
    )


__all__ = [
    "celery_app",
    "run_quantum_job",
    "run_ai_task",
    "run_scientific_pipeline",
    "periodic_health_check",
    "cleanup_expired_jobs",
    "collect_metrics_snapshot",
    "main",
]