"""QuantumJob aggregate root — tracks quantum circuit execution lifecycle."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import Field, field_validator

from .base import AggregateRoot, DomainEvent


class JobStatus(str, Enum):
    SUBMITTED = "submitted"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class QuantumAlgorithm(str, Enum):
    BELL = "bell"
    GHZ = "ghz"
    QFT = "qft"
    GROVER = "grover"
    VQE = "vqe"
    QAOA = "qaoa"
    QML = "qml"
    CUSTOM = "custom"


# ---------------------------------------------------------------------------
# Domain Events
# ---------------------------------------------------------------------------

class QuantumJobSubmitted(DomainEvent):
    event_type: str = "quantum.job_submitted"
    aggregate_type: str = "QuantumJob"


class QuantumJobStarted(DomainEvent):
    event_type: str = "quantum.job_started"
    aggregate_type: str = "QuantumJob"


class QuantumJobCompleted(DomainEvent):
    event_type: str = "quantum.job_completed"
    aggregate_type: str = "QuantumJob"


class QuantumJobFailed(DomainEvent):
    event_type: str = "quantum.job_failed"
    aggregate_type: str = "QuantumJob"


class QuantumJobCancelled(DomainEvent):
    event_type: str = "quantum.job_cancelled"
    aggregate_type: str = "QuantumJob"


# ---------------------------------------------------------------------------
# Aggregate Root
# ---------------------------------------------------------------------------

class QuantumJob(AggregateRoot):
    """Quantum job aggregate — models the full lifecycle of a quantum computation."""

    user_id: str = Field(..., min_length=1)
    algorithm: QuantumAlgorithm = QuantumAlgorithm.BELL
    backend: str = Field(default="aer_simulator", max_length=50)
    status: JobStatus = JobStatus.SUBMITTED
    num_qubits: int = Field(default=2, ge=1, le=30)
    shots: int = Field(default=1024, ge=1, le=100000)
    parameters: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None
    execution_time_ms: float | None = None
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    completed_at: datetime | None = None

    @field_validator("backend")
    @classmethod
    def validate_backend(cls, v: str) -> str:
        allowed = {
            "aer_simulator", "statevector_simulator",
            "ibm_quantum", "ionq", "rigetti",
        }
        if v not in allowed:
            raise ValueError(f"Unsupported backend: {v}. Allowed: {allowed}")
        return v

    # -- Factory ------------------------------------------------------------

    @classmethod
    def submit(
        cls,
        user_id: str,
        algorithm: str,
        num_qubits: int = 2,
        shots: int = 1024,
        backend: str = "aer_simulator",
        parameters: dict[str, Any] | None = None,
    ) -> QuantumJob:
        job = cls(
            user_id=user_id,
            algorithm=QuantumAlgorithm(algorithm),
            num_qubits=num_qubits,
            shots=shots,
            backend=backend,
            parameters=parameters or {},
        )
        job.raise_event(QuantumJobSubmitted(
            aggregate_id=job.id,
            payload={
                "user_id": user_id,
                "algorithm": algorithm,
                "num_qubits": num_qubits,
                "backend": backend,
            },
        ))
        return job

    # -- State transitions --------------------------------------------------

    def start(self) -> None:
        if self.status != JobStatus.SUBMITTED and self.status != JobStatus.QUEUED:
            raise ValueError(f"Cannot start job in status '{self.status.value}'")
        self.status = JobStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)
        self.increment_version()
        self.raise_event(QuantumJobStarted(
            aggregate_id=self.id,
            payload={"algorithm": self.algorithm.value},
        ))

    def complete(self, result: dict[str, Any], execution_time_ms: float) -> None:
        if self.status != JobStatus.RUNNING:
            raise ValueError(f"Cannot complete job in status '{self.status.value}'")
        self.status = JobStatus.COMPLETED
        self.result = result
        self.execution_time_ms = execution_time_ms
        self.completed_at = datetime.now(timezone.utc)
        self.increment_version()
        self.raise_event(QuantumJobCompleted(
            aggregate_id=self.id,
            payload={
                "algorithm": self.algorithm.value,
                "execution_time_ms": execution_time_ms,
            },
        ))

    def fail(self, error_message: str) -> None:
        if self.status == JobStatus.COMPLETED:
            raise ValueError("Cannot fail an already completed job")
        self.status = JobStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.now(timezone.utc)
        self.increment_version()
        self.raise_event(QuantumJobFailed(
            aggregate_id=self.id,
            payload={"error": error_message},
        ))

    def cancel(self, reason: str = "") -> None:
        terminal = {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}
        if self.status in terminal:
            raise ValueError(f"Cannot cancel job in terminal status '{self.status.value}'")
        self.status = JobStatus.CANCELLED
        self.completed_at = datetime.now(timezone.utc)
        self.increment_version()
        self.raise_event(QuantumJobCancelled(
            aggregate_id=self.id,
            payload={"reason": reason},
        ))

    # -- Queries ------------------------------------------------------------

    @property
    def is_terminal(self) -> bool:
        return self.status in {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}

    @property
    def is_running(self) -> bool:
        return self.status == JobStatus.RUNNING

    @property
    def duration_ms(self) -> float | None:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() * 1000
        return self.execution_time_ms