from sqlalchemy import Column, String, Boolean, DateTime, Integer, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from src.infrastructure.persistence.database import Base
from src.domain.entities.user import UserRole, UserStatus
from src.domain.entities.ai_expert import ExpertStatus, ExpertDomain
from src.domain.entities.quantum_job import QuantumJobStatus, QuantumJobType

class UserModel(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    role = Column(SQLEnum(UserRole), default=UserRole.USER)
    status = Column(SQLEnum(UserStatus), default=UserStatus.ACTIVE)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class AIExpertModel(Base):
    __tablename__ = "ai_experts"
    id = Column(String, primary_key=True)
    name = Column(String)
    specialty = Column(String)
    bio = Column(String, nullable=True)
    status = Column(SQLEnum(ExpertStatus), default=ExpertStatus.AVAILABLE)
    domain = Column(SQLEnum(ExpertDomain), default=ExpertDomain.AI)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class QuantumJobModel(Base):
    __tablename__ = "quantum_jobs"
    id = Column(String, primary_key=True)
    name = Column(String)
    status = Column(SQLEnum(QuantumJobStatus), default=QuantumJobStatus.PENDING)
    job_type = Column(SQLEnum(QuantumJobType), default=QuantumJobType.SIMULATION)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
