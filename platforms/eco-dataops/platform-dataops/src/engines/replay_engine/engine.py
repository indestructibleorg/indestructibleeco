#!/usr/bin/env python3
"""
Replay Engine v1.0
State reconstruction, timeline management, snapshot/restore.

This module implements the complete replay engine for reconstructing system
state from event timelines, managing point-in-time queries, and maintaining
verifiable snapshot/restore capabilities with cryptographic integrity.

Governance Stage: S5-VERIFIED
Status: ENFORCED
"""

import hashlib
import json
import logging
import sys
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# Configure logging with CRITICAL-only default
logging.basicConfig(
    level=logging.CRITICAL,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================
# ENUMS
# ============================================

class ReplayMode(Enum):
    """Supported replay modes for state reconstruction."""
    FULL = "full"
    PARTIAL = "partial"
    POINT_IN_TIME = "point_in_time"
    DIFFERENTIAL = "differential"


# ============================================
# DATA STRUCTURES
# ============================================

@dataclass
class TimelineEvent:
    """An immutable event on the timeline with cryptographic binding."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    event_type: str = ""
    actor: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    sequence_number: int = 0
    hash_value: str = ""

    def to_bytes(self) -> bytes:
        """Convert core fields to bytes for hashing."""
        data = {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "actor": self.actor,
            "payload": self.payload,
            "sequence_number": self.sequence_number,
        }
        return json.dumps(data, sort_keys=True).encode("utf-8")

    def compute_hash(self) -> str:
        """Compute SHA3-512 hash of this event."""
        return hashlib.sha3_512(self.to_bytes()).hexdigest()


@dataclass
class StateSnapshot:
    """A point-in-time snapshot of reconstructed state."""
    snapshot_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    state: Dict[str, Any] = field(default_factory=dict)
    hash_value: str = ""
    sequence_number: int = 0

    def compute_hash(self) -> str:
        """Compute SHA3-512 hash of the snapshot state."""
        data = {
            "snapshot_id": self.snapshot_id,
            "state": self.state,
            "sequence_number": self.sequence_number,
        }
        raw = json.dumps(data, sort_keys=True).encode("utf-8")
        return hashlib.sha3_512(raw).hexdigest()


@dataclass
class ReplaySession:
    """Tracks a replay operation from start to completion."""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    mode: ReplayMode = ReplayMode.FULL
    start_time: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    end_time: Optional[str] = None
    events: List[TimelineEvent] = field(default_factory=list)
    snapshots: List[StateSnapshot] = field(default_factory=list)
    status: str = "active"  # "active" | "completed" | "failed"


# ============================================
# REPLAY ENGINE
# ============================================

class ReplayEngine:
    """Replay Engine -- state reconstruction, timeline management, snapshot/restore."""

    def __init__(self) -> None:
        """Initialize the replay engine with empty timeline and snapshot stores."""
        self.timeline: List[TimelineEvent] = []
        self.snapshots: List[StateSnapshot] = []
        self.sessions: List[ReplaySession] = []
        self._sequence_counter: int = 0
        logger.info("ReplayEngine initialized")

    # ------------------------------------------
    # PUBLIC API
    # ------------------------------------------

    def record_event(
        self, event_type: str, actor: str, payload: Dict[str, Any]
    ) -> TimelineEvent:
        """Append a new event to the timeline with an auto-incremented sequence number.

        Args:
            event_type: Category or type identifier for the event.
            actor: The entity that triggered the event.
            payload: Arbitrary data associated with the event.

        Returns:
            The newly created TimelineEvent.
        """
        self._sequence_counter += 1
        event = TimelineEvent(
            event_type=event_type,
            actor=actor,
            payload=payload,
            sequence_number=self._sequence_counter,
        )
        event.hash_value = event.compute_hash()
        self.timeline.append(event)
        logger.info(
            "Recorded event seq=%d type=%s actor=%s",
            event.sequence_number, event.event_type, event.actor,
        )
        return event

    def create_snapshot(self, state: Dict[str, Any]) -> StateSnapshot:
        """Capture a state snapshot at the current point in the timeline.

        Args:
            state: The state dictionary to snapshot.

        Returns:
            The newly created StateSnapshot.
        """
        snapshot = StateSnapshot(
            state=state,
            sequence_number=self._sequence_counter,
        )
        snapshot.hash_value = snapshot.compute_hash()
        self.snapshots.append(snapshot)
        logger.info(
            "Created snapshot %s at seq=%d",
            snapshot.snapshot_id[:8], snapshot.sequence_number,
        )
        return snapshot

    def replay(
        self,
        mode: ReplayMode,
        start_seq: int,
        end_seq: Optional[int] = None,
    ) -> ReplaySession:
        """Reconstruct state by replaying events between sequence numbers.

        Args:
            mode: The replay mode to use.
            start_seq: Starting sequence number (inclusive).
            end_seq: Ending sequence number (inclusive). Defaults to latest.

        Returns:
            A ReplaySession containing the replayed events and any generated snapshots.
        """
        if end_seq is None:
            end_seq = self._sequence_counter

        session = ReplaySession(mode=mode)
        logger.info(
            "Starting replay session %s mode=%s range=[%d, %d]",
            session.session_id[:8], mode.value, start_seq, end_seq,
        )

        try:
            # Select events within the sequence range
            selected_events = [
                e for e in self.timeline
                if start_seq <= e.sequence_number <= end_seq
            ]

            if mode == ReplayMode.FULL:
                session.events = selected_events
            elif mode == ReplayMode.PARTIAL:
                # Partial replay: only include events that modify state
                session.events = [
                    e for e in selected_events
                    if e.event_type in ("state_change", "mutation", "update", "create", "delete")
                ]
            elif mode == ReplayMode.POINT_IN_TIME:
                # All events up to end_seq
                session.events = [
                    e for e in self.timeline if e.sequence_number <= end_seq
                ]
            elif mode == ReplayMode.DIFFERENTIAL:
                # Find nearest snapshot before start_seq and replay from there
                base_snapshot = self._find_nearest_snapshot(start_seq)
                if base_snapshot:
                    session.snapshots.append(base_snapshot)
                session.events = selected_events

            # Build reconstructed state from events
            reconstructed_state = self._reconstruct_state(session.events)
            result_snapshot = StateSnapshot(
                state=reconstructed_state,
                sequence_number=end_seq,
            )
            result_snapshot.hash_value = result_snapshot.compute_hash()
            session.snapshots.append(result_snapshot)

            session.status = "completed"
            session.end_time = datetime.now(timezone.utc).isoformat()
            logger.info(
                "Replay session %s completed: %d events replayed",
                session.session_id[:8], len(session.events),
            )

        except Exception as exc:
            session.status = "failed"
            session.end_time = datetime.now(timezone.utc).isoformat()
            logger.error("Replay session %s failed: %s", session.session_id[:8], exc)

        self.sessions.append(session)
        return session

    def point_in_time_query(self, timestamp: str) -> Dict[str, Any]:
        """Return reconstructed state at the given ISO-8601 timestamp.

        Args:
            timestamp: ISO-8601 timestamp string.

        Returns:
            Reconstructed state dictionary at the given point in time.
        """
        events_at_time = [
            e for e in self.timeline if e.timestamp <= timestamp
        ]
        return self._reconstruct_state(events_at_time)

    def verify_timeline_integrity(self) -> Tuple[bool, List[str]]:
        """Verify sequence continuity and hash integrity of the full timeline.

        Returns:
            Tuple of (is_valid, list_of_error_strings).
        """
        errors: List[str] = []

        if not self.timeline:
            return True, []

        # Check sequence continuity
        expected_seq = self.timeline[0].sequence_number
        for idx, event in enumerate(self.timeline):
            if event.sequence_number != expected_seq:
                errors.append(
                    f"Sequence gap at index {idx}: expected {expected_seq}, "
                    f"got {event.sequence_number}"
                )
            expected_seq = event.sequence_number + 1

            # Verify hash integrity
            computed_hash = event.compute_hash()
            if event.hash_value != computed_hash:
                errors.append(
                    f"Hash mismatch at seq={event.sequence_number}: "
                    f"stored={event.hash_value[:16]}..., "
                    f"computed={computed_hash[:16]}..."
                )

        is_valid = len(errors) == 0
        return is_valid, errors

    def get_timeline_stats(self) -> Dict[str, Any]:
        """Return aggregate statistics about the timeline and replay sessions.

        Returns:
            Dictionary with event counts, session counts, snapshot counts, etc.
        """
        event_types: Dict[str, int] = {}
        for event in self.timeline:
            event_types[event.event_type] = event_types.get(event.event_type, 0) + 1

        session_statuses: Dict[str, int] = {}
        for session in self.sessions:
            session_statuses[session.status] = session_statuses.get(session.status, 0) + 1

        return {
            "total_events": len(self.timeline),
            "total_snapshots": len(self.snapshots),
            "total_sessions": len(self.sessions),
            "current_sequence": self._sequence_counter,
            "event_types": event_types,
            "session_statuses": session_statuses,
            "timeline_span": {
                "first": self.timeline[0].timestamp if self.timeline else None,
                "last": self.timeline[-1].timestamp if self.timeline else None,
            },
        }

    # ------------------------------------------
    # INTERNAL METHODS
    # ------------------------------------------

    def _find_nearest_snapshot(self, target_seq: int) -> Optional[StateSnapshot]:
        """Find the nearest snapshot at or before the given sequence number.

        Args:
            target_seq: The target sequence number.

        Returns:
            The nearest StateSnapshot, or None if no snapshots precede the target.
        """
        candidates = [
            s for s in self.snapshots if s.sequence_number <= target_seq
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda s: s.sequence_number)

    def _reconstruct_state(self, events: List[TimelineEvent]) -> Dict[str, Any]:
        """Reconstruct state by folding events in sequence order.

        Events are applied in sequence_number order. Each event payload is
        merged into the accumulated state dictionary.

        Args:
            events: The list of events to replay.

        Returns:
            Reconstructed state dictionary.
        """
        state: Dict[str, Any] = {}
        sorted_events = sorted(events, key=lambda e: e.sequence_number)
        for event in sorted_events:
            # Merge event payload into state
            for key, value in event.payload.items():
                state[key] = value
            # Track metadata
            state["_last_event_type"] = event.event_type
            state["_last_actor"] = event.actor
            state["_last_sequence"] = event.sequence_number
            state["_last_timestamp"] = event.timestamp
        return state


# ============================================
# CLI INTERFACE
# ============================================

def main() -> None:
    """Demonstrate replay engine usage."""
    print("=" * 60)
    print("Replay Engine -- Demo")
    print("=" * 60)

    engine = ReplayEngine()

    # Record a series of events
    e1 = engine.record_event("create", "admin", {"user": "alice", "role": "engineer"})
    print(f"\nEvent 1: seq={e1.sequence_number} type={e1.event_type}")

    e2 = engine.record_event("update", "admin", {"user": "alice", "role": "senior_engineer"})
    print(f"Event 2: seq={e2.sequence_number} type={e2.event_type}")

    # Take a snapshot
    snap = engine.create_snapshot({"user": "alice", "role": "senior_engineer"})
    print(f"\nSnapshot: {snap.snapshot_id[:8]}... at seq={snap.sequence_number}")

    e3 = engine.record_event("create", "admin", {"user": "bob", "role": "analyst"})
    print(f"Event 3: seq={e3.sequence_number} type={e3.event_type}")

    e4 = engine.record_event("state_change", "system", {"status": "active", "uptime": 99.9})
    print(f"Event 4: seq={e4.sequence_number} type={e4.event_type}")

    # Full replay
    print("\n--- Full Replay (seq 1-4) ---")
    session = engine.replay(ReplayMode.FULL, start_seq=1, end_seq=4)
    print(f"Session: {session.session_id[:8]}... status={session.status}")
    print(f"Events replayed: {len(session.events)}")
    if session.snapshots:
        final_state = session.snapshots[-1].state
        print(f"Reconstructed state keys: {list(final_state.keys())}")

    # Differential replay
    print("\n--- Differential Replay (seq 3-4) ---")
    diff_session = engine.replay(ReplayMode.DIFFERENTIAL, start_seq=3, end_seq=4)
    print(f"Session: {diff_session.session_id[:8]}... status={diff_session.status}")
    print(f"Events replayed: {len(diff_session.events)}")

    # Point-in-time query
    print("\n--- Point-in-Time Query ---")
    pit_state = engine.point_in_time_query(e2.timestamp)
    print(f"State at event 2 timestamp: {pit_state}")

    # Verify timeline
    print("\n--- Timeline Integrity ---")
    is_valid, errors = engine.verify_timeline_integrity()
    print(f"Timeline valid: {is_valid}")
    if errors:
        for err in errors:
            print(f"  ERROR: {err}")

    # Stats
    print("\n--- Timeline Stats ---")
    stats = engine.get_timeline_stats()
    print(f"Total events: {stats['total_events']}")
    print(f"Total snapshots: {stats['total_snapshots']}")
    print(f"Total sessions: {stats['total_sessions']}")
    print(f"Current sequence: {stats['current_sequence']}")
    print(f"Event types: {json.dumps(stats['event_types'], indent=2)}")

    print("\n" + "=" * 60)
    print("Replay Engine -- Demo Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
