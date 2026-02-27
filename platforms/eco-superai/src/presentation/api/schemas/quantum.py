from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class QuantumJobStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class QuantumJobRequest(BaseModel):
    """Submit a quantum computing job."""

    algorithm: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Quantum algorithm to execute",
        examples=["vqe", "qaoa", "qml", "grover", "bell"],
    )
    num_qubits: int = Field(
        ...,
        ge=1,
        le=30,
        description="Number of qubits",
    )
    shots: int = Field(
        default=1024,
        ge=1,
        le=100_000,
        description="Number of measurement shots",
    )
    backend: str = Field(
        default="aer_simulator",
        max_length=50,
        description="Quantum backend identifier",
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Algorithm-specific parameters",
    )

    @field_validator("algorithm")
    @classmethod
    def normalise_algorithm(cls, v: str) -> str:
        return v.lower().strip()

    @field_validator("backend")
    @classmethod
    def normalise_backend(cls, v: str) -> str:
        return v.lower().strip()


class QuantumJobResponse(BaseModel):
    """Quantum job execution result."""

    job_id: str
    status: str
    algorithm: str
    result: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: float = Field(
        default=0.0,
        ge=0.0,
        description="Execution wall-clock time in milliseconds",
    )


class QuantumJobResult(BaseModel):
    job_id: str
    result: dict[str, Any]
