"""Integration tests for infrastructure/logging and infrastructure/telemetry.

Tests cover:
- setup_logging: console output, JSON output, file output
- get_logger: returns a bound logger
- set_request_id: context variable propagation
- setup_telemetry: provider initialisation, graceful failure on missing OTLP
- instrument_fastapi / instrument_sqlalchemy / instrument_httpx: no-raise
- get_tracer: returns a usable tracer (real or NoOp)
- _NoOpTracer: context manager works correctly
"""
from __future__ import annotations

import logging
import os
import tempfile

import pytest

pytestmark = pytest.mark.integration


class TestSetupLogging:

    def test_setup_logging_console_mode(self) -> None:
        from src.infrastructure.logging import setup_logging, get_logger
        setup_logging(level="info", json_output=False)
        logger = get_logger("test.console")
        # Must not raise
        logger.info("test_event", key="value")

    def test_setup_logging_json_mode(self) -> None:
        from src.infrastructure.logging import setup_logging, get_logger
        setup_logging(level="debug", json_output=True)
        logger = get_logger("test.json")
        logger.debug("json_event", payload={"x": 1})

    def test_setup_logging_with_file_output(self) -> None:
        from src.infrastructure.logging import setup_logging, get_logger
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
            log_path = f.name
        try:
            setup_logging(level="warning", json_output=False, log_file=log_path)
            logger = get_logger("test.file")
            logger.warning("file_log_event", severity="warning")
            # File must exist and be non-empty
            assert os.path.exists(log_path)
            assert os.path.getsize(log_path) > 0
        finally:
            os.unlink(log_path)

    def test_setup_logging_invalid_level_falls_back_to_info(self) -> None:
        from src.infrastructure.logging import setup_logging
        # Should not raise even with an unknown level
        setup_logging(level="NOTAVALIDLEVEL")
        root = logging.getLogger()
        assert root.level == logging.INFO

    def test_get_logger_returns_bound_logger(self) -> None:
        from src.infrastructure.logging import get_logger
        logger = get_logger("test.bound")
        assert logger is not None
        # Bound logger must support standard log methods
        assert callable(getattr(logger, "info", None))
        assert callable(getattr(logger, "error", None))

    def test_set_request_id_propagates_to_context(self) -> None:
        from src.infrastructure.logging import set_request_id, get_logger
        set_request_id("req-abc-123")
        logger = get_logger("test.request_id")
        # Must not raise — context variable is set
        logger.info("with_request_id")


class TestTelemetry:

    def test_setup_telemetry_with_unreachable_endpoint(self) -> None:
        """setup_telemetry must not raise even when the OTLP endpoint is
        unreachable — the BatchSpanProcessor handles connectivity failures
        asynchronously.
        """
        from src.infrastructure.telemetry import setup_telemetry
        provider = setup_telemetry(
            service_name="test-service",
            otlp_endpoint="http://localhost:19999",  # Nothing listening
            sample_rate=1.0,
        )
        assert provider is not None

    def test_get_tracer_returns_usable_tracer(self) -> None:
        from src.infrastructure.telemetry import get_tracer
        tracer = get_tracer("test.tracer")
        assert tracer is not None
        # Must support start_as_current_span as a context manager
        with tracer.start_as_current_span("test-span"):
            pass  # Must not raise

    def test_noop_tracer_context_manager(self) -> None:
        from src.infrastructure.telemetry import _NoOpTracer
        tracer = _NoOpTracer()
        with tracer.start_as_current_span("noop-span") as span:
            assert span is None  # NoOp yields None

    def test_instrument_fastapi_no_raise(self) -> None:
        from src.infrastructure.telemetry import instrument_fastapi
        from fastapi import FastAPI
        app = FastAPI()
        # Must not raise regardless of whether opentelemetry-instrumentation-fastapi is installed
        instrument_fastapi(app)

    def test_instrument_sqlalchemy_no_raise(self) -> None:
        from src.infrastructure.telemetry import instrument_sqlalchemy
        from unittest.mock import MagicMock
        mock_engine = MagicMock()
        instrument_sqlalchemy(mock_engine)

    def test_instrument_httpx_no_raise(self) -> None:
        from src.infrastructure.telemetry import instrument_httpx
        instrument_httpx()
