"""ETL pipeline orchestrator for the GovOps Platform.

Coordinates extractors, transformers, and loaders into a cohesive pipeline
that can be executed as a standalone CLI or embedded in the larger platform.

@GL-governed
@GL-layer: GL30-49
@GL-semantic: etl-pipeline
"""
from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import structlog

from etl.extractors.base_extractor import BaseExtractor, Record
from etl.transformers.transformers import BaseTransformer
from etl.loaders.loaders import BaseLoader

logger = structlog.get_logger(__name__)


class PipelineStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PipelineConfig:
    """Configuration for a pipeline run."""

    name: str = "default-pipeline"
    batch_size: int = 100
    source_config: dict[str, Any] = field(default_factory=dict)
    target_config: dict[str, Any] = field(default_factory=dict)
    max_records: int = 0  # 0 = unlimited


@dataclass
class PipelineRun:
    """Tracks the state of a single pipeline execution."""

    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pipeline_name: str = ""
    status: PipelineStatus = PipelineStatus.PENDING
    records_extracted: int = 0
    records_transformed: int = 0
    records_loaded: int = 0
    errors: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None

    @property
    def duration_seconds(self) -> float | None:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def as_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "pipeline_name": self.pipeline_name,
            "status": self.status.value,
            "records_extracted": self.records_extracted,
            "records_transformed": self.records_transformed,
            "records_loaded": self.records_loaded,
            "errors": self.errors,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
        }


class ETLPipeline:
    """Orchestrates extract → transform → load stages.

    Usage::

        pipeline = ETLPipeline(
            extractors=[APIExtractor()],
            transformers=[GovernanceTransformer()],
            loaders=[FileLoader()],
        )
        run = await pipeline.execute(config)
    """

    def __init__(
        self,
        extractors: list[BaseExtractor] | None = None,
        transformers: list[BaseTransformer] | None = None,
        loaders: list[BaseLoader] | None = None,
    ) -> None:
        self.extractors = extractors or []
        self.transformers = transformers or []
        self.loaders = loaders or []
        self._log = logger.bind(component="etl-pipeline")
        self._history: list[PipelineRun] = []

    async def execute(self, config: PipelineConfig) -> PipelineRun:
        """Run the full ETL pipeline and return the run report."""
        run = PipelineRun(pipeline_name=config.name)
        run.status = PipelineStatus.RUNNING
        run.started_at = datetime.now(timezone.utc)
        self._log.info("pipeline_start", run_id=run.run_id, name=config.name)

        try:
            # Extract
            records: list[Record] = []
            for extractor in self.extractors:
                async for record in extractor.extract(config.source_config):
                    records.append(record)
                    run.records_extracted += 1
                    if config.max_records and run.records_extracted >= config.max_records:
                        break
                if config.max_records and run.records_extracted >= config.max_records:
                    break

            # Transform (apply each transformer sequentially)
            for transformer in self.transformers:
                records = await transformer.transform_batch(records)
            run.records_transformed = len(records)

            # Load (send to all loaders)
            for loader in self.loaders:
                for i in range(0, len(records), config.batch_size):
                    batch = records[i : i + config.batch_size]
                    loaded = await loader.load(batch, config.target_config)
                    run.records_loaded += loaded

            run.status = PipelineStatus.COMPLETED
        except Exception as exc:
            run.status = PipelineStatus.FAILED
            run.errors += 1
            self._log.error("pipeline_error", run_id=run.run_id, error=str(exc))
        finally:
            run.completed_at = datetime.now(timezone.utc)
            self._history.append(run)
            self._log.info(
                "pipeline_complete",
                run_id=run.run_id,
                status=run.status.value,
                duration=run.duration_seconds,
            )

        return run

    @property
    def history(self) -> list[PipelineRun]:
        return list(self._history)


def main() -> None:
    """CLI entry point for ``govops-etl``."""
    import argparse

    parser = argparse.ArgumentParser(description="GovOps ETL Pipeline")
    parser.add_argument("--name", default="cli-pipeline", help="Pipeline run name")
    parser.add_argument("--source-path", default=".", help="Source path for filesystem extractor")
    parser.add_argument("--output", default="output.jsonl", help="Output file path")
    args = parser.parse_args()

    from etl.extractors.extractors import FileSystemExtractor
    from etl.transformers.transformers import GovernanceTransformer
    from etl.loaders.loaders import FileLoader

    pipeline = ETLPipeline(
        extractors=[FileSystemExtractor()],
        transformers=[GovernanceTransformer()],
        loaders=[FileLoader()],
    )

    config = PipelineConfig(
        name=args.name,
        source_config={"root": args.source_path, "pattern": "**/*.json"},
        target_config={"path": args.output},
    )

    run = asyncio.run(pipeline.execute(config))
    print(f"Pipeline {run.status.value}: {run.records_loaded} records loaded in {run.duration_seconds:.2f}s")


if __name__ == "__main__":
    main()
