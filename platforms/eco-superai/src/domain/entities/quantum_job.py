from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from src.domain.entities.base import BaseEntity

class QuantumJobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class QuantumJobType(str, Enum):
    SIMULATION = "simulation"
    HARDWARE = "hardware"

@dataclass
class QuantumJob(BaseEntity):
    name: str = ""
    status: QuantumJobStatus = QuantumJobStatus.PENDING
    job_type: QuantumJobType = QuantumJobType.SIMULATION
