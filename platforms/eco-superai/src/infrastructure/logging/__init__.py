"""Structured logging configuration -- structlog + stdlib integration.

Provides a single :func:`setup_logging` entry-point that configures
**structlog** and Python's built-in :mod:`logging` so that every log
statement (including third-party libraries that use ``logging.getLogger``)
flows through a unified processor pipeline and renderer.

Processors added to every log event:

* **timestamp** -- UTC ISO-8601 / RFC-3339 (``2024-01-15T09:23:01.123Z``)
* **log level** -- standard ``debug`` / ``info`` / ``warning`` / ``error`` /
  ``critical``
* **logger name** -- the ``__name__`` of the calling module
* **caller info** -- file, function, line number (debug/dev only by default)
* **request_id** -- pulled from :mod:`structlog.contextvars` (set by
  ``request_id_middleware`` in the FastAPI stack)

In **production** (``json_output=True``), events are rendered as single-line
JSON objects suitable for ingestion by Elasticsearch / Loki / CloudWatch.
In **development** (``json_output=False``), events are rendered with colours
and human-friendly formatting via :class:`structlog.dev.ConsoleRenderer`.
"""
from __future__ import annotations

import logging
import sys
from contextvars import ContextVar
from typing import Any

import structlog

# ---------------------------------------------------------------------------
# Context variable for request_id (set by middleware, read by processor)
# ---------------------------------------------------------------------------

_request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")


def _add_request_id(
    logger: Any,
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """Structlog processor that injects ``request_id`` from contextvars."""
    rid = _request_id_ctx.get("")
    if rid:
        event_dict.setdefault("request_id", rid)
    return event_dict


def _add_caller_info(
    logger: Any,
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """Structlog processor that adds caller file, function and line."""
    record = event_dict.get("_record")
    if record is not None:
        event_dict["caller"] = f"{record.pathname}:{record.lineno}"
        event_dict["function"] = record.funcName
    return event_dict


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def setup_logging(
    level: str = "info",
    json_output: bool = False,
    log_file: str | None = None,
) -> None:
    """Configure structlog with stdlib logging integration.

    Args:
        level: Log level string (``debug``, ``info``, ``warning``, ``error``,
            ``critical``).
        json_output: If ``True``, output JSON lines (production); otherwise
            human-readable coloured output (development).
        log_file: Optional file path for log output **in addition** to
            stderr.  File output is always JSON regardless of
            ``json_output``.
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # ------------------------------------------------------------------ #
    # Shared processors (used by both structlog and stdlib foreign loggers)
    # ------------------------------------------------------------------ #
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        _add_request_id,
        _add_caller_info,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    # ------------------------------------------------------------------ #
    # Renderer selection
    # ------------------------------------------------------------------ #
    if json_output:
        renderer: Any = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(
            colors=sys.stderr.isatty(),
            pad_event=40,
        )

    # ------------------------------------------------------------------ #
    # structlog configuration
    # ------------------------------------------------------------------ #
    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # ------------------------------------------------------------------ #
    # stdlib logging configuration
    # ------------------------------------------------------------------ #
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=shared_processors,
    )

    # Console handler (stderr)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)

    handlers: list[logging.Handler] = [console_handler]

    # Optional file handler (always JSON for machine ingestion)
    if log_file:
        file_formatter = structlog.stdlib.ProcessorFormatter(
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.processors.JSONRenderer(),
            ],
            foreign_pre_chain=shared_processors,
        )
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(file_formatter)
        handlers.append(file_handler)

    # Apply to root logger so that all stdlib loggers (including
    # third-party libraries) flow through structlog's renderer.
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(log_level)
    for handler in handlers:
        root_logger.addHandler(handler)

    # Suppress noisy third-party loggers that spam at INFO/DEBUG
    for noisy in (
        "uvicorn.access",
        "sqlalchemy.engine",
        "httpx",
        "httpcore",
        "urllib3",
        "asyncio",
        "aiohttp",
        "botocore",
        "celery",
    ):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    structlog.get_logger().info(
        "logging_configured",
        level=level,
        json_output=json_output,
        log_file=log_file or "none",
    )


def get_logger(name: str | None = None) -> Any:
    """Return a structlog bound logger.

    This is a thin convenience wrapper so that callers do not need to import
    structlog directly::

        from src.infrastructure.logging import get_logger
        logger = get_logger(__name__)
    """
    return structlog.get_logger(name)


def set_request_id(request_id: str) -> None:
    """Store a request ID in the current context variable.

    Prefer using ``structlog.contextvars.bind_contextvars(request_id=...)``
    directly (which the middleware already does).  This helper exists for
    non-HTTP code paths (Celery tasks, CLI commands) that want the
    ``request_id`` to appear in log events.
    """
    _request_id_ctx.set(request_id)


__all__ = ["setup_logging", "get_logger", "set_request_id"]
