"""Lightweight YAML Governance proto stubs.

URI: indestructibleeco://backend/shared/proto/generated/yaml_governance_pb2

Matches the message definitions in backend/shared/proto/yaml_governance.proto.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ValidateRequest:
    content: str = ""
    strict: bool = True


@dataclass
class ValidationError:
    path: str = ""
    message: str = ""
    severity: str = "error"


@dataclass
class ValidateResponse:
    valid: bool = False
    errors: List[ValidationError] = field(default_factory=list)


@dataclass
class StampRequest:
    name: str = ""
    namespace: str = "indestructibleeco"
    kind: str = "Deployment"
    target_system: str = "gke-production"
    owner: str = "platform-team"


@dataclass
class StampResponse:
    unique_id: str = ""
    uri: str = ""
    urn: str = ""
    yaml_content: str = ""
