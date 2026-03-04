from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid

from src.domain.value_objects.email import Email
from src.domain.entities.base import BaseEntity

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    EXPERT = "expert"

class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"

@dataclass
class User(BaseEntity):
    username: str = ""
    email: Email = field(default_factory=lambda: Email("default@example.com"))
    is_active: bool = True
    role: UserRole = UserRole.USER
    status: UserStatus = UserStatus.ACTIVE
