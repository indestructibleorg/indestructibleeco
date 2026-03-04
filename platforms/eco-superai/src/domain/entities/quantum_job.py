from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
import uuid

from src.domain.entities.base import BaseEntity

class QuantumAlgorithm(str, Enum):
    GROVER = "grover"
    SHOR = "shor"
    VQE = "vqe"
    QAOA = "qaoa"

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class QuantumJob(BaseEntity):
    user_id: str = ""
    algorithm: QuantumAlgorithm = QuantumAlgorithm.GROVER
    backend: str = ""
    status: JobStatus = JobStatus.PENDING
    num_qubits: int = 1
    shots: int = 1024
    parameters: Dict[str, Any] = field(default_factory=dict)
    result: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None
    submitted_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
