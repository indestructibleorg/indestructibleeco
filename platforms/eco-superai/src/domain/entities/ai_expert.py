"""AIExpert aggregate root — models domain-specific AI expert lifecycle."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import Field, field_validator

from .base import AggregateRoot, DomainEvent


class ExpertStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    TRAINING = "training"
    DEGRADED = "degraded"


class ExpertDomain(str, Enum):
    QUANTUM = "quantum"
    ML = "ml"
    DEVOPS = "devops"
    SECURITY = "security"
    DATA_ENGINEERING = "data_engineering"
    SCIENTIFIC = "scientific"
    GENERAL = "general"


# ---------------------------------------------------------------------------
# Domain Events
# ---------------------------------------------------------------------------

class AIExpertCreated(DomainEvent):
    event_type: str = "ai.expert_created"
    aggregate_type: str = "AIExpert"


class AIExpertQueried(DomainEvent):
    event_type: str = "ai.expert_queried"
    aggregate_type: str = "AIExpert"


class AIExpertDeactivated(DomainEvent):
    event_type: str = "ai.expert_deactivated"
    aggregate_type: str = "AIExpert"


class AIExpertKnowledgeUpdated(DomainEvent):
    event_type: str = "ai.expert_knowledge_updated"
    aggregate_type: str = "AIExpert"


# ---------------------------------------------------------------------------
# Aggregate Root
# ---------------------------------------------------------------------------

class AIExpert(AggregateRoot):
    """AI Expert aggregate — encapsulates a domain-specific AI assistant."""

    name: str = Field(..., min_length=1, max_length=100)
    domain: ExpertDomain = ExpertDomain.GENERAL
    specialization: str = Field(default="", max_length=200)
    status: ExpertStatus = ExpertStatus.ACTIVE
    model: str = Field(default="gpt-4-turbo-preview", max_length=100)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    system_prompt: str = Field(default="", max_length=10000)
    knowledge_base_ids: list[str] = Field(default_factory=list)
    owner_id: str = Field(default="", max_length=36)
    query_count: int = Field(default=0, ge=0)
    total_tokens_used: int = Field(default=0, ge=0)
    last_queried_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        allowed_prefixes = ("gpt-", "claude-", "llama-", "mistral-", "gemini-")
        if not any(v.startswith(p) for p in allowed_prefixes) and v not in ("local", "mock"):
            raise ValueError(
                f"Unsupported model: {v}. Must start with one of {allowed_prefixes} or be 'local'/'mock'"
            )
        return v

    # -- Factory ------------------------------------------------------------

    @classmethod
    def create(
        cls,
        name: str,
        domain: str,
        owner_id: str,
        specialization: str = "",
        model: str = "gpt-4-turbo-preview",
        temperature: float = 0.7,
        system_prompt: str = "",
        knowledge_base_ids: list[str] | None = None,
    ) -> AIExpert:
        expert = cls(
            name=name,
            domain=ExpertDomain(domain),
            owner_id=owner_id,
            specialization=specialization,
            model=model,
            temperature=temperature,
            system_prompt=system_prompt,
            knowledge_base_ids=knowledge_base_ids or [],
        )
        expert.raise_event(AIExpertCreated(
            aggregate_id=expert.id,
            payload={
                "name": name,
                "domain": domain,
                "model": model,
                "owner_id": owner_id,
            },
        ))
        return expert

    # -- Commands -----------------------------------------------------------

    def record_query(self, tokens_used: int = 0) -> None:
        self.query_count += 1
        self.total_tokens_used += tokens_used
        self.last_queried_at = datetime.now(timezone.utc)
        self.increment_version()
        self.raise_event(AIExpertQueried(
            aggregate_id=self.id,
            payload={
                "query_count": self.query_count,
                "tokens_used": tokens_used,
            },
        ))

    def deactivate(self, reason: str = "") -> None:
        if self.status == ExpertStatus.INACTIVE:
            return
        self.status = ExpertStatus.INACTIVE
        self.increment_version()
        self.raise_event(AIExpertDeactivated(
            aggregate_id=self.id,
            payload={"name": self.name, "reason": reason},
        ))

    def activate(self) -> None:
        self.status = ExpertStatus.ACTIVE
        self.increment_version()

    def update_knowledge_base(self, knowledge_base_ids: list[str]) -> None:
        self.knowledge_base_ids = knowledge_base_ids
        self.increment_version()
        self.raise_event(AIExpertKnowledgeUpdated(
            aggregate_id=self.id,
            payload={"knowledge_base_count": len(knowledge_base_ids)},
        ))

    def update_system_prompt(self, prompt: str) -> None:
        if len(prompt) > 10000:
            raise ValueError("System prompt exceeds maximum length of 10000 characters")
        self.system_prompt = prompt
        self.increment_version()

    def update_model_config(self, model: str | None = None, temperature: float | None = None) -> None:
        if model is not None:
            self.model = model
        if temperature is not None:
            if not 0.0 <= temperature <= 2.0:
                raise ValueError("Temperature must be between 0.0 and 2.0")
            self.temperature = temperature
        self.increment_version()

    # -- Queries ------------------------------------------------------------

    @property
    def is_active(self) -> bool:
        return self.status == ExpertStatus.ACTIVE

    @property
    def has_knowledge_base(self) -> bool:
        return len(self.knowledge_base_ids) > 0

    @property
    def effective_system_prompt(self) -> str:
        if self.system_prompt:
            return self.system_prompt
        defaults = {
            ExpertDomain.QUANTUM: (
                "You are a quantum computing expert specializing in Qiskit, VQE, QAOA, "
                "and quantum error correction."
            ),
            ExpertDomain.ML: (
                "You are a machine learning expert with deep knowledge of scikit-learn, "
                "TensorFlow, and PyTorch."
            ),
            ExpertDomain.DEVOPS: (
                "You are a DevOps expert specializing in Kubernetes, ArgoCD, Helm, "
                "CI/CD pipelines, and cloud-native architecture."
            ),
            ExpertDomain.SECURITY: (
                "You are a cybersecurity expert focusing on application security, "
                "OWASP, and zero-trust architecture."
            ),
            ExpertDomain.DATA_ENGINEERING: (
                "You are a data engineering expert specializing in ETL pipelines, "
                "data warehousing, and real-time streaming."
            ),
            ExpertDomain.SCIENTIFIC: (
                "You are a scientific computing expert with expertise in numerical "
                "methods, statistical analysis, and simulation."
            ),
        }
        return defaults.get(self.domain, f"You are an expert in {self.domain.value}.")