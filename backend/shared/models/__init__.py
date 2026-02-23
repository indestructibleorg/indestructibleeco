"""Shared database models for eco-base platform.

UUID Policy: UUID v1 (time-based) for all identifiers.
- Sortable by creation time
- Traceable generation timestamp
- Node-aware for distributed systems

URI/URN Policy:
- URI: eco-base://{domain}/{kind}/{name}
- URN: urn:eco-base:{domain}:{kind}:{name}:{uuid}
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid1


def generate_uri(domain: str, kind: str, name: str) -> str:
    return f"eco-base://{domain}/{kind}/{name}"


def generate_urn(domain: str, kind: str, name: str, uid: UUID) -> str:
    return f"urn:eco-base:{domain}:{kind}:{name}:{uid}"


class UserRole(str, Enum):
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class PlatformStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPLOYING = "deploying"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ServiceHealth(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class User:
    id: UUID = field(default_factory=uuid1)
    email: str = ""
    role: UserRole = UserRole.MEMBER
    uri: str = ""
    urn: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.uri:
            self.uri = generate_uri("iam", "user", self.email or str(self.id))
        if not self.urn:
            self.urn = generate_urn("iam", "user", self.email or str(self.id), self.id)


@dataclass
class Platform:
    id: UUID = field(default_factory=uuid1)
    name: str = ""
    slug: str = ""
    status: PlatformStatus = PlatformStatus.INACTIVE
    uri: str = ""
    urn: str = ""
    config: Dict[str, Any] = field(default_factory=dict)
    capabilities: List[str] = field(default_factory=list)
    k8s_namespace: str = "eco-base"
    deploy_target: str = ""
    owner_id: Optional[UUID] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        if not self.uri:
            self.uri = generate_uri("platform", "module", self.slug or str(self.id))
        if not self.urn:
            self.urn = generate_urn("platform", "module", self.slug or str(self.id), self.id)


@dataclass
class AIJob:
    id: UUID = field(default_factory=uuid1)
    user_id: UUID = field(default_factory=uuid1)
    model_id: str = ""
    prompt: str = ""
    status: JobStatus = JobStatus.PENDING
    uri: str = ""
    urn: str = ""
    result: Optional[str] = None
    error: Optional[str] = None
    progress: float = 0.0
    params: Dict[str, Any] = field(default_factory=dict)
    usage: Dict[str, int] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.uri:
            self.uri = generate_uri("ai", "job", str(self.id))
        if not self.urn:
            self.urn = generate_urn("ai", "job", self.model_id or "unknown", self.id)


@dataclass
class ServiceRegistration:
    id: UUID = field(default_factory=uuid1)
    service_name: str = ""
    endpoint: str = ""
    uri: str = ""
    urn: str = ""
    discovery_protocol: str = "consul"
    health_check_path: str = "/health"
    health: ServiceHealth = ServiceHealth.UNKNOWN
    registry_ttl: int = 30
    metadata: Dict[str, Any] = field(default_factory=dict)
    registered_at: datetime = field(default_factory=datetime.utcnow)
    last_heartbeat: Optional[datetime] = None

    def __post_init__(self):
        if not self.uri:
            self.uri = generate_uri("registry", "service", self.service_name or str(self.id))
        if not self.urn:
            self.urn = generate_urn("registry", "service", self.service_name or str(self.id), self.id)


@dataclass
class GovernanceRecord:
    id: UUID = field(default_factory=uuid1)
    unique_id: str = ""
    uri: str = ""
    urn: str = ""
    target_system: str = ""
    schema_version: str = "v1"
    generated_by: str = "yaml-toolkit-v1"
    owner: str = ""
    compliance_tags: List[str] = field(default_factory=list)
    cross_layer_binding: List[str] = field(default_factory=list)
    coherence_vector: List[float] = field(default_factory=list)
    function_keywords: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        if not self.unique_id:
            self.unique_id = str(self.id)
        if not self.uri:
            self.uri = generate_uri("governance", "record", self.unique_id)
        if not self.urn:
            self.urn = generate_urn("governance", "record", self.target_system or "unknown", self.id)


@dataclass
class QYAMLDocument:
    unique_id: str = field(default_factory=lambda: str(uuid1()))
    uri: str = ""
    urn: str = ""
    target_system: str = ""
    cross_layer_binding: List[str] = field(default_factory=list)
    schema_version: str = "v1"
    generated_by: str = "yaml-toolkit-v1"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    owner: str = "platform-team"
    approval_chain: List[str] = field(default_factory=list)
    compliance_tags: List[str] = field(default_factory=list)
    lifecycle_policy: str = "active"
    service_endpoint: str = ""
    discovery_protocol: str = "consul"
    health_check_path: str = "/health"
    registry_ttl: int = 30
    alignment_model: str = "BAAI/bge-large-en-v1.5"
    coherence_vector: List[float] = field(default_factory=list)
    function_keywords: List[str] = field(default_factory=list)
    contextual_binding: str = ""
    content: str = ""

    def __post_init__(self):
        if not self.uri:
            self.uri = generate_uri("k8s", "manifest", self.unique_id)
        if not self.urn:
            self.urn = generate_urn("k8s", "manifest", self.target_system or "unknown",
                                     UUID(self.unique_id) if len(self.unique_id) == 36 else uuid1())