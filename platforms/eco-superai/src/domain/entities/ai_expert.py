from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid

from src.domain.entities.base import BaseEntity

class ExpertStatus(str, Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"

class ExpertDomain(str, Enum):
    QUANTUM = "quantum"
    AI = "ai"
    SECURITY = "security"
    DEVOPS = "devops"

@dataclass
class AIExpert(BaseEntity):
    name: str = ""
    specialty: str = ""
    bio: Optional[str] = None
    status: ExpertStatus = ExpertStatus.AVAILABLE
    domain: ExpertDomain = ExpertDomain.AI
