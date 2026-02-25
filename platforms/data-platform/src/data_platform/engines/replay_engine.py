"""ReplayEngine — replay event sequences for debugging and analysis.

Creates replay sessions that can step through, fast-forward, or rewind
through event sequences.
"""

from __future__ import annotations

from typing import Any

from data_platform.domain.entities import ReplaySession
from data_platform.domain.events import ReplayCompleted
from data_platform.domain.exceptions import ReplayError
from data_platform.domain.value_objects import ReplayMode


class ReplayEngine:
    """Manages replay session lifecycle and navigation."""

    def __init__(self) -> None:
        self._sessions: dict[str, ReplaySession] = {}
        self._events: list[ReplayCompleted] = []

    def create_session(
        self,
        events: list[dict[str, Any]],
        mode: ReplayMode = ReplayMode.SEQUENTIAL,
    ) -> ReplaySession:
        """Create a new replay session with the given events.

        Args:
            events: Ordered list of event dictionaries to replay.
            mode: Replay mode (sequential, fast_forward, step_by_step).

        Returns:
            The created ReplaySession.
        """
        session = ReplaySession(events=list(events), position=0, mode=mode)
        self._sessions[session.id] = session
        return session

    def get_session(self, session_id: str) -> ReplaySession:
        """Retrieve a session by id."""
        session = self._sessions.get(session_id)
        if session is None:
            raise ReplayError(
                f"Session '{session_id}' not found",
                session_id=session_id,
            )
        return session

    def step(self, session_id: str) -> dict[str, Any] | None:
        """Advance the session by one event, returning the event at the new position.

        Returns the current event before advancing, or None if already complete.
        """
        session = self.get_session(session_id)

        if session.is_complete:
            return None

        event = session.current_event
        session.position += 1

        # If we've reached the end, emit a completion event
        if session.is_complete:
            self._emit_completion(session)

        return event

    def fast_forward(self, session_id: str, n: int) -> list[dict[str, Any]]:
        """Advance the session by up to n events, returning all traversed events.

        Args:
            session_id: Session to advance.
            n: Maximum number of events to advance.

        Returns:
            List of events traversed during the fast-forward.
        """
        session = self.get_session(session_id)

        if n < 0:
            raise ReplayError(
                "fast_forward count must be non-negative",
                session_id=session_id,
            )

        traversed: list[dict[str, Any]] = []
        for _ in range(n):
            if session.is_complete:
                break
            event = session.current_event
            if event is not None:
                traversed.append(event)
            session.position += 1

        if session.is_complete:
            self._emit_completion(session)

        return traversed

    def rewind(self, session_id: str, n: int) -> int:
        """Move the session backward by up to n events.

        Args:
            session_id: Session to rewind.
            n: Number of events to go back.

        Returns:
            The new position after rewinding.
        """
        session = self.get_session(session_id)

        if n < 0:
            raise ReplayError(
                "rewind count must be non-negative",
                session_id=session_id,
            )

        new_pos = max(0, session.position - n)
        session.position = new_pos
        return new_pos

    def get_state(self, session_id: str) -> dict[str, Any]:
        """Get the current state of a replay session.

        Returns:
            Dictionary with position, current_event, total_events,
            is_complete, remaining, and mode.
        """
        session = self.get_session(session_id)
        return {
            "session_id": session.id,
            "position": session.position,
            "current_event": session.current_event,
            "total_events": len(session.events),
            "is_complete": session.is_complete,
            "remaining": session.remaining,
            "mode": session.mode.value,
        }

    def delete_session(self, session_id: str) -> None:
        """Remove a session from the engine."""
        if session_id not in self._sessions:
            raise ReplayError(
                f"Session '{session_id}' not found",
                session_id=session_id,
            )
        del self._sessions[session_id]

    def _emit_completion(self, session: ReplaySession) -> None:
        self._events.append(
            ReplayCompleted(
                session_id=session.id,
                total_events=len(session.events),
                final_position=session.position,
            )
        )

    @property
    def session_count(self) -> int:
        return len(self._sessions)

    @property
    def events(self) -> list[ReplayCompleted]:
        return list(self._events)
