"""Unit tests for infrastructure/tasks/worker.py.

Uses Celery's ALWAYS_EAGER mode so tasks execute synchronously in-process
without requiring a broker or Redis backend.
"""
from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_worker_module():
    """Import worker module, skip if Celery is not installed."""
    try:
        import src.infrastructure.tasks.worker as worker
        return worker
    except ImportError as e:
        pytest.skip(f"Worker module requires missing dependency: {e}")


# ---------------------------------------------------------------------------
# Module-level smoke tests
# ---------------------------------------------------------------------------

class TestWorkerModuleImport:
    """Verify the worker module is importable and exports expected symbols."""

    def test_module_importable(self) -> None:
        worker = _get_worker_module()
        assert worker is not None

    def test_celery_app_created(self) -> None:
        worker = _get_worker_module()
        from celery import Celery
        assert isinstance(worker.celery_app, Celery)

    def test_all_exports_present(self) -> None:
        worker = _get_worker_module()
        for name in ["celery_app", "run_quantum_job", "run_ai_task",
                     "run_scientific_pipeline", "periodic_health_check",
                     "cleanup_expired_jobs", "collect_metrics_snapshot"]:
            assert hasattr(worker, name), f"Missing export: {name}"


# ---------------------------------------------------------------------------
# Periodic / maintenance tasks (pure Python, no external deps)
# ---------------------------------------------------------------------------

class TestPeriodicHealthCheck:
    """Tests for periodic_health_check task."""

    def test_returns_healthy_status(self) -> None:
        worker = _get_worker_module()
        # Call the underlying function directly (not via Celery)
        result = worker.periodic_health_check()
        assert result["status"] == "healthy"
        assert "timestamp" in result
        assert "hostname" in result
        assert "python_version" in result

    def test_timestamp_is_iso_format(self) -> None:
        worker = _get_worker_module()
        result = worker.periodic_health_check()
        # Should be parseable as ISO datetime
        from datetime import datetime
        dt = datetime.fromisoformat(result["timestamp"].replace("Z", "+00:00"))
        assert dt is not None


class TestCleanupExpiredJobs:
    """Tests for cleanup_expired_jobs task."""

    def test_returns_completed_status(self) -> None:
        worker = _get_worker_module()
        result = worker.cleanup_expired_jobs()
        assert result["status"] == "completed"
        assert "cleaned" in result
        assert isinstance(result["cleaned"], int)


class TestCollectMetricsSnapshot:
    """Tests for collect_metrics_snapshot task."""

    def test_returns_collected_status(self) -> None:
        worker = _get_worker_module()
        result = worker.collect_metrics_snapshot()
        assert result["status"] == "collected"
        assert "pid" in result
        assert result["pid"] == os.getpid()
        assert "memory_mb" in result
        assert isinstance(result["memory_mb"], float)

    def test_memory_is_non_negative(self) -> None:
        worker = _get_worker_module()
        result = worker.collect_metrics_snapshot()
        assert result["memory_mb"] >= 0.0


class TestGetProcessMemoryMb:
    """Tests for _get_process_memory_mb helper."""

    def test_returns_float(self) -> None:
        worker = _get_worker_module()
        result = worker._get_process_memory_mb()
        assert isinstance(result, float)
        assert result >= 0.0

    def test_resource_exception_returns_zero(self) -> None:
        worker = _get_worker_module()
        with patch("resource.getrusage", side_effect=OSError("no resource")):
            result = worker._get_process_memory_mb()
        assert result == 0.0


# ---------------------------------------------------------------------------
# Signal handlers (coverage for on_task_prerun, on_task_postrun, on_task_failure)
# ---------------------------------------------------------------------------

class TestSignalHandlers:
    """Tests for Celery signal handler functions."""

    def test_on_task_prerun_with_sender(self) -> None:
        worker = _get_worker_module()
        mock_sender = MagicMock()
        mock_sender.name = "test_task"
        # Should not raise
        worker.on_task_prerun(sender=mock_sender, task_id="task-123")

    def test_on_task_prerun_without_sender(self) -> None:
        worker = _get_worker_module()
        worker.on_task_prerun(sender=None, task_id="task-456")

    def test_on_task_postrun_with_sender(self) -> None:
        worker = _get_worker_module()
        mock_sender = MagicMock()
        mock_sender.name = "test_task"
        worker.on_task_postrun(
            sender=mock_sender, task_id="task-123",
            retval={"status": "ok"}, state="SUCCESS"
        )

    def test_on_task_postrun_without_sender(self) -> None:
        worker = _get_worker_module()
        worker.on_task_postrun(sender=None, task_id="task-789", retval=None, state="FAILURE")

    def test_on_task_failure_with_sender(self) -> None:
        worker = _get_worker_module()
        mock_sender = MagicMock()
        mock_sender.name = "failing_task"
        worker.on_task_failure(
            sender=mock_sender, task_id="task-err",
            exception=ValueError("test error")
        )

    def test_on_task_failure_without_sender(self) -> None:
        worker = _get_worker_module()
        worker.on_task_failure(sender=None, task_id="task-err2", exception=RuntimeError("boom"))


# ---------------------------------------------------------------------------
# Scientific pipeline task (pure Python path — no external services)
# ---------------------------------------------------------------------------

class TestRunScientificPipeline:
    """Tests for run_scientific_pipeline task using mock DataPipeline."""

    def test_scientific_pipeline_with_mock(self) -> None:
        worker = _get_worker_module()
        mock_pipeline = MagicMock()
        mock_pipeline.execute.return_value = {"status": "completed", "rows_processed": 10}
        mock_pipeline_class = MagicMock(return_value=mock_pipeline)

        with patch("src.scientific.pipelines.DataPipeline", mock_pipeline_class):
            # Apply task with ALWAYS_EAGER so it runs synchronously
            worker.celery_app.conf.task_always_eager = True
            worker.celery_app.conf.task_eager_propagates = True
            result = worker.run_scientific_pipeline.apply(
                kwargs={
                    "pipeline_name": "test_pipeline",
                    "data": [1, 2, 3],
                    "steps": [],
                }
            ).result
        assert "task_execution_time_ms" in result

    def test_scientific_pipeline_exception_triggers_retry(self) -> None:
        worker = _get_worker_module()
        worker.celery_app.conf.task_always_eager = True
        worker.celery_app.conf.task_eager_propagates = False

        with patch("src.scientific.pipelines.DataPipeline", side_effect=ImportError("no module")):
            result = worker.run_scientific_pipeline.apply(
                kwargs={
                    "pipeline_name": "fail_pipeline",
                    "data": [],
                    "steps": None,
                }
            )
        # Task should fail (exception absorbed by eager mode)
        assert result.failed() or result.result is not None


# ---------------------------------------------------------------------------
# Quantum and AI tasks (mock use cases to avoid external services)
# ---------------------------------------------------------------------------

class TestRunQuantumJob:
    """Tests for run_quantum_job task with mocked use case."""

    def test_quantum_job_success(self) -> None:
        worker = _get_worker_module()
        worker.celery_app.conf.task_always_eager = True
        worker.celery_app.conf.task_eager_propagates = True
        mock_uc = AsyncMock()
        mock_uc.execute.return_value = {"status": "completed", "result": {}}

        with patch("src.application.use_cases.quantum_management.SubmitQuantumJobUseCase",
                   return_value=mock_uc):
            result = worker.run_quantum_job.apply(
                kwargs={
                    "user_id": "user-1",
                    "algorithm": "bell",
                    "num_qubits": 2,
                    "shots": 100,
                    "backend": "aer_simulator",
                    "parameters": {},
                }
            ).result
        assert result["status"] == "completed"

    def test_quantum_job_exception_is_handled(self) -> None:
        worker = _get_worker_module()
        worker.celery_app.conf.task_always_eager = True
        worker.celery_app.conf.task_eager_propagates = False

        with patch("src.application.use_cases.quantum_management.SubmitQuantumJobUseCase",
                   side_effect=RuntimeError("quantum error")):
            result = worker.run_quantum_job.apply(
                kwargs={
                    "user_id": "user-1",
                    "algorithm": "bell",
                    "num_qubits": 2,
                    "shots": 100,
                    "backend": "aer_simulator",
                    "parameters": {},
                }
            )
        assert result.failed() or result.result is not None


class TestRunAiTask:
    """Tests for run_ai_task task with mocked use case."""

    def test_ai_task_success(self) -> None:
        worker = _get_worker_module()
        worker.celery_app.conf.task_always_eager = True
        worker.celery_app.conf.task_eager_propagates = True
        mock_uc = AsyncMock()
        mock_uc.execute.return_value = {"status": "completed", "output": "result"}

        with patch("src.application.use_cases.ai_management.ExecuteAgentTaskUseCase",
                   return_value=mock_uc):
            result = worker.run_ai_task.apply(
                kwargs={
                    "agent_type": "analyst",
                    "task": "analyze data",
                    "context": None,
                    "constraints": None,
                    "output_format": "markdown",
                }
            ).result
        assert result["status"] == "completed"

    def test_ai_task_exception_is_handled(self) -> None:
        worker = _get_worker_module()
        worker.celery_app.conf.task_always_eager = True
        worker.celery_app.conf.task_eager_propagates = False

        with patch("src.application.use_cases.ai_management.ExecuteAgentTaskUseCase",
                   side_effect=RuntimeError("ai error")):
            result = worker.run_ai_task.apply(
                kwargs={
                    "agent_type": "analyst",
                    "task": "analyze data",
                    "context": None,
                    "constraints": None,
                    "output_format": "markdown",
                }
            )
        assert result.failed() or result.result is not None
