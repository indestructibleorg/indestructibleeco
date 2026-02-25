"""Concrete loader implementations for the GovOps ETL pipeline.

Loaders receive transformed Records and write them to target destinations
(databases, files, event streams).

@GL-governed
@GL-layer: GL30-49
@GL-semantic: etl-loaders
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog

from etl.extractors.base_extractor import Record

logger = structlog.get_logger(__name__)


class BaseLoader(ABC):
    """Abstract base class for all data loaders."""

    def __init__(self, name: str = "base-loader") -> None:
        self.name = name
        self._log = logger.bind(loader=name)
        self._records_loaded: int = 0
        self._errors: int = 0

    @abstractmethod
    async def load(self, records: list[Record], target_config: dict[str, Any]) -> int:
        """Load records to the target destination.

        Returns the number of records successfully loaded.
        """
        ...

    @property
    def metrics(self) -> dict[str, Any]:
        return {
            "loader": self.name,
            "records_loaded": self._records_loaded,
            "errors": self._errors,
        }


class DatabaseLoader(BaseLoader):
    """Load records into a database via SQLAlchemy."""

    def __init__(self) -> None:
        super().__init__(name="database-loader")

    async def load(self, records: list[Record], target_config: dict[str, Any]) -> int:
        table = target_config.get("table", "governance_records")
        dsn = target_config.get("dsn", "")
        self._log.info("db_load_start", table=table, count=len(records))

        loaded = 0
        try:
            import sqlalchemy
            from sqlalchemy.ext.asyncio import create_async_engine

            engine = create_async_engine(dsn)
            async with engine.begin() as conn:
                for record in records:
                    row = {
                        **record.data,
                        "source": record.source,
                        "extracted_at": record.timestamp.isoformat(),
                        "loaded_at": datetime.now(timezone.utc).isoformat(),
                    }
                    await conn.execute(
                        sqlalchemy.text(
                            f"INSERT INTO {table} (data) VALUES (:data)"
                        ),
                        {"data": json.dumps(row, default=str)},
                    )
                    loaded += 1
            await engine.dispose()
        except Exception as exc:
            self._errors += 1
            self._log.error("db_load_error", error=str(exc))

        self._records_loaded += loaded
        return loaded


class FileLoader(BaseLoader):
    """Load records as JSONL files to disk."""

    def __init__(self) -> None:
        super().__init__(name="file-loader")

    async def load(self, records: list[Record], target_config: dict[str, Any]) -> int:
        output_path = Path(target_config.get("path", "output.jsonl"))
        self._log.info("file_load_start", path=str(output_path), count=len(records))

        output_path.parent.mkdir(parents=True, exist_ok=True)

        loaded = 0
        try:
            with output_path.open("a") as fh:
                for record in records:
                    line = json.dumps(
                        {
                            "data": record.data,
                            "source": record.source,
                            "timestamp": record.timestamp.isoformat(),
                            "metadata": record.metadata,
                        },
                        default=str,
                    )
                    fh.write(line + "\n")
                    loaded += 1
        except Exception as exc:
            self._errors += 1
            self._log.error("file_load_error", error=str(exc))

        self._records_loaded += loaded
        return loaded


class EventStreamLoader(BaseLoader):
    """Load records to an event stream (Redis Streams / message queue)."""

    def __init__(self) -> None:
        super().__init__(name="event-stream-loader")

    async def load(self, records: list[Record], target_config: dict[str, Any]) -> int:
        stream = target_config.get("stream", "governance-events")
        redis_url = target_config.get("redis_url", "redis://localhost:6379")
        self._log.info("stream_load_start", stream=stream, count=len(records))

        loaded = 0
        try:
            import redis.asyncio as aioredis

            client = aioredis.from_url(redis_url)
            for record in records:
                payload = {
                    "data": json.dumps(record.data, default=str),
                    "source": record.source,
                    "timestamp": record.timestamp.isoformat(),
                }
                await client.xadd(stream, payload)
                loaded += 1
            await client.aclose()
        except Exception as exc:
            self._errors += 1
            self._log.error("stream_load_error", error=str(exc))

        self._records_loaded += loaded
        return loaded
