from __future__ import annotations

"""
test_final_coverage.py
======================

This test suite aims to cover all remaining lines of code to achieve 100% test coverage.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Import all modules to be tested
from src.infrastructure.persistence.database import get_session, Base, engine
from src.infrastructure.persistence.repositories import SQLAlchemyUserRepository, EntityAlreadyExistsError, EntityNotFoundError, OptimisticLockError
from src.presentation.api.dependencies import get_db_session, get_current_user
from src.presentation.api.middleware import RequestLoggingMiddleware, RateLimitMiddleware
from src.presentation.api.schemas import quantum as quantum_schemas
from src.quantum.runtime.executor import QuantumExecutor
from src.quantum.algorithms import qaoa, qml, vqe
from src.quantum.circuits import CircuitBuilder


class TestFinalCoverage:
    """A comprehensive test suite to fill all coverage gaps."""

    def test_database_engine_and_base(self):
        assert engine is not None
        assert Base is not None

    @pytest.mark.asyncio
    async def test_sqlalchemy_user_repository_update_not_found(self):
        """Test that EntityNotFoundError is raised when entity does not exist."""
        mock_session = AsyncMock()
        # execute returns a result with rowcount=0 (no rows updated)
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result
        # exists() check: scalar returns 0 (entity not found)
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0
        mock_session.execute.side_effect = [mock_result, mock_count_result]

        repo = SQLAlchemyUserRepository(session=mock_session)
        mock_entity = MagicMock()
        mock_entity.id = "non_existent_id"
        mock_entity.version = 1
        mock_entity.email = MagicMock()
        mock_entity.email.value = "test@example.com"
        mock_entity.hashed_password = MagicMock()
        mock_entity.hashed_password.value = "hashed"
        mock_entity.role = MagicMock()
        mock_entity.role.value = "viewer"
        mock_entity.status = MagicMock()
        mock_entity.status.value = "active"
        mock_entity.username = "testuser"
        mock_entity.full_name = "Test User"
        mock_entity.permissions = []
        mock_entity.last_login_at = None
        mock_entity.failed_login_attempts = 0
        mock_entity.locked_until = None

        with pytest.raises(EntityNotFoundError):
            await repo.update(mock_entity)

    @pytest.mark.asyncio
    async def test_sqlalchemy_user_repository_update_optimistic_lock(self):
        """Test that OptimisticLockError is raised when version conflicts."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 0
        # exists() check: scalar returns 1 (entity exists but version mismatch)
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1
        mock_session.execute.side_effect = [mock_result, mock_count_result]

        repo = SQLAlchemyUserRepository(session=mock_session)
        mock_entity = MagicMock()
        mock_entity.id = "existing_id"
        mock_entity.version = 2
        mock_entity.email = MagicMock()
        mock_entity.email.value = "test@example.com"
        mock_entity.hashed_password = MagicMock()
        mock_entity.hashed_password.value = "hashed"
        mock_entity.role = MagicMock()
        mock_entity.role.value = "viewer"
        mock_entity.status = MagicMock()
        mock_entity.status.value = "active"
        mock_entity.username = "testuser"
        mock_entity.full_name = "Test User"
        mock_entity.permissions = []
        mock_entity.last_login_at = None
        mock_entity.failed_login_attempts = 0
        mock_entity.locked_until = None

        with pytest.raises(OptimisticLockError):
            await repo.update(mock_entity)

    def test_quantum_job_status_enum(self):
        assert quantum_schemas.QuantumJobStatus.PENDING.value == "PENDING"
        assert quantum_schemas.QuantumJobStatus.RUNNING.value == "RUNNING"
        assert quantum_schemas.QuantumJobStatus.COMPLETED.value == "COMPLETED"
        assert quantum_schemas.QuantumJobStatus.FAILED.value == "FAILED"

    def test_quantum_job_result_schema(self):
        result = quantum_schemas.QuantumJobResult(job_id="123", result={"counts": {"01": 100}})
        assert result.job_id == "123"

    def test_vqe_solver_init(self):
        solver = vqe.VQESolver()
        assert solver is not None

    def test_qaoa_solver_init(self):
        solver = qaoa.QAOASolver()
        assert solver is not None

    def test_qml_classifier_init(self):
        classifier = qml.QMLClassifier()
        assert classifier is not None

    def test_bell_circuit(self):
        circuit = CircuitBuilder.bell_pair().to_qiskit()
        assert circuit.num_qubits == 2

    def test_ghz_circuit(self):
        circuit = CircuitBuilder.ghz_state(3).to_qiskit()
        assert circuit.num_qubits == 3

    def test_qft_circuit(self):
        circuit = CircuitBuilder.qft(3).to_qiskit()
        assert circuit.num_qubits == 3

    def test_circuit_builder_gates(self):
        cb = CircuitBuilder(4)
        cb.h(0).x(1).y(2).z(3).rx(0, 1.0).ry(1, 2.0).rz(2, 3.0)
        cb.cx(0, 1).cz(2, 3).swap(0, 3).barrier().measure_all()
        assert cb.depth > 0
        d = cb.to_dict()
        cb2 = CircuitBuilder.from_dict(d)
        assert cb2.num_qubits == 4

    def test_circuit_builder_invalid_qubit(self):
        cb = CircuitBuilder(2)
        with pytest.raises(ValueError):
            cb.h(5)

    def test_circuit_builder_cx_same_qubit(self):
        cb = CircuitBuilder(2)
        with pytest.raises(ValueError):
            cb.cx(0, 0)
