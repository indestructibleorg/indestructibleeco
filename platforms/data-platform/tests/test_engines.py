"""Tests for data platform engines — evidence, quality, and replay."""

import pytest

from data_platform.engines.evidence_engine import EvidenceEngine
from data_platform.engines.quality_engine import QualityEngine, QualityReport, FieldResult
from data_platform.engines.replay_engine import ReplayEngine
from data_platform.domain.entities import EvidenceRecord, QualityRule, ReplaySession
from data_platform.domain.value_objects import EvidenceType, QualityScore, ReplayMode
from data_platform.domain.exceptions import (
    EvidenceChainError,
    QualityCheckError,
    ReplayError,
)


# ===========================================================================
# EvidenceEngine
# ===========================================================================


class TestEvidenceEngineIngest:
    def test_ingest_single_record(self, evidence_engine: EvidenceEngine):
        record = EvidenceRecord(
            type=EvidenceType.FILE,
            payload={"path": "/data/file.csv"},
        )
        result = evidence_engine.ingest(record)
        assert result.hash
        assert len(result.hash) == 64
        assert evidence_engine.record_count == 1

    def test_ingest_computes_hash(self, evidence_engine: EvidenceEngine):
        record = EvidenceRecord(
            type=EvidenceType.LOG,
            payload={"msg": "hello"},
        )
        evidence_engine.ingest(record)
        assert record.hash != ""
        assert record.verify_hash() is True

    def test_ingest_chains_to_parent(self, evidence_engine: EvidenceEngine):
        parent = EvidenceRecord(id="parent-1", type=EvidenceType.FILE, payload={"x": 1})
        evidence_engine.ingest(parent)

        child = EvidenceRecord(
            id="child-1",
            type=EvidenceType.LOG,
            payload={"x": 2},
            parent_id="parent-1",
        )
        result = evidence_engine.ingest(child)
        assert result.parent_id == "parent-1"
        assert evidence_engine.record_count == 2

    def test_ingest_rejects_missing_parent(self, evidence_engine: EvidenceEngine):
        record = EvidenceRecord(
            type=EvidenceType.EVENT,
            payload={"data": "test"},
            parent_id="nonexistent",
        )
        with pytest.raises(EvidenceChainError, match="not found"):
            evidence_engine.ingest(record)

    def test_ingest_emits_event(self, evidence_engine: EvidenceEngine):
        record = EvidenceRecord(type=EvidenceType.METRIC, payload={"cpu": 0.5})
        evidence_engine.ingest(record)
        assert len(evidence_engine.events) == 1
        event = evidence_engine.events[0]
        assert event.evidence_id == record.id
        assert event.evidence_type == "metric"
        assert event.hash == record.hash


class TestEvidenceEngineChaining:
    def test_three_record_chain(self, evidence_engine: EvidenceEngine):
        r1 = EvidenceRecord(id="r1", type=EvidenceType.FILE, payload={"step": 1})
        r2 = EvidenceRecord(id="r2", type=EvidenceType.LOG, payload={"step": 2}, parent_id="r1")
        r3 = EvidenceRecord(id="r3", type=EvidenceType.METRIC, payload={"step": 3}, parent_id="r2")

        evidence_engine.ingest(r1)
        evidence_engine.ingest(r2)
        evidence_engine.ingest(r3)

        assert evidence_engine.record_count == 3
        assert evidence_engine.verify_chain() is True

    def test_chain_ordering(
        self,
        evidence_engine: EvidenceEngine,
        sample_evidence_records: list[EvidenceRecord],
    ):
        # Chain the sample records
        records = sample_evidence_records
        evidence_engine.ingest(records[0])
        records[1].parent_id = records[0].id
        evidence_engine.ingest(records[1])
        records[2].parent_id = records[1].id
        evidence_engine.ingest(records[2])

        assert evidence_engine.verify_chain() is True


class TestEvidenceEngineVerification:
    def test_verify_empty_chain(self, evidence_engine: EvidenceEngine):
        assert evidence_engine.verify_chain() is True

    def test_verify_valid_chain(self, evidence_engine: EvidenceEngine):
        r1 = EvidenceRecord(id="a", type=EvidenceType.FILE, payload={"data": "test"})
        r2 = EvidenceRecord(id="b", type=EvidenceType.LOG, payload={"msg": "ok"}, parent_id="a")
        evidence_engine.ingest(r1)
        evidence_engine.ingest(r2)
        assert evidence_engine.verify_chain() is True

    def test_verify_detects_tampered_hash(self, evidence_engine: EvidenceEngine):
        record = EvidenceRecord(id="t1", type=EvidenceType.FILE, payload={"x": 1})
        evidence_engine.ingest(record)

        # Tamper with the payload after ingestion
        record.payload["x"] = 999

        with pytest.raises(EvidenceChainError, match="Hash mismatch"):
            evidence_engine.verify_chain()


class TestEvidenceEngineQuery:
    def test_query_all(self, evidence_engine: EvidenceEngine):
        for i in range(3):
            evidence_engine.ingest(
                EvidenceRecord(type=EvidenceType.FILE, payload={"i": i})
            )
        results = evidence_engine.query()
        assert len(results) == 3

    def test_query_by_type(self, evidence_engine: EvidenceEngine):
        evidence_engine.ingest(EvidenceRecord(type=EvidenceType.FILE, payload={"a": 1}))
        evidence_engine.ingest(EvidenceRecord(type=EvidenceType.LOG, payload={"b": 2}))
        evidence_engine.ingest(EvidenceRecord(type=EvidenceType.FILE, payload={"c": 3}))

        results = evidence_engine.query({"type": EvidenceType.FILE})
        assert len(results) == 2

    def test_query_by_type_string(self, evidence_engine: EvidenceEngine):
        evidence_engine.ingest(EvidenceRecord(type=EvidenceType.LOG, payload={"x": 1}))
        results = evidence_engine.query({"type": "log"})
        assert len(results) == 1

    def test_query_by_parent_id(self, evidence_engine: EvidenceEngine):
        r1 = EvidenceRecord(id="p1", type=EvidenceType.FILE, payload={"x": 1})
        r2 = EvidenceRecord(type=EvidenceType.LOG, payload={"y": 2}, parent_id="p1")
        r3 = EvidenceRecord(type=EvidenceType.LOG, payload={"z": 3}, parent_id="p1")
        evidence_engine.ingest(r1)
        evidence_engine.ingest(r2)
        evidence_engine.ingest(r3)

        results = evidence_engine.query({"parent_id": "p1"})
        assert len(results) == 2

    def test_query_has_parent(self, evidence_engine: EvidenceEngine):
        r1 = EvidenceRecord(id="root", type=EvidenceType.FILE, payload={"x": 1})
        r2 = EvidenceRecord(type=EvidenceType.LOG, payload={"y": 2}, parent_id="root")
        evidence_engine.ingest(r1)
        evidence_engine.ingest(r2)

        with_parent = evidence_engine.query({"has_parent": True})
        assert len(with_parent) == 1

        without_parent = evidence_engine.query({"has_parent": False})
        assert len(without_parent) == 1

    def test_get_by_id(self, evidence_engine: EvidenceEngine):
        record = EvidenceRecord(id="lookup-1", type=EvidenceType.FILE, payload={"a": 1})
        evidence_engine.ingest(record)
        result = evidence_engine.get("lookup-1")
        assert result is not None
        assert result.id == "lookup-1"

    def test_get_missing_returns_none(self, evidence_engine: EvidenceEngine):
        result = evidence_engine.get("nonexistent")
        assert result is None


# ===========================================================================
# QualityEngine
# ===========================================================================


class TestQualityEngineBasic:
    def test_evaluate_empty_data(self, quality_engine: QualityEngine):
        rules = [QualityRule(name="r1", field="x", check_type="not_null")]
        report = quality_engine.evaluate([], rules)
        assert report.overall_score.value == 1.0
        assert report.passed is True

    def test_evaluate_no_rules(self, quality_engine: QualityEngine):
        data = [{"x": 1}]
        report = quality_engine.evaluate(data, [])
        assert report.overall_score.value == 1.0
        assert report.rule_count == 0

    def test_evaluate_emits_event(self, quality_engine: QualityEngine):
        data = [{"x": 1}]
        rules = [QualityRule(name="r1", field="x", check_type="not_null")]
        quality_engine.evaluate(data, rules)
        assert len(quality_engine.events) == 1
        assert quality_engine.events[0].rule_count == 1


class TestQualityEngineNotNull:
    def test_all_present(self, quality_engine: QualityEngine):
        data = [{"name": "Alice"}, {"name": "Bob"}, {"name": "Charlie"}]
        rules = [QualityRule(name="name_present", field="name", check_type="not_null")]
        report = quality_engine.evaluate(data, rules)
        assert report.field_results[0].score.value == 1.0

    def test_some_missing(self, quality_engine: QualityEngine):
        data = [{"name": "Alice"}, {"name": None}, {"name": "Charlie"}]
        rules = [QualityRule(name="name_present", field="name", check_type="not_null")]
        report = quality_engine.evaluate(data, rules)
        assert abs(report.field_results[0].score.value - 2 / 3) < 0.001

    def test_empty_string_fails(self, quality_engine: QualityEngine):
        data = [{"name": ""}, {"name": "Bob"}]
        rules = [QualityRule(name="name_present", field="name", check_type="not_null")]
        report = quality_engine.evaluate(data, rules)
        assert report.field_results[0].passed_records == 1

    def test_missing_field_fails(self, quality_engine: QualityEngine):
        data = [{"other": 1}, {"name": "Bob"}]
        rules = [QualityRule(name="name_present", field="name", check_type="not_null")]
        report = quality_engine.evaluate(data, rules)
        assert report.field_results[0].passed_records == 1


class TestQualityEngineRange:
    def test_all_in_range(self, quality_engine: QualityEngine):
        data = [{"age": 25}, {"age": 30}, {"age": 35}]
        rules = [
            QualityRule(
                name="age_range", field="age", check_type="range",
                parameters={"min": 0, "max": 120},
            )
        ]
        report = quality_engine.evaluate(data, rules)
        assert report.field_results[0].score.value == 1.0

    def test_some_out_of_range(self, quality_engine: QualityEngine):
        data = [{"age": 25}, {"age": -5}, {"age": 150}]
        rules = [
            QualityRule(
                name="age_range", field="age", check_type="range",
                parameters={"min": 0, "max": 120},
            )
        ]
        report = quality_engine.evaluate(data, rules)
        assert abs(report.field_results[0].score.value - 1 / 3) < 0.001

    def test_non_numeric_fails_range(self, quality_engine: QualityEngine):
        data = [{"age": "not_a_number"}, {"age": 25}]
        rules = [
            QualityRule(
                name="age_range", field="age", check_type="range",
                parameters={"min": 0, "max": 120},
            )
        ]
        report = quality_engine.evaluate(data, rules)
        assert report.field_results[0].passed_records == 1


class TestQualityEngineRegex:
    def test_all_match(self, quality_engine: QualityEngine):
        data = [
            {"email": "alice@example.com"},
            {"email": "bob@test.org"},
        ]
        rules = [
            QualityRule(
                name="email_format", field="email", check_type="regex",
                parameters={"pattern": r"^[\w.+-]+@[\w-]+\.[\w.]+$"},
            )
        ]
        report = quality_engine.evaluate(data, rules)
        assert report.field_results[0].score.value == 1.0

    def test_some_dont_match(self, quality_engine: QualityEngine):
        data = [
            {"email": "alice@example.com"},
            {"email": "invalid"},
            {"email": "bob@test.org"},
        ]
        rules = [
            QualityRule(
                name="email_format", field="email", check_type="regex",
                parameters={"pattern": r"^[\w.+-]+@[\w-]+\.[\w.]+$"},
            )
        ]
        report = quality_engine.evaluate(data, rules)
        assert abs(report.field_results[0].score.value - 2 / 3) < 0.001

    def test_missing_pattern_raises(self, quality_engine: QualityEngine):
        data = [{"x": "val"}]
        rules = [
            QualityRule(name="bad_regex", field="x", check_type="regex", parameters={})
        ]
        with pytest.raises(QualityCheckError, match="pattern"):
            quality_engine.evaluate(data, rules)


class TestQualityEngineUnique:
    def test_all_unique(self, quality_engine: QualityEngine):
        data = [{"id": 1}, {"id": 2}, {"id": 3}]
        rules = [QualityRule(name="id_unique", field="id", check_type="unique")]
        report = quality_engine.evaluate(data, rules)
        assert report.field_results[0].score.value == 1.0

    def test_some_duplicates(self, quality_engine: QualityEngine):
        data = [{"id": 1}, {"id": 2}, {"id": 1}]
        rules = [QualityRule(name="id_unique", field="id", check_type="unique")]
        report = quality_engine.evaluate(data, rules)
        # 2 unique values out of 3 records
        assert abs(report.field_results[0].score.value - 2 / 3) < 0.001


class TestQualityEngineOverallScore:
    def test_overall_is_average(self, quality_engine: QualityEngine, sample_data, sample_rules):
        report = quality_engine.evaluate(sample_data, sample_rules)
        # Overall score should be average of individual scores
        individual_scores = [r.score.value for r in report.field_results]
        expected = sum(individual_scores) / len(individual_scores)
        assert abs(report.overall_score.value - expected) < 0.001

    def test_report_metadata(self, quality_engine: QualityEngine, sample_data, sample_rules):
        report = quality_engine.evaluate(sample_data, sample_rules)
        assert report.metadata["record_count"] == len(sample_data)
        assert report.metadata["rule_count"] == len(sample_rules)

    def test_unknown_check_type(self, quality_engine: QualityEngine):
        data = [{"x": 1}]
        rules = [QualityRule(name="bad", field="x", check_type="unknown_type")]
        with pytest.raises(QualityCheckError, match="Unknown check type"):
            quality_engine.evaluate(data, rules)


class TestQualityEngineFieldResult:
    def test_field_result_properties(self, quality_engine: QualityEngine):
        data = [{"x": 1}, {"x": None}, {"x": 3}]
        rules = [QualityRule(name="x_check", field="x", check_type="not_null")]
        report = quality_engine.evaluate(data, rules)
        fr = report.field_results[0]
        assert fr.rule_name == "x_check"
        assert fr.field_name == "x"
        assert fr.check_type == "not_null"
        assert fr.total_records == 3
        assert fr.passed_records == 2
        assert fr.failed_records == 1


# ===========================================================================
# ReplayEngine
# ===========================================================================


class TestReplayEngineSessionLifecycle:
    def test_create_session(self, replay_engine: ReplayEngine, sample_events):
        session = replay_engine.create_session(sample_events)
        assert session.id
        assert len(session.events) == 5
        assert session.position == 0
        assert session.mode == ReplayMode.SEQUENTIAL
        assert replay_engine.session_count == 1

    def test_create_session_with_mode(self, replay_engine: ReplayEngine, sample_events):
        session = replay_engine.create_session(sample_events, mode=ReplayMode.STEP_BY_STEP)
        assert session.mode == ReplayMode.STEP_BY_STEP

    def test_get_session(self, replay_engine: ReplayEngine, sample_events):
        created = replay_engine.create_session(sample_events)
        fetched = replay_engine.get_session(created.id)
        assert fetched.id == created.id

    def test_get_nonexistent_session(self, replay_engine: ReplayEngine):
        with pytest.raises(ReplayError, match="not found"):
            replay_engine.get_session("nonexistent")

    def test_delete_session(self, replay_engine: ReplayEngine, sample_events):
        session = replay_engine.create_session(sample_events)
        replay_engine.delete_session(session.id)
        assert replay_engine.session_count == 0

    def test_delete_nonexistent_session(self, replay_engine: ReplayEngine):
        with pytest.raises(ReplayError, match="not found"):
            replay_engine.delete_session("nonexistent")


class TestReplayEngineStep:
    def test_step_returns_current_event(self, replay_engine: ReplayEngine, sample_events):
        session = replay_engine.create_session(sample_events)
        event = replay_engine.step(session.id)
        assert event == sample_events[0]

    def test_step_advances_position(self, replay_engine: ReplayEngine, sample_events):
        session = replay_engine.create_session(sample_events)
        replay_engine.step(session.id)
        state = replay_engine.get_state(session.id)
        assert state["position"] == 1

    def test_step_through_all_events(self, replay_engine: ReplayEngine, sample_events):
        session = replay_engine.create_session(sample_events)
        collected = []
        for _ in range(len(sample_events)):
            event = replay_engine.step(session.id)
            collected.append(event)
        assert collected == sample_events

    def test_step_past_end_returns_none(self, replay_engine: ReplayEngine, sample_events):
        session = replay_engine.create_session(sample_events)
        for _ in range(len(sample_events)):
            replay_engine.step(session.id)
        result = replay_engine.step(session.id)
        assert result is None

    def test_step_emits_completion_event(self, replay_engine: ReplayEngine, sample_events):
        session = replay_engine.create_session(sample_events)
        for _ in range(len(sample_events)):
            replay_engine.step(session.id)
        assert len(replay_engine.events) == 1
        assert replay_engine.events[0].session_id == session.id
        assert replay_engine.events[0].total_events == len(sample_events)


class TestReplayEngineFastForward:
    def test_fast_forward(self, replay_engine: ReplayEngine, sample_events):
        session = replay_engine.create_session(sample_events)
        traversed = replay_engine.fast_forward(session.id, 3)
        assert len(traversed) == 3
        assert traversed == sample_events[:3]

    def test_fast_forward_past_end(self, replay_engine: ReplayEngine, sample_events):
        session = replay_engine.create_session(sample_events)
        traversed = replay_engine.fast_forward(session.id, 100)
        assert len(traversed) == len(sample_events)
        state = replay_engine.get_state(session.id)
        assert state["is_complete"] is True

    def test_fast_forward_zero(self, replay_engine: ReplayEngine, sample_events):
        session = replay_engine.create_session(sample_events)
        traversed = replay_engine.fast_forward(session.id, 0)
        assert traversed == []
        state = replay_engine.get_state(session.id)
        assert state["position"] == 0

    def test_fast_forward_negative_raises(self, replay_engine: ReplayEngine, sample_events):
        session = replay_engine.create_session(sample_events)
        with pytest.raises(ReplayError, match="non-negative"):
            replay_engine.fast_forward(session.id, -1)


class TestReplayEngineRewind:
    def test_rewind(self, replay_engine: ReplayEngine, sample_events):
        session = replay_engine.create_session(sample_events)
        replay_engine.fast_forward(session.id, 4)
        new_pos = replay_engine.rewind(session.id, 2)
        assert new_pos == 2

    def test_rewind_past_start(self, replay_engine: ReplayEngine, sample_events):
        session = replay_engine.create_session(sample_events)
        replay_engine.fast_forward(session.id, 2)
        new_pos = replay_engine.rewind(session.id, 100)
        assert new_pos == 0

    def test_rewind_zero(self, replay_engine: ReplayEngine, sample_events):
        session = replay_engine.create_session(sample_events)
        replay_engine.fast_forward(session.id, 3)
        new_pos = replay_engine.rewind(session.id, 0)
        assert new_pos == 3

    def test_rewind_negative_raises(self, replay_engine: ReplayEngine, sample_events):
        session = replay_engine.create_session(sample_events)
        with pytest.raises(ReplayError, match="non-negative"):
            replay_engine.rewind(session.id, -1)


class TestReplayEngineGetState:
    def test_get_state_initial(self, replay_engine: ReplayEngine, sample_events):
        session = replay_engine.create_session(sample_events)
        state = replay_engine.get_state(session.id)
        assert state["session_id"] == session.id
        assert state["position"] == 0
        assert state["current_event"] == sample_events[0]
        assert state["total_events"] == 5
        assert state["is_complete"] is False
        assert state["remaining"] == 5
        assert state["mode"] == "sequential"

    def test_get_state_after_step(self, replay_engine: ReplayEngine, sample_events):
        session = replay_engine.create_session(sample_events)
        replay_engine.step(session.id)
        state = replay_engine.get_state(session.id)
        assert state["position"] == 1
        assert state["remaining"] == 4

    def test_get_state_when_complete(self, replay_engine: ReplayEngine, sample_events):
        session = replay_engine.create_session(sample_events)
        replay_engine.fast_forward(session.id, len(sample_events))
        state = replay_engine.get_state(session.id)
        assert state["is_complete"] is True
        assert state["remaining"] == 0
        assert state["current_event"] is None

    def test_get_state_nonexistent_raises(self, replay_engine: ReplayEngine):
        with pytest.raises(ReplayError, match="not found"):
            replay_engine.get_state("nonexistent")
