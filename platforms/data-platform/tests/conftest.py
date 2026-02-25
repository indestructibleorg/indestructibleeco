"""Test conftest — shared fixtures for data platform tests."""

import pytest

from data_platform.engines.evidence_engine import EvidenceEngine
from data_platform.engines.quality_engine import QualityEngine
from data_platform.engines.replay_engine import ReplayEngine
from data_platform.domain.entities import EvidenceRecord, QualityRule
from data_platform.domain.value_objects import EvidenceType


@pytest.fixture
def evidence_engine() -> EvidenceEngine:
    return EvidenceEngine()


@pytest.fixture
def quality_engine() -> QualityEngine:
    return QualityEngine(threshold=0.8)


@pytest.fixture
def replay_engine() -> ReplayEngine:
    return ReplayEngine()


@pytest.fixture
def sample_evidence_records() -> list[EvidenceRecord]:
    """Three evidence records that can form a chain."""
    return [
        EvidenceRecord(id="rec-001", type=EvidenceType.FILE, payload={"path": "/data/input.csv"}),
        EvidenceRecord(id="rec-002", type=EvidenceType.LOG, payload={"message": "ingested 100 rows"}),
        EvidenceRecord(id="rec-003", type=EvidenceType.METRIC, payload={"row_count": 100, "errors": 0}),
    ]


@pytest.fixture
def sample_data() -> list[dict]:
    """Sample data rows for quality testing."""
    return [
        {"name": "Alice", "age": 30, "email": "alice@example.com", "id": 1},
        {"name": "Bob", "age": 25, "email": "bob@example.com", "id": 2},
        {"name": "Charlie", "age": 35, "email": "charlie@example.com", "id": 3},
        {"name": "", "age": -5, "email": "invalid", "id": 4},
        {"name": "Eve", "age": 150, "email": "eve@test.org", "id": 5},
    ]


@pytest.fixture
def sample_rules() -> list[QualityRule]:
    """Quality rules for the sample data."""
    return [
        QualityRule(name="name_not_null", field="name", check_type="not_null"),
        QualityRule(
            name="age_range",
            field="age",
            check_type="range",
            parameters={"min": 0, "max": 120},
        ),
        QualityRule(
            name="email_format",
            field="email",
            check_type="regex",
            parameters={"pattern": r"^[\w.+-]+@[\w-]+\.[\w.]+$"},
        ),
        QualityRule(name="id_unique", field="id", check_type="unique"),
    ]


@pytest.fixture
def sample_events() -> list[dict]:
    """Sample events for replay testing."""
    return [
        {"type": "start", "data": {"pipeline": "etl-1"}},
        {"type": "ingest", "data": {"rows": 100}},
        {"type": "validate", "data": {"errors": 2}},
        {"type": "transform", "data": {"transforms": ["clean", "normalize"]}},
        {"type": "store", "data": {"destination": "warehouse"}},
    ]
