"""Test replay session domain entity."""

from domain.entities.replay_session import ReplayMode, ReplaySession, ReplayStatus


def test_replay_session_creation():
    s = ReplaySession(
        mode=ReplayMode.FULL,
        start_sequence=0,
        end_sequence=100,
    )
    assert s.mode == ReplayMode.FULL
    assert s.status == ReplayStatus.ACTIVE
    assert s.start_sequence == 0
    assert s.end_sequence == 100
    assert s.events_replayed == 0
    assert s.reconstructed_state == {}


def test_replay_session_hash_deterministic():
    s = ReplaySession(
        id="session-001",
        mode=ReplayMode.PARTIAL,
        start_sequence=10,
        end_sequence=50,
    )
    hash1 = s.session_hash
    hash2 = s.session_hash
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex digest


def test_replay_session_hash_differs_by_mode():
    s1 = ReplaySession(id="s1", mode=ReplayMode.FULL, start_sequence=0)
    s2 = ReplaySession(id="s1", mode=ReplayMode.DIFFERENTIAL, start_sequence=0)
    assert s1.session_hash != s2.session_hash


def test_replay_is_complete():
    s = ReplaySession(mode=ReplayMode.FULL, start_sequence=0)
    assert s.is_complete is False
    s.status = ReplayStatus.COMPLETED
    assert s.is_complete is True


def test_replay_mode_enum_values():
    assert ReplayMode.FULL.value == "FULL"
    assert ReplayMode.PARTIAL.value == "PARTIAL"
    assert ReplayMode.POINT_IN_TIME.value == "POINT_IN_TIME"
    assert ReplayMode.DIFFERENTIAL.value == "DIFFERENTIAL"


def test_replay_status_enum_values():
    assert ReplayStatus.ACTIVE.value == "ACTIVE"
    assert ReplayStatus.COMPLETED.value == "COMPLETED"
    assert ReplayStatus.FAILED.value == "FAILED"
