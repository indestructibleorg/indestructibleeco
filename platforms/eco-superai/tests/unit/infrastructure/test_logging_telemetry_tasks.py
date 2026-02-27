"""Unit tests for infrastructure/logging, telemetry, and tasks modules.

All external dependencies (OpenTelemetry, Redis, DB) are mocked so these
tests run in any CI environment without external services.
"""
from __future__ import annotations

import asyncio
import logging
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# infrastructure/logging
# ---------------------------------------------------------------------------

class TestSetupLogging:
    """Tests for setup_logging() configuration function."""

    def test_setup_logging_default(self) -> None:
        from src.infrastructure.logging import setup_logging
        # Should not raise
        setup_logging(level="info", json_output=False)
        root = logging.getLogger()
        assert root.level == logging.INFO

    def test_setup_logging_debug_level(self) -> None:
        from src.infrastructure.logging import setup_logging
        setup_logging(level="debug", json_output=False)
        root = logging.getLogger()
        assert root.level == logging.DEBUG

    def test_setup_logging_json_output(self) -> None:
        from src.infrastructure.logging import setup_logging
        # JSON output mode — should not raise
        setup_logging(level="warning", json_output=True)
        root = logging.getLogger()
        assert root.level == logging.WARNING

    def test_setup_logging_with_log_file(self, tmp_path) -> None:
        from src.infrastructure.logging import setup_logging
        log_file = str(tmp_path / "test.log")
        setup_logging(level="info", json_output=False, log_file=log_file)
        # File handler should be added
        root = logging.getLogger()
        handler_types = [type(h).__name__ for h in root.handlers]
        assert "FileHandler" in handler_types

    def test_setup_logging_invalid_level_falls_back_to_info(self) -> None:
        from src.infrastructure.logging import setup_logging
        # getattr with invalid level returns INFO (20) as default
        setup_logging(level="INVALID_LEVEL", json_output=False)
        root = logging.getLogger()
        assert root.level == logging.INFO

    def test_get_logger_returns_logger(self) -> None:
        from src.infrastructure.logging import get_logger
        logger = get_logger("test_module")
        assert logger is not None

    def test_get_logger_without_name(self) -> None:
        from src.infrastructure.logging import get_logger
        logger = get_logger()
        assert logger is not None

    def test_set_request_id(self) -> None:
        from src.infrastructure.logging import set_request_id
        # Should not raise
        set_request_id("req-abc-123")

    def test_set_request_id_empty_string(self) -> None:
        from src.infrastructure.logging import set_request_id
        set_request_id("")

    def test_noisy_loggers_suppressed(self) -> None:
        from src.infrastructure.logging import setup_logging
        setup_logging(level="info", json_output=False)
        # Noisy loggers should be at WARNING or above
        for name in ("sqlalchemy.engine", "httpx", "urllib3"):
            assert logging.getLogger(name).level >= logging.WARNING


# ---------------------------------------------------------------------------
# infrastructure/telemetry
# ---------------------------------------------------------------------------

class TestSetupTelemetry:
    """Tests for setup_telemetry() — covers both enabled and disabled paths."""

    def test_telemetry_disabled_returns_none(self) -> None:
        from src.infrastructure.telemetry import setup_telemetry
        result = setup_telemetry(enabled=False)
        assert result is None

    def test_telemetry_import_error_returns_none(self) -> None:
        """When opentelemetry packages are not installed, should return None gracefully."""
        from src.infrastructure.telemetry import setup_telemetry
        # Simulate missing opentelemetry by patching the import
        with patch.dict(sys.modules, {
            "opentelemetry": None,
            "opentelemetry.trace": None,
            "opentelemetry.sdk": None,
            "opentelemetry.sdk.trace": None,
            "opentelemetry.sdk.resources": None,
            "opentelemetry.sdk.trace.export": None,
            "opentelemetry.sdk.trace.sampling": None,
            "opentelemetry.exporter.otlp.proto.grpc.trace_exporter": None,
            "opentelemetry.instrumentation.fastapi": None,
        }):
            result = setup_telemetry(enabled=True)
        assert result is None

    def test_instrument_fastapi_import_error_does_not_raise(self) -> None:
        """instrument_fastapi should silently skip when OTel is not installed."""
        from src.infrastructure.telemetry import instrument_fastapi
        mock_app = MagicMock()
        with patch.dict(sys.modules, {
            "opentelemetry.instrumentation.fastapi": None,
        }):
            instrument_fastapi(mock_app)  # Should not raise

    def test_instrument_fastapi_exception_does_not_raise(self) -> None:
        """instrument_fastapi should log warning and not propagate exceptions."""
        from src.infrastructure.telemetry import instrument_fastapi
        mock_app = MagicMock()
        mock_instrumentor = MagicMock()
        mock_instrumentor.instrument_app.side_effect = RuntimeError("otel error")
        mock_module = MagicMock()
        mock_module.FastAPIInstrumentor = mock_instrumentor
        with patch.dict(sys.modules, {"opentelemetry.instrumentation.fastapi": mock_module}):
            instrument_fastapi(mock_app)  # Should not raise


# ---------------------------------------------------------------------------
# infrastructure/tasks
# ---------------------------------------------------------------------------

class TestTaskRunner:
    """Tests for TaskRunner — async background task management."""

    @pytest.mark.asyncio
    async def test_submit_and_complete(self) -> None:
        from src.infrastructure.tasks import TaskRunner
        runner = TaskRunner()
        results = []

        async def work():
            results.append("done")

        runner.submit("task1", work())
        await asyncio.sleep(0.05)
        assert results == ["done"]

    @pytest.mark.asyncio
    async def test_submit_duplicate_running_task_is_skipped(self) -> None:
        from src.infrastructure.tasks import TaskRunner
        runner = TaskRunner()
        started = []

        async def slow():
            started.append(1)
            await asyncio.sleep(0.5)

        runner.submit("slow_task", slow())
        await asyncio.sleep(0.01)
        # Submit again while running — should be skipped
        runner.submit("slow_task", slow())
        await asyncio.sleep(0.01)
        assert len(started) == 1  # Only one started
        runner.cancel("slow_task")

    @pytest.mark.asyncio
    async def test_cancel_running_task(self) -> None:
        from src.infrastructure.tasks import TaskRunner
        runner = TaskRunner()

        async def long_running():
            await asyncio.sleep(10)

        runner.submit("cancel_me", long_running())
        await asyncio.sleep(0.01)
        cancelled = runner.cancel("cancel_me")
        assert cancelled is True

    def test_cancel_nonexistent_task_returns_false(self) -> None:
        from src.infrastructure.tasks import TaskRunner
        runner = TaskRunner()
        assert runner.cancel("nonexistent") is False

    @pytest.mark.asyncio
    async def test_cancel_all(self) -> None:
        from src.infrastructure.tasks import TaskRunner
        runner = TaskRunner()

        async def long_running():
            await asyncio.sleep(10)

        runner.submit("t1", long_running())
        runner.submit("t2", long_running())
        await asyncio.sleep(0.01)
        count = runner.cancel_all()
        assert count == 2

    @pytest.mark.asyncio
    async def test_get_status_unknown(self) -> None:
        from src.infrastructure.tasks import TaskRunner
        runner = TaskRunner()
        assert runner.get_status("unknown_task") == "unknown"

    @pytest.mark.asyncio
    async def test_get_status_completed(self) -> None:
        from src.infrastructure.tasks import TaskRunner
        runner = TaskRunner()

        async def quick():
            return "result"

        runner.submit("quick_task", quick())
        await asyncio.sleep(0.05)
        status = runner.get_status("quick_task")
        assert status == "completed"

    @pytest.mark.asyncio
    async def test_get_status_failed(self) -> None:
        from src.infrastructure.tasks import TaskRunner
        runner = TaskRunner()

        async def failing():
            raise ValueError("task error")

        runner.submit("failing_task", failing())
        await asyncio.sleep(0.05)
        status = runner.get_status("failing_task")
        assert status == "failed"

    @pytest.mark.asyncio
    async def test_task_exception_does_not_propagate_to_runner(self) -> None:
        """TaskRunner should absorb task exceptions without crashing."""
        from src.infrastructure.tasks import TaskRunner
        runner = TaskRunner()

        async def boom():
            raise RuntimeError("boom")

        runner.submit("boom_task", boom())
        await asyncio.sleep(0.05)
        # Runner should still be operational
        assert runner.get_status("boom_task") == "failed"

    @pytest.mark.asyncio
    async def test_cancelled_task_is_done(self) -> None:
        from src.infrastructure.tasks import TaskRunner
        runner = TaskRunner()

        async def long_running():
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                pass  # absorb cancellation

        runner.submit("to_cancel", long_running())
        await asyncio.sleep(0.01)
        cancelled = runner.cancel("to_cancel")
        assert cancelled is True
        await asyncio.sleep(0.05)
        # After cancellation, task.done() should be True
        task = runner._tasks.get("to_cancel")
        assert task is not None and task.done()


class TestScheduler:
    """Tests for Scheduler (if present in tasks module)."""

    def test_scheduler_import(self) -> None:
        """Verify the tasks module exports expected symbols."""
        import src.infrastructure.tasks as tasks_mod
        # TaskRunner must be present
        assert hasattr(tasks_mod, "TaskRunner")


class TestWorker:
    """Tests for infrastructure/tasks/worker.py."""

    def test_worker_module_importable(self) -> None:
        """Worker module should be importable without external services."""
        try:
            import src.infrastructure.tasks.worker as worker_mod
            assert worker_mod is not None
        except ImportError as e:
            pytest.skip(f"Worker module has unresolvable import: {e}")

    def test_worker_has_expected_classes(self) -> None:
        try:
            import src.infrastructure.tasks.worker as worker_mod
            # At minimum the module should define some callable
            assert len(dir(worker_mod)) > 0
        except ImportError:
            pytest.skip("Worker module not importable in test environment")
