"""
GovOps Platform - ETL Layer
Handles data extraction, transformation, loading, and pipeline orchestration
for governance operations data.
"""

__version__ = "1.0.0"
__author__ = "GovOps Platform Team"
__description__ = "ETL layer for governance operations data pipelines"

from .extractors import (
    BaseExtractor,
    APIExtractor,
    DatabaseExtractor,
    LogExtractor,
    FileSystemExtractor,
)
from .transformers import (
    BaseTransformer,
    DataTransformer,
    DataValidator,
    GovernanceTransformer,
)
from .loaders import (
    BaseLoader,
    DatabaseLoader,
    FileLoader,
    EventStreamLoader,
)
from .pipeline import (
    ETLPipeline,
    PipelineConfig,
    PipelineRun,
)
from .sync import (
    ChangeTracker,
    SyncManager,
)

__all__ = [
    # Extractors
    "BaseExtractor",
    "APIExtractor",
    "DatabaseExtractor",
    "LogExtractor",
    "FileSystemExtractor",
    # Transformers
    "BaseTransformer",
    "DataTransformer",
    "DataValidator",
    "GovernanceTransformer",
    # Loaders
    "BaseLoader",
    "DatabaseLoader",
    "FileLoader",
    "EventStreamLoader",
    # Pipeline
    "ETLPipeline",
    "PipelineConfig",
    "PipelineRun",
    # Sync
    "ChangeTracker",
    "SyncManager",
]
