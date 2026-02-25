"""SQLAlchemy ORM models -- infrastructure persistence layer.

Maps domain aggregate roots to relational tables using modern SQLAlchemy 2.0
``mapped_column`` style.  Every model carries a ``version`` integer used for
optimistic-concurrency control in the repository layer.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.persistence.database import Base


# ---------------------------------------------------------------------------
# UserModel
# ---------------------------------------------------------------------------

class UserModel(Base):
    """``users`` table -- maps to the domain ``User`` aggregate."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True,
    )
    email: Mapped[str] = mapped_column(
        String(254), unique=True, nullable=False, index=True,
    )
    hashed_password: Mapped[str] = mapped_column(String(128), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    role: Mapped[str] = mapped_column(
        String(30), nullable=False, default="viewer", index=True,
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending_verification", index=True,
    )
    permissions: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    failed_login_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # --- relationships -------------------------------------------------------
    quantum_jobs: Mapped[list["QuantumJobModel"]] = relationship(
        "QuantumJobModel", back_populates="user", lazy="selectin",
    )

    __table_args__ = (
        Index("ix_users_email_status", "email", "status"),
        Index("ix_users_role_status", "role", "status"),
    )

    def __repr__(self) -> str:
        return f"<UserModel id={self.id} username={self.username} role={self.role}>"


# ---------------------------------------------------------------------------
# QuantumJobModel
# ---------------------------------------------------------------------------

class QuantumJobModel(Base):
    """``quantum_jobs`` table -- maps to the domain ``QuantumJob`` aggregate."""

    __tablename__ = "quantum_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    algorithm: Mapped[str] = mapped_column(String(50), nullable=False)
    backend: Mapped[str] = mapped_column(String(50), nullable=False, default="aer_simulator")
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="submitted", index=True,
    )
    num_qubits: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    shots: Mapped[int] = mapped_column(Integer, nullable=False, default=1024)
    parameters: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # --- relationships -------------------------------------------------------
    user: Mapped["UserModel"] = relationship(
        "UserModel", back_populates="quantum_jobs", lazy="selectin",
    )

    __table_args__ = (
        Index("ix_quantum_jobs_user_status", "user_id", "status"),
        Index("ix_quantum_jobs_submitted_at", "submitted_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<QuantumJobModel id={self.id} algorithm={self.algorithm} "
            f"status={self.status}>"
        )


# ---------------------------------------------------------------------------
# AIExpertModel
# ---------------------------------------------------------------------------

class AIExpertModel(Base):
    """``ai_experts`` table -- maps to the domain ``AIExpert`` aggregate."""

    __tablename__ = "ai_experts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    domain: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    specialization: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="active", index=True,
    )
    model: Mapped[str] = mapped_column(
        String(100), nullable=False, default="gpt-4-turbo-preview",
    )
    temperature: Mapped[float] = mapped_column(Float, nullable=False, default=0.7)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    knowledge_base_ids: Mapped[list | None] = mapped_column(
        JSON, nullable=True, default=list,
    )
    owner_id: Mapped[str] = mapped_column(String(36), nullable=False, default="", index=True)
    query_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_queried_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata", JSON, nullable=True, default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        Index("ix_ai_experts_domain_status", "domain", "status"),
        Index("ix_ai_experts_owner", "owner_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<AIExpertModel id={self.id} name={self.name} domain={self.domain} "
            f"status={self.status}>"
        )


__all__ = [
    "UserModel",
    "QuantumJobModel",
    "AIExpertModel",
]
