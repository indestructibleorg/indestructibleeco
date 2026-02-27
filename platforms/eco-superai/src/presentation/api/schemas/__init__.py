"""Centralised API request/response schemas — Pydantic v2 models with strict validation.

All schemas use ``model_config = ConfigDict(...)`` and Pydantic v2 ``Field`` /
``field_validator`` / ``model_validator`` where appropriate.
"""
from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


# ============================================================================
# Common / shared
# ============================================================================

class ErrorDetail(BaseModel):
    """Single field-level validation error."""

    model_config = ConfigDict(frozen=True)

    field: str | None = None
    message: str


class ErrorResponse(BaseModel):
    """Standard error envelope returned for all non-2xx responses."""

    model_config = ConfigDict(frozen=True)

    code: str
    message: str
    details: list[ErrorDetail] = Field(default_factory=list)
    request_id: str | None = None
    timestamp: str | None = None


class PaginatedRequest(BaseModel):
    """Pagination query parameters reused across list endpoints."""

    model_config = ConfigDict(frozen=True)

    skip: int = Field(default=0, ge=0, description="Number of items to skip")
    limit: int = Field(default=20, ge=1, le=100, description="Max items per page")
    search: str | None = Field(
        default=None,
        max_length=200,
        description="Optional full-text search term",
    )


class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper."""

    items: list[Any]
    total: int = Field(ge=0)
    skip: int = Field(ge=0)
    limit: int = Field(ge=1)
    has_next: bool = False


# ============================================================================
# User schemas
# ============================================================================

class _ValidRolesMixin:
    """Shared role validation constant."""

    _VALID_ROLES = {"admin", "operator", "scientist", "developer", "viewer"}


class UserCreateRequest(BaseModel):
    """Register a new user account."""

    model_config = ConfigDict(str_strip_whitespace=True)

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Alphanumeric username (hyphens/underscores allowed)",
        examples=["jane_doe"],
    )
    email: EmailStr = Field(
        ...,
        description="Valid email address",
        examples=["jane@example.com"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Must contain uppercase, lowercase, digit, and special char",
    )
    full_name: str = Field(
        default="",
        max_length=200,
        description="Display name",
    )
    role: str = Field(
        default="viewer",
        description="User role",
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        violations: list[str] = []
        if not re.search(r"[A-Z]", v):
            violations.append("at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            violations.append("at least one lowercase letter")
        if not re.search(r"\d", v):
            violations.append("at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>\-_=+\[\]\\/'`~;]", v):
            violations.append("at least one special character")
        if violations:
            raise ValueError(f"Password must contain: {'; '.join(violations)}")
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        allowed = {"admin", "operator", "scientist", "developer", "viewer"}
        if v not in allowed:
            raise ValueError(f"Role must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        return v.lower()


class UserUpdateRequest(BaseModel):
    """Partial update for user profile fields."""

    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: str | None = Field(None, max_length=200)
    role: str | None = Field(None)

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str | None) -> str | None:
        if v is None:
            return v
        allowed = {"admin", "operator", "scientist", "developer", "viewer"}
        if v not in allowed:
            raise ValueError(f"Role must be one of: {', '.join(sorted(allowed))}")
        return v

    @model_validator(mode="after")
    def at_least_one_field(self) -> "UserUpdateRequest":
        if self.full_name is None and self.role is None:
            raise ValueError("At least one field must be provided for update")
        return self


class UserResponse(BaseModel):
    """Public representation of a user."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    email: str
    full_name: str
    role: str
    status: str
    created_at: datetime
    last_login_at: datetime | None = None

    @field_validator("created_at", "last_login_at", mode="before")
    @classmethod
    def coerce_datetime(cls, v: Any) -> Any:
        """Accept ISO-format strings as well as native datetimes."""
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        return v


class UserListResponse(PaginatedResponse):
    """Paginated list of users."""

    items: list[UserResponse]  # type: ignore[assignment]


# ============================================================================
# Authentication / token schemas
# ============================================================================

class TokenRequest(BaseModel):
    """Login credentials for token acquisition."""

    model_config = ConfigDict(str_strip_whitespace=True)

    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)


# Alias for backward compatibility with routes/users.py
LoginRequest = TokenRequest


class TokenResponse(BaseModel):
    """JWT token pair returned on successful authentication."""

    access_token: str
    refresh_token: str
    token_type: str = Field(default="bearer")
    expires_in: int = Field(
        ...,
        gt=0,
        description="Token lifetime in seconds",
    )


class RefreshTokenRequest(BaseModel):
    """Request to exchange a refresh token for a new access token."""

    refresh_token: str = Field(..., min_length=1)


# ============================================================================
# Quantum computing schemas
# ============================================================================

class QuantumJobRequest(BaseModel):
    """Submit a quantum computing job."""

    model_config = ConfigDict(str_strip_whitespace=True)

    algorithm: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Quantum algorithm to execute",
        examples=["vqe", "qaoa", "qml", "grover", "bell"],
    )
    num_qubits: int = Field(
        ...,
        ge=1,
        le=30,
        description="Number of qubits",
    )
    shots: int = Field(
        default=1024,
        ge=1,
        le=100_000,
        description="Number of measurement shots",
    )
    backend: str = Field(
        default="aer_simulator",
        max_length=50,
        description="Quantum backend identifier",
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Algorithm-specific parameters",
    )

    @field_validator("algorithm")
    @classmethod
    def normalise_algorithm(cls, v: str) -> str:
        return v.lower().strip()

    @field_validator("backend")
    @classmethod
    def normalise_backend(cls, v: str) -> str:
        return v.lower().strip()


class QuantumJobResponse(BaseModel):
    """Quantum job execution result."""

    model_config = ConfigDict(from_attributes=True)

    job_id: str
    status: str
    algorithm: str
    result: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: float = Field(
        default=0.0,
        ge=0.0,
        description="Execution wall-clock time in milliseconds",
    )


# ============================================================================
# AI expert schemas
# ============================================================================

class AIExpertCreateRequest(BaseModel):
    """Create a new AI domain expert."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Expert display name",
        examples=["QuantumML Advisor"],
    )
    domain: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Knowledge domain (e.g. quantum, ml, devops, security)",
    )
    specialization: str = Field(
        default="",
        max_length=500,
        description="Narrow area of expertise",
    )
    model: str = Field(
        default="gpt-4-turbo-preview",
        max_length=100,
        description="Underlying LLM model identifier",
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature",
    )
    system_prompt: str = Field(
        default="",
        max_length=10_000,
        description="Custom system prompt for the expert",
    )
    knowledge_base: list[str] = Field(
        default_factory=list,
        description="List of document IDs or URLs for RAG context",
    )

    @field_validator("knowledge_base")
    @classmethod
    def validate_knowledge_base(cls, v: list[str]) -> list[str]:
        if len(v) > 100:
            raise ValueError("Knowledge base cannot contain more than 100 entries")
        return [entry.strip() for entry in v if entry.strip()]


class AIExpertQueryRequest(BaseModel):
    """Query an AI expert."""

    model_config = ConfigDict(str_strip_whitespace=True)

    query: str = Field(
        ...,
        min_length=1,
        max_length=10_000,
        description="Natural-language query",
    )
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context key-value pairs",
    )
    max_tokens: int = Field(
        default=2000,
        ge=1,
        le=32_000,
        description="Maximum tokens in the response",
    )
    include_sources: bool = Field(
        default=False,
        description="Include RAG source references in the response",
    )


class AIExpertResponse(BaseModel):
    """Public representation of an AI expert."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    domain: str
    specialization: str
    status: str
    model: str
    query_count: int = Field(default=0, ge=0)
    created_at: datetime

    @field_validator("created_at", mode="before")
    @classmethod
    def coerce_datetime(cls, v: Any) -> Any:
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        return v


# ============================================================================
# Scientific computing schemas
# ============================================================================

class ScientificAnalysisRequest(BaseModel):
    """Tabular data analysis request (Pandas-style)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    data: list[list[float]] = Field(
        ...,
        min_length=1,
        description="Data matrix — rows are samples, columns are features",
    )
    columns: list[str] = Field(
        default_factory=list,
        description="Optional column names (must match data width if provided)",
    )
    operations: list[str] = Field(
        default_factory=lambda: ["describe"],
        min_length=1,
        description="Statistical operations to perform",
    )

    @field_validator("data")
    @classmethod
    def validate_data_shape(cls, v: list[list[float]]) -> list[list[float]]:
        if not v:
            raise ValueError("Data must contain at least one row")
        row_len = len(v[0])
        if row_len == 0:
            raise ValueError("Data rows must not be empty")
        for idx, row in enumerate(v):
            if len(row) != row_len:
                raise ValueError(
                    f"Row {idx} has {len(row)} columns, expected {row_len}"
                )
        return v

    @field_validator("operations")
    @classmethod
    def validate_operations(cls, v: list[str]) -> list[str]:
        allowed = {
            "describe",
            "correlation",
            "covariance",
            "histogram",
            "outliers",
            "percentiles",
            "normality_test",
            "skewness",
            "kurtosis",
        }
        for op in v:
            if op not in allowed:
                raise ValueError(
                    f"Unknown operation '{op}'. Allowed: {', '.join(sorted(allowed))}"
                )
        return v

    @model_validator(mode="after")
    def check_columns_match_data(self) -> "ScientificAnalysisRequest":
        if self.columns and len(self.columns) != len(self.data[0]):
            raise ValueError(
                f"Number of column names ({len(self.columns)}) must match "
                f"data width ({len(self.data[0])})"
            )
        return self


class ScientificMatrixRequest(BaseModel):
    """Matrix operation request."""

    model_config = ConfigDict(str_strip_whitespace=True)

    matrix: list[list[float]] = Field(
        ...,
        min_length=1,
        description="Input matrix",
    )
    operation: str = Field(
        ...,
        description="Matrix operation to perform",
    )
    params: dict[str, Any] = Field(
        default_factory=dict,
        description="Operation-specific parameters",
    )

    @field_validator("matrix")
    @classmethod
    def validate_matrix_shape(cls, v: list[list[float]]) -> list[list[float]]:
        if not v:
            raise ValueError("Matrix must contain at least one row")
        row_len = len(v[0])
        if row_len == 0:
            raise ValueError("Matrix rows must not be empty")
        for idx, row in enumerate(v):
            if len(row) != row_len:
                raise ValueError(
                    f"Row {idx} has {len(row)} columns, expected {row_len}"
                )
        return v

    @field_validator("operation")
    @classmethod
    def validate_operation(cls, v: str) -> str:
        allowed = {
            "multiply",
            "inverse",
            "eigenvalues",
            "svd",
            "determinant",
            "transpose",
            "norm",
            "solve",
            "rank",
            "trace",
            "cholesky",
            "qr",
            "lu",
        }
        normalised = v.lower().strip()
        if normalised not in allowed:
            raise ValueError(
                f"Unknown operation '{v}'. Allowed: {', '.join(sorted(allowed))}"
            )
        return normalised


# ============================================================================
# Quantum route schemas (extended)
# ============================================================================

class CircuitRequest(BaseModel):
    """Generic quantum circuit execution request."""
    model_config = ConfigDict(str_strip_whitespace=True)
    circuit_type: str = Field(default="bell", max_length=50, description="Circuit type identifier")
    num_qubits: int = Field(..., ge=1, le=30)
    gates: list[dict[str, Any]] = Field(default_factory=list)
    shots: int = Field(default=1024, ge=1, le=100_000)
    backend: str = Field(default="aer_simulator", max_length=50)
    parameters: dict[str, Any] = Field(default_factory=dict)


class VQERequest(BaseModel):
    """Variational Quantum Eigensolver request."""
    model_config = ConfigDict(str_strip_whitespace=True)
    num_qubits: int = Field(..., ge=1, le=30)
    hamiltonian: dict[str, Any] = Field(default_factory=dict)
    ansatz: str = Field(default="ry", max_length=50)
    optimizer: str = Field(default="cobyla", max_length=50)
    max_iterations: int = Field(default=100, ge=1, le=10_000)
    shots: int = Field(default=1024, ge=1, le=100_000)
    backend: str = Field(default="aer_simulator", max_length=50)


class QAOARequest(BaseModel):
    """Quantum Approximate Optimization Algorithm request."""
    model_config = ConfigDict(str_strip_whitespace=True)
    num_qubits: int = Field(..., ge=1, le=30)
    cost_matrix: list[list[float]] = Field(default_factory=list, description="Cost matrix for QAOA")
    num_layers: int = Field(default=1, ge=1, le=20, description="Number of QAOA layers (p)")
    optimizer: str = Field(default="cobyla", max_length=50)
    shots: int = Field(default=1024, ge=1, le=100_000)
    backend: str = Field(default="aer_simulator", max_length=50)


class QMLRequest(BaseModel):
    """Quantum Machine Learning request."""
    model_config = ConfigDict(str_strip_whitespace=True)
    num_qubits: int = Field(..., ge=1, le=30)
    training_data: list[list[float]] = Field(default_factory=list, description="Training data matrix")
    training_labels: list[float] = Field(default_factory=list, description="Training labels")
    test_data: list[list[float]] = Field(default_factory=list, description="Test data matrix")
    feature_map: str = Field(default="ZZFeatureMap", max_length=50, description="Quantum feature map")
    ansatz: str = Field(default="RealAmplitudes", max_length=50, description="Variational ansatz")
    model_type: str = Field(default="variational_classifier", max_length=50)
    epochs: int = Field(default=50, ge=1, le=1000)
    shots: int = Field(default=1024, ge=1, le=100_000)
    backend: str = Field(default="aer_simulator", max_length=50)


class QuantumResultResponse(BaseModel):
    """Quantum computation result."""
    model_config = ConfigDict(from_attributes=True)
    job_id: str
    status: str
    algorithm: str
    result: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: float = Field(default=0.0, ge=0.0)


class QuantumBackendResponse(BaseModel):
    """Quantum backend information."""
    name: str
    status: str
    num_qubits: int
    description: str = ""


class QuantumJobListResponse(PaginatedResponse):
    """Paginated list of quantum jobs."""
    items: list[QuantumResultResponse]  # type: ignore[assignment]


class CancelJobResponse(BaseModel):
    """Quantum job cancellation result."""
    job_id: str
    status: str
    message: str = ""


# ============================================================================
# AI route schemas (extended)
# ============================================================================

class ExpertCreateRequest(BaseModel):
    """Create an AI expert (alias for AIExpertCreateRequest)."""
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str = Field(..., min_length=1, max_length=200)
    domain: str = Field(..., min_length=1, max_length=50)
    specialization: str = Field(default="", max_length=500)
    model: str = Field(default="gpt-4-turbo-preview", max_length=100)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    system_prompt: str = Field(default="", max_length=10_000)
    knowledge_base: list[str] = Field(default_factory=list)


class ExpertQueryRequest(BaseModel):
    """Query an AI expert (alias for AIExpertQueryRequest)."""
    model_config = ConfigDict(str_strip_whitespace=True)
    query: str = Field(..., min_length=1, max_length=10_000)
    context: dict[str, Any] = Field(default_factory=dict)
    max_tokens: int = Field(default=2000, ge=1, le=32_000)
    include_sources: bool = Field(default=False)


class ExpertResponse(BaseModel):
    """AI expert public representation."""
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    domain: str
    specialization: str
    status: str
    model: str
    query_count: int = Field(default=0, ge=0)
    created_at: datetime


class ExpertQueryResponse(BaseModel):
    """AI expert query result."""
    expert_id: str
    response: str
    sources: list[dict[str, Any]] = Field(default_factory=list)
    tokens_used: int = Field(default=0, ge=0)
    latency_ms: float = Field(default=0.0, ge=0.0)


class ExpertListResponse(PaginatedResponse):
    """Paginated list of AI experts."""
    items: list[ExpertResponse]  # type: ignore[assignment]


class EmbeddingRequest(BaseModel):
    """Text embedding generation request."""
    model_config = ConfigDict(str_strip_whitespace=True)
    texts: list[str] = Field(..., min_length=1, max_length=100)
    model: str = Field(default="text-embedding-ada-002", max_length=100)


class EmbeddingResponse(BaseModel):
    """Embedding generation result."""
    embeddings: list[list[float]]
    model: str
    usage: dict[str, int] = Field(default_factory=dict)


class VectorStoreRequest(BaseModel):
    """Store documents in a vector collection."""
    model_config = ConfigDict(str_strip_whitespace=True)
    collection: str = Field(..., min_length=1, max_length=100)
    documents: list[str] = Field(..., min_length=1)
    metadatas: list[dict[str, Any]] = Field(default_factory=list)
    ids: list[str] = Field(default_factory=list)


class VectorUpsertResponse(BaseModel):
    """Vector upsert result."""
    collection: str
    count: int = Field(ge=0)
    status: str = "success"


class VectorSearchRequest(BaseModel):
    """Semantic search in a vector collection."""
    model_config = ConfigDict(str_strip_whitespace=True)
    collection: str = Field(..., min_length=1, max_length=100)
    query: str = Field(..., min_length=1, max_length=10_000)
    top_k: int = Field(default=5, ge=1, le=100)
    threshold: float = Field(default=0.0, ge=0.0, le=1.0)


class VectorSearchResultResponse(BaseModel):
    """Vector search result."""
    results: list[dict[str, Any]]
    query: str
    collection: str
    count: int = Field(ge=0)


class CollectionResponse(BaseModel):
    """Vector collection info."""
    name: str
    count: int = Field(default=0, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentTaskRequest(BaseModel):
    """Agent task execution request."""
    model_config = ConfigDict(str_strip_whitespace=True)
    agent_type: str = Field(..., min_length=1, max_length=50)
    task: str = Field(..., min_length=1, max_length=10_000)
    context: dict[str, Any] = Field(default_factory=dict)
    constraints: dict[str, Any] = Field(default_factory=dict)
    output_format: str = Field(default="text", max_length=50)


class AgentTaskResponse(BaseModel):
    """Agent task execution result."""
    task_id: str
    status: str
    result: dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: float = Field(default=0.0, ge=0.0)


# ============================================================================
# Re-export all schemas for convenient imports
# ============================================================================

__all__ = [
    # Common
    "ErrorDetail",
    "ErrorResponse",
    "PaginatedRequest",
    "PaginatedResponse",
    # Users
    "UserCreateRequest",
    "UserUpdateRequest",
    "UserResponse",
    "UserListResponse",
    # Auth
    "TokenRequest",
    "LoginRequest",
    "TokenResponse",
    "RefreshTokenRequest",
    # Quantum
    "QuantumJobRequest",
    "QuantumJobResponse",
    "CircuitRequest",
    "VQERequest",
    "QAOARequest",
    "QMLRequest",
    "QuantumResultResponse",
    "QuantumBackendResponse",
    "QuantumJobListResponse",
    "CancelJobResponse",
    # AI (original)
    "AIExpertCreateRequest",
    "AIExpertQueryRequest",
    "AIExpertResponse",
    # AI (route aliases)
    "ExpertCreateRequest",
    "ExpertQueryRequest",
    "ExpertResponse",
    "ExpertQueryResponse",
    "ExpertListResponse",
    "EmbeddingRequest",
    "EmbeddingResponse",
    "VectorStoreRequest",
    "VectorUpsertResponse",
    "VectorSearchRequest",
    "VectorSearchResultResponse",
    "CollectionResponse",
    "AgentTaskRequest",
    "AgentTaskResponse",
    # Scientific
    "ScientificAnalysisRequest",
    "ScientificMatrixRequest",
]
