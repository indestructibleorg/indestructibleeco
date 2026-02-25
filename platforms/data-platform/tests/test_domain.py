"""Tests for data platform domain layer — entities, value objects, events, exceptions."""

import pytest

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


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------


class TestEvidenceType:
    def test_all_members(self):
        assert set(EvidenceType) == {
            EvidenceType.FILE,
            EvidenceType.LOG,
            EvidenceType.METRIC,
            EvidenceType.EVENT,
            EvidenceType.ASSERTION,
        }

    def test_string_values(self):
        assert EvidenceType.FILE.value == "file"
        assert EvidenceType.LOG.value == "log"
        assert EvidenceType.METRIC.value == "metric"

    def test_from_string(self):
        assert EvidenceType("event") == EvidenceType.EVENT


class TestPipelinePhase:
    def test_all_phases(self):
        assert set(PipelinePhase) == {
            PipelinePhase.INGEST,
            PipelinePhase.VALIDATE,
            PipelinePhase.TRANSFORM,
            PipelinePhase.STORE,
        }

    def test_string_values(self):
        assert PipelinePhase.INGEST.value == "ingest"
        assert PipelinePhase.STORE.value == "store"


class TestReplayMode:
    def test_all_modes(self):
        assert set(ReplayMode) == {
            ReplayMode.SEQUENTIAL,
            ReplayMode.FAST_FORWARD,
            ReplayMode.STEP_BY_STEP,
        }


class TestQualityScore:
    def test_passing_score(self):
        score = QualityScore(value=0.9, threshold=0.8)
        assert score.passed is True
        assert score.failed is False

    def test_failing_score(self):
        score = QualityScore(value=0.5, threshold=0.8)
        assert score.passed is False
        assert score.failed is True

    def test_exact_threshold_passes(self):
        score = QualityScore(value=0.8, threshold=0.8)
        assert score.passed is True

    def test_default_threshold(self):
        score = QualityScore(value=0.85)
        assert score.threshold == 0.8
        assert score.passed is True

    def test_value_bounds_low(self):
        with pytest.raises(ValueError, match="0.0-1.0"):
            QualityScore(value=-0.1)

    def test_value_bounds_high(self):
        with pytest.raises(ValueError, match="0.0-1.0"):
            QualityScore(value=1.1)

    def test_threshold_bounds(self):
        with pytest.raises(ValueError, match="threshold"):
            QualityScore(value=0.5, threshold=1.5)

    def test_str_representation(self):
        score = QualityScore(value=0.9, threshold=0.8)
        result = str(score)
        assert "0.900" in result
        assert "PASS" in result

    def test_str_fail_representation(self):
        score = QualityScore(value=0.3, threshold=0.8)
        result = str(score)
        assert "FAIL" in result

    def test_immutable(self):
        score = QualityScore(value=0.5)
        with pytest.raises(AttributeError):
            score.value = 0.9  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------


class TestEvidenceRecord:
    def test_default_values(self):
        record = EvidenceRecord()
        assert record.id
        assert record.type == EvidenceType.EVENT
        assert record.payload == {}
        assert record.hash == ""
        assert record.parent_id is None
        assert record.timestamp > 0

    def test_compute_hash(self):
        record = EvidenceRecord(
            type=EvidenceType.FILE,
            payload={"path": "/data/input.csv"},
        )
        h = record.compute_hash()
        assert h
        assert len(h) == 64  # SHA-256 hex digest
        assert record.hash == h

    def test_verify_hash_valid(self):
        record = EvidenceRecord(
            type=EvidenceType.LOG,
            payload={"msg": "test"},
        )
        record.compute_hash()
        assert record.verify_hash() is True

    def test_verify_hash_after_tamper(self):
        record = EvidenceRecord(
            type=EvidenceType.LOG,
            payload={"msg": "test"},
        )
        record.compute_hash()
        record.payload["msg"] = "tampered"
        assert record.verify_hash() is False

    def test_hash_includes_parent(self):
        r1 = EvidenceRecord(type=EvidenceType.FILE, payload={"x": 1})
        r2 = EvidenceRecord(type=EvidenceType.FILE, payload={"x": 1}, parent_id="abc")
        r1.compute_hash()
        r2.compute_hash()
        assert r1.hash != r2.hash

    def test_hash_includes_type(self):
        r1 = EvidenceRecord(type=EvidenceType.FILE, payload={"x": 1})
        r2 = EvidenceRecord(type=EvidenceType.LOG, payload={"x": 1})
        r1.compute_hash()
        r2.compute_hash()
        assert r1.hash != r2.hash

    def test_deterministic_hash(self):
        r1 = EvidenceRecord(id="a", type=EvidenceType.FILE, payload={"k": "v"})
        r2 = EvidenceRecord(id="b", type=EvidenceType.FILE, payload={"k": "v"})
        assert r1.compute_hash() == r2.compute_hash()


class TestDataPipeline:
    def test_default_state(self):
        pipeline = DataPipeline(name="etl")
        assert pipeline.status == "idle"
        assert pipeline.phases == []

    def test_advance_through_phases(self):
        pipeline = DataPipeline(
            name="etl",
            phases=[PipelinePhase.INGEST, PipelinePhase.VALIDATE, PipelinePhase.STORE],
        )
        assert pipeline.status == "idle"

        phase = pipeline.advance()
        assert phase == PipelinePhase.INGEST
        assert pipeline.status == "ingest"

        phase = pipeline.advance()
        assert phase == PipelinePhase.VALIDATE
        assert pipeline.status == "validate"

        phase = pipeline.advance()
        assert phase == PipelinePhase.STORE
        assert pipeline.status == "store"

        phase = pipeline.advance()
        assert phase is None
        assert pipeline.status == "completed"

    def test_advance_empty_pipeline(self):
        pipeline = DataPipeline(name="empty", phases=[])
        phase = pipeline.advance()
        assert phase is None


class TestQualityRule:
    def test_creation(self):
        rule = QualityRule(name="not_null_check", field="email", check_type="not_null")
        assert rule.name == "not_null_check"
        assert rule.field == "email"
        assert rule.check_type == "not_null"
        assert rule.threshold == 0.0
        assert rule.parameters == {}

    def test_with_parameters(self):
        rule = QualityRule(
            name="range_check",
            field="age",
            check_type="range",
            parameters={"min": 0, "max": 120},
        )
        assert rule.parameters["min"] == 0
        assert rule.parameters["max"] == 120

    def test_immutable(self):
        rule = QualityRule(name="test", field="x", check_type="not_null")
        with pytest.raises(AttributeError):
            rule.name = "changed"  # type: ignore[misc]


class TestReplaySession:
    def test_default_state(self):
        session = ReplaySession()
        assert session.events == []
        assert session.position == 0
        assert session.mode == ReplayMode.SEQUENTIAL
        assert session.is_complete is True
        assert session.current_event is None

    def test_with_events(self):
        events = [{"type": "a"}, {"type": "b"}, {"type": "c"}]
        session = ReplaySession(events=events)
        assert session.current_event == {"type": "a"}
        assert session.is_complete is False
        assert session.remaining == 3

    def test_position_tracking(self):
        events = [{"type": "a"}, {"type": "b"}]
        session = ReplaySession(events=events, position=1)
        assert session.current_event == {"type": "b"}
        assert session.remaining == 1

    def test_is_complete(self):
        session = ReplaySession(events=[{"x": 1}], position=1)
        assert session.is_complete is True
        assert session.current_event is None


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


class TestDomainEvents:
    def test_evidence_ingested(self):
        event = EvidenceIngested(
            evidence_id="rec-1",
            evidence_type="file",
            hash="abc123",
        )
        assert event.evidence_id == "rec-1"
        assert event.evidence_type == "file"
        assert event.hash == "abc123"
        assert event.parent_id is None
        assert event.event_id
        assert event.timestamp > 0

    def test_quality_checked(self):
        event = QualityChecked(
            rule_count=3,
            overall_score=0.95,
            passed=True,
        )
        assert event.rule_count == 3
        assert event.overall_score == 0.95
        assert event.passed is True

    def test_replay_completed(self):
        event = ReplayCompleted(
            session_id="sess-1",
            total_events=10,
            final_position=10,
        )
        assert event.session_id == "sess-1"
        assert event.total_events == 10
        assert event.final_position == 10


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class TestExceptions:
    def test_data_platform_error(self):
        err = DataPlatformError("something failed")
        assert str(err) == "something failed"
        assert err.code == "DATA_PLATFORM_ERROR"

    def test_evidence_chain_error(self):
        err = EvidenceChainError("chain broken", record_id="rec-1")
        assert "chain broken" in str(err)
        assert err.record_id == "rec-1"
        assert err.code == "EVIDENCE_CHAIN_ERROR"

    def test_quality_check_error(self):
        err = QualityCheckError("rule failed", rule_name="not_null")
        assert err.rule_name == "not_null"
        assert err.code == "QUALITY_CHECK_ERROR"

    def test_replay_error(self):
        err = ReplayError("session error", session_id="sess-1")
        assert err.session_id == "sess-1"
        assert err.code == "REPLAY_ERROR"

    def test_inheritance(self):
        from platform_shared.domain.errors import PlatformError

        err = DataPlatformError("test")
        assert isinstance(err, PlatformError)

        err2 = EvidenceChainError("test")
        assert isinstance(err2, DataPlatformError)
        assert isinstance(err2, PlatformError)
