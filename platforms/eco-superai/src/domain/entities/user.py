from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid

from src.domain.value_objects.email import Email
from src.domain.entities.base import BaseEntity

@dataclass
class User(BaseEntity):
    username: str = ""
    email: Email = field(default_factory=lambda: Email("default@example.com"))
    is_active: bool = True
