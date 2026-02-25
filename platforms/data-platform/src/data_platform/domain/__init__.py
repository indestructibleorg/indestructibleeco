"""Data Platform domain — entities, value objects, events, and exceptions."""

from data_platform.domain.entities import (
    DataPipeline,
    EvidenceRecord,
    QualityRule,
    ReplaySession,
)
from data_platform.domain.value_objects import (
    EvidenceType,
    PipelinePhase,
    QualityScore,
    ReplayMode,
)
from data_platform.domain.events import (
    EvidenceIngested,
    QualityChecked,
    ReplayCompleted,
)
from data_platform.domain.exceptions import (
    DataPlatformError,
    EvidenceChainError,
    QualityCheckError,
    ReplayError,
)

__all__ = [
    "DataPipeline",
    "EvidenceRecord",
    "QualityRule",
    "ReplaySession",
    "EvidenceType",
    "PipelinePhase",
    "QualityScore",
    "ReplayMode",
    "EvidenceIngested",
    "QualityChecked",
    "ReplayCompleted",
    "DataPlatformError",
    "EvidenceChainError",
    "QualityCheckError",
    "ReplayError",
]
