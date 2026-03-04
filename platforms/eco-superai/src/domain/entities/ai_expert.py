from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid

from src.domain.entities.base import BaseEntity

@dataclass
class AIExpert(BaseEntity):
    name: str = ""
    specialty: str = ""
    bio: Optional[str] = None
