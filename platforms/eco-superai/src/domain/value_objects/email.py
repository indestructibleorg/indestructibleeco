import re
from dataclasses import dataclass
from src.domain.entities.base import ValueObject

@dataclass(frozen=True)
class Email(ValueObject):
    address: str

    def __post_init__(self):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", self.address):
            raise ValueError(f"Invalid email address: {self.address}")

    def __str__(self):
        return self.address
