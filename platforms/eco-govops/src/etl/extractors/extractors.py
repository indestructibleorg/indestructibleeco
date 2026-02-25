"""Concrete extractor implementations for the GovOps ETL pipeline.

@GL-governed
@GL-layer: GL30-49
@GL-semantic: etl-extractors
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any

import structlog

from etl.extractors.base_extractor import BaseExtractor, Record

logger = structlog.get_logger(__name__)


class APIExtractor(BaseExtractor):
    """Extract governance data from REST API endpoints."""

    def __init__(self) -> None:
        super().__init__(name="api-extractor")

    async def extract(self, source_config: dict[str, Any]) -> AsyncIterator[Record]:
        url = source_config.get("url", "")
        self._log.info("api_extract_start", url=url)
        self.reset_counters()

        try:
            import httpx

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=source_config.get("headers", {}))
                response.raise_for_status()
                data = response.json()

                items = data if isinstance(data, list) else [data]
                for item in items:
                    yield self._make_record(
                        data=item,
                        source=url,
                        metadata={"status_code": response.status_code},
                    )
        except Exception as exc:
            self._errors += 1
            self._log.error("api_extract_error", url=url, error=str(exc))

    def validate_source(self, source_config: dict[str, Any]) -> bool:
        return bool(source_config.get("url"))

    def health_check(self) -> bool:
        return True


class DatabaseExtractor(BaseExtractor):
    """Extract governance data from database queries."""

    def __init__(self) -> None:
        super().__init__(name="database-extractor")

    async def extract(self, source_config: dict[str, Any]) -> AsyncIterator[Record]:
        query = source_config.get("query", "")
        dsn = source_config.get("dsn", "")
        self._log.info("db_extract_start", query=query[:100])
        self.reset_counters()

        try:
            import sqlalchemy
            from sqlalchemy.ext.asyncio import create_async_engine

            engine = create_async_engine(dsn)
            async with engine.connect() as conn:
                result = await conn.execute(sqlalchemy.text(query))
                columns = list(result.keys())
                for row in result:
                    yield self._make_record(
                        data=dict(zip(columns, row)),
                        source=f"db:{dsn.split('@')[-1] if '@' in dsn else 'local'}",
                    )
            await engine.dispose()
        except Exception as exc:
            self._errors += 1
            self._log.error("db_extract_error", error=str(exc))

    def validate_source(self, source_config: dict[str, Any]) -> bool:
        return bool(source_config.get("dsn") and source_config.get("query"))

    def health_check(self) -> bool:
        return True


class LogExtractor(BaseExtractor):
    """Extract governance events from structured log files."""

    def __init__(self) -> None:
        super().__init__(name="log-extractor")

    async def extract(self, source_config: dict[str, Any]) -> AsyncIterator[Record]:
        import json as json_mod
        from pathlib import Path

        log_path = Path(source_config.get("path", ""))
        self._log.info("log_extract_start", path=str(log_path))
        self.reset_counters()

        if not log_path.exists():
            self._errors += 1
            self._log.error("log_file_not_found", path=str(log_path))
            return

        with log_path.open("r") as fh:
            for line_num, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json_mod.loads(line)
                except (json_mod.JSONDecodeError, ValueError):
                    data = {"raw": line}
                yield self._make_record(
                    data=data,
                    source=str(log_path),
                    metadata={"line_number": line_num},
                )

    def validate_source(self, source_config: dict[str, Any]) -> bool:
        return bool(source_config.get("path"))

    def health_check(self) -> bool:
        return True


class FileSystemExtractor(BaseExtractor):
    """Extract governance data from filesystem directories."""

    def __init__(self) -> None:
        super().__init__(name="filesystem-extractor")

    async def extract(self, source_config: dict[str, Any]) -> AsyncIterator[Record]:
        import hashlib
        from pathlib import Path

        root = Path(source_config.get("root", "."))
        pattern = source_config.get("pattern", "**/*")
        self._log.info("fs_extract_start", root=str(root), pattern=pattern)
        self.reset_counters()

        if not root.is_dir():
            self._errors += 1
            self._log.error("fs_root_not_found", root=str(root))
            return

        for path in sorted(root.glob(pattern)):
            if path.is_file():
                try:
                    content = path.read_bytes()
                    yield self._make_record(
                        data={
                            "path": str(path.relative_to(root)),
                            "size": len(content),
                            "hash": hashlib.sha256(content).hexdigest(),
                        },
                        source=str(root),
                        metadata={"absolute_path": str(path)},
                    )
                except Exception as exc:
                    self._errors += 1
                    self._log.warning("fs_extract_skip", path=str(path), error=str(exc))

    def validate_source(self, source_config: dict[str, Any]) -> bool:
        return bool(source_config.get("root"))

    def health_check(self) -> bool:
        return True
