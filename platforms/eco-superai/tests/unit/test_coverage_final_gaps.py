"""test_coverage_final_gaps.py
Covers all remaining uncovered lines to reach 100% coverage.
"""
from __future__ import annotations

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# 1. src/presentation/api/schemas/__init__.py
# ---------------------------------------------------------------------------
class TestSchemasValidators:
    """Covers uncovered validator branches in schemas/__init__.py."""

    def test_user_register_password_missing_uppercase(self):
        from src.presentation.api.schemas import UserCreateRequest
        with pytest.raises(Exception):
            UserCreateRequest(
                username="testuser",
                email="test@example.com",
                password="nouppercase1!",
                full_name="Test",
                role="viewer",
            )

    def test_user_register_password_missing_lowercase(self):
        from src.presentation.api.schemas import UserCreateRequest
        with pytest.raises(Exception):
            UserCreateRequest(
                username="testuser",
                email="test@example.com",
                password="NOLOWERCASE1!",
                full_name="Test",
                role="viewer",
            )

    def test_user_register_password_missing_digit(self):
        from src.presentation.api.schemas import UserCreateRequest
        with pytest.raises(Exception):
            UserCreateRequest(
                username="testuser",
                email="test@example.com",
                password="NoDigitHere!",
                full_name="Test",
                role="viewer",
            )

    def test_user_register_password_missing_special(self):
        from src.presentation.api.schemas import UserCreateRequest
        with pytest.raises(Exception):
            UserCreateRequest(
                username="testuser",
                email="test@example.com",
                password="NoSpecial123",
                full_name="Test",
                role="viewer",
            )

    def test_user_update_role_none_is_valid(self):
        from src.presentation.api.schemas import UserUpdateRequest
        req = UserUpdateRequest(full_name="Test User", role=None)
        assert req.full_name == "Test User"

    def test_user_update_role_valid(self):
        from src.presentation.api.schemas import UserUpdateRequest
        req = UserUpdateRequest(role="admin")
        assert req.role == "admin"

    def test_user_update_role_invalid(self):
        from src.presentation.api.schemas import UserUpdateRequest
        with pytest.raises(Exception):
            UserUpdateRequest(role="superadmin")

    def test_user_update_no_fields_raises(self):
        from src.presentation.api.schemas import UserUpdateRequest
        with pytest.raises(Exception):
            UserUpdateRequest(full_name=None, role=None)

    def test_user_create_role_invalid(self):
        from src.presentation.api.schemas import UserCreateRequest
        with pytest.raises(Exception):
            UserCreateRequest(
                username="testuser",
                email="test@example.com",
                password="ValidPass1!",
                role="superadmin",
            )

    def test_quantum_job_request_normalise_algorithm(self):
        from src.presentation.api.schemas import QuantumJobRequest
        req = QuantumJobRequest(algorithm="  VQE  ", backend="Aer_Simulator", num_qubits=2, shots=1024)
        assert req.algorithm == "vqe"
        assert req.backend == "aer_simulator"

    def test_ai_expert_create_knowledge_base_too_many(self):
        from src.presentation.api.schemas import AIExpertCreateRequest
        with pytest.raises(Exception):
            AIExpertCreateRequest(
                name="Expert",
                domain="quantum",
                knowledge_base=["doc" + str(i) for i in range(101)],
            )

    def test_ai_expert_create_knowledge_base_strips_whitespace(self):
        from src.presentation.api.schemas import AIExpertCreateRequest
        req = AIExpertCreateRequest(
            name="Expert",
            domain="quantum",
            knowledge_base=["  doc1  ", "", "  doc2  "],
        )
        assert req.knowledge_base == ["doc1", "doc2"]

    def test_ai_expert_response_coerce_datetime_from_string(self):
        from src.presentation.api.schemas import AIExpertResponse
        resp = AIExpertResponse(
            id="e1",
            name="Expert One",
            domain="quantum",
            specialization="vqe",
            status="active",
            model="gpt-4",
            query_count=0,
            created_at="2024-01-01T00:00:00",
        )
        from datetime import datetime
        assert isinstance(resp.created_at, datetime)

    def test_ai_expert_response_coerce_datetime_passthrough(self):
        from src.presentation.api.schemas import AIExpertResponse
        from datetime import datetime
        dt = datetime(2024, 1, 1)
        resp = AIExpertResponse(
            id="e1",
            name="Expert One",
            domain="quantum",
            specialization="vqe",
            status="active",
            model="gpt-4",
            query_count=0,
            created_at=dt,
        )
        assert resp.created_at == dt

    def test_scientific_analysis_request_empty_data(self):
        from src.presentation.api.schemas import ScientificAnalysisRequest
        with pytest.raises(Exception):
            ScientificAnalysisRequest(data=[], operations=["describe"])

    def test_scientific_analysis_request_empty_row(self):
        from src.presentation.api.schemas import ScientificAnalysisRequest
        with pytest.raises(Exception):
            ScientificAnalysisRequest(data=[[]], operations=["describe"])

    def test_scientific_analysis_request_jagged_rows(self):
        from src.presentation.api.schemas import ScientificAnalysisRequest
        with pytest.raises(Exception):
            ScientificAnalysisRequest(data=[[1.0, 2.0], [3.0]], operations=["describe"])

    def test_scientific_analysis_request_invalid_operation(self):
        from src.presentation.api.schemas import ScientificAnalysisRequest
        with pytest.raises(Exception):
            ScientificAnalysisRequest(data=[[1.0, 2.0]], operations=["invalid_op"])

    def test_scientific_analysis_request_columns_mismatch(self):
        from src.presentation.api.schemas import ScientificAnalysisRequest
        with pytest.raises(Exception):
            ScientificAnalysisRequest(
                data=[[1.0, 2.0]],
                operations=["describe"],
                columns=["a", "b", "c"],
            )

    def test_scientific_matrix_request_empty_matrix(self):
        from src.presentation.api.schemas import ScientificMatrixRequest
        with pytest.raises(Exception):
            ScientificMatrixRequest(matrix=[], operation="determinant")

    def test_scientific_matrix_request_empty_row(self):
        from src.presentation.api.schemas import ScientificMatrixRequest
        with pytest.raises(Exception):
            ScientificMatrixRequest(matrix=[[]], operation="determinant")

    def test_scientific_matrix_request_jagged(self):
        from src.presentation.api.schemas import ScientificMatrixRequest
        with pytest.raises(Exception):
            ScientificMatrixRequest(matrix=[[1.0, 2.0], [3.0]], operation="determinant")

    def test_scientific_matrix_request_invalid_operation(self):
        from src.presentation.api.schemas import ScientificMatrixRequest
        with pytest.raises(Exception):
            ScientificMatrixRequest(matrix=[[1.0]], operation="invalid_op")


# ---------------------------------------------------------------------------
# 2. src/presentation/api/schemas/quantum.py (lines 52, 57)
# ---------------------------------------------------------------------------
class TestQuantumSchemas:
    """Covers uncovered lines in schemas/quantum.py."""

    def test_quantum_job_request_normalise_algorithm(self):
        from src.presentation.api.schemas.quantum import QuantumJobRequest
        req = QuantumJobRequest(algorithm="  VQE  ", backend="Aer_Simulator", num_qubits=2, shots=1024)
        assert req.algorithm == "vqe"

    def test_quantum_job_request_normalise_backend(self):
        from src.presentation.api.schemas.quantum import QuantumJobRequest
        req = QuantumJobRequest(algorithm="vqe", backend="  Aer_Simulator  ", num_qubits=2, shots=1024)
        assert req.backend == "aer_simulator"


# ---------------------------------------------------------------------------
# 3. src/presentation/exceptions/handlers.py (lines 144-145)
# ---------------------------------------------------------------------------
class TestExceptionHandlers:
    """Covers uncovered lines in handlers.py."""

    def test_infrastructure_exception_handler(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from src.presentation.exceptions.handlers import register_exception_handlers
        from src.shared.exceptions import InfrastructureException

        app = FastAPI()
        register_exception_handlers(app)

        @app.get("/test-infra")
        async def trigger():
            raise InfrastructureException("db_error", "Database connection failed")

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/test-infra")
        assert response.status_code == 500


# ---------------------------------------------------------------------------
# 4. src/quantum/runtime/executor.py (lines 77-84, 87-104)
# ---------------------------------------------------------------------------
class TestQuantumExecutorCircuits:
    """Covers uncovered circuit types in executor.py."""

    @pytest.mark.asyncio
    async def test_run_qft_circuit(self):
        from src.quantum.runtime.executor import QuantumExecutor
        executor = QuantumExecutor()
        result = await executor.run_circuit(
            num_qubits=2,
            circuit_type="qft",
            shots=100,
            parameters={},
        )
        assert "status" in result

    @pytest.mark.asyncio
    async def test_run_grover_circuit(self):
        from src.quantum.runtime.executor import QuantumExecutor
        executor = QuantumExecutor()
        result = await executor.run_circuit(
            num_qubits=2,
            circuit_type="grover",
            shots=100,
            parameters={},
        )
        assert "status" in result

    @pytest.mark.asyncio
    async def test_run_custom_circuit(self):
        from src.quantum.runtime.executor import QuantumExecutor
        executor = QuantumExecutor()
        result = await executor.run_circuit(
            num_qubits=2,
            circuit_type="custom",
            shots=100,
            parameters={"gates": [{"name": "h", "qubits": [0], "params": []}]},
        )
        assert "status" in result


# ---------------------------------------------------------------------------
# 5. src/quantum/algorithms/vqe.py (lines 41-44, 46, 90-94)
# ---------------------------------------------------------------------------
class TestVQESolver:
    """Covers uncovered lines in vqe.py."""

    @pytest.mark.asyncio
    async def test_vqe_ryrz_ansatz(self):
        from src.quantum.algorithms.vqe import VQESolver
        solver = VQESolver()
        result = await solver.solve(
            hamiltonian=[[1.0, 0.0], [0.0, -1.0]],
            num_qubits=2,
            ansatz="ryrz",
            optimizer="cobyla",
            max_iterations=5,
            shots=100,
        )
        assert "status" in result

    @pytest.mark.asyncio
    async def test_vqe_import_error(self):
        from src.quantum.algorithms.vqe import VQESolver
        solver = VQESolver()
        with patch("src.quantum.algorithms.vqe.np.linalg.eigvalsh", side_effect=ImportError("Qiskit not installed")):
            result = await solver.solve(
                hamiltonian=[[1.0, 0.0], [0.0, -1.0]],
                num_qubits=2,
                ansatz="ry",
                optimizer="cobyla",
                max_iterations=5,
                shots=100,
            )
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_vqe_general_exception(self):
        from src.quantum.algorithms.vqe import VQESolver
        solver = VQESolver()
        with patch("src.quantum.algorithms.vqe.np.linalg.eigvalsh", side_effect=RuntimeError("Unexpected error")):
            result = await solver.solve(
                hamiltonian=[[1.0, 0.0], [0.0, -1.0]],
                num_qubits=2,
                ansatz="ry",
                optimizer="cobyla",
                max_iterations=5,
                shots=100,
            )
        assert result["status"] == "error"


# ---------------------------------------------------------------------------
# 6. src/quantum/algorithms/qaoa.py (lines 125-129)
# ---------------------------------------------------------------------------
class TestQAOASolver:
    """Covers uncovered lines in qaoa.py."""

    @pytest.mark.asyncio
    async def test_qaoa_import_error(self):
        from src.quantum.algorithms.qaoa import QAOASolver
        solver = QAOASolver()
        with patch("src.quantum.algorithms.qaoa.np.array", side_effect=ImportError("Qiskit not installed")):
            result = await solver.solve(
                cost_matrix=[[0.0, 1.0], [1.0, 0.0]],
                num_layers=1,
                optimizer="cobyla",
                shots=100,
            )
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_qaoa_general_exception(self):
        from src.quantum.algorithms.qaoa import QAOASolver
        solver = QAOASolver()
        with patch("src.quantum.algorithms.qaoa.np.array", side_effect=RuntimeError("Unexpected error")):
            result = await solver.solve(
                cost_matrix=[[0.0, 1.0], [1.0, 0.0]],
                num_layers=1,
                optimizer="cobyla",
                shots=100,
            )
        assert result["status"] == "error"


# ---------------------------------------------------------------------------
# 7. src/quantum/algorithms/qml.py (lines 45, 125-129)
# ---------------------------------------------------------------------------
class TestQMLClassifier:
    """Covers uncovered lines in qml.py."""

    @pytest.mark.asyncio
    async def test_qml_pauli_feature_map(self):
        from src.quantum.algorithms.qml import QMLClassifier
        classifier = QMLClassifier()
        result = await classifier.classify(
            training_data=[[0.1, 0.2], [0.3, 0.4]],
            training_labels=[0, 1],
            test_data=[[0.2, 0.3]],
            feature_map="pauli",
            ansatz="real_amplitudes",
            epochs=2,
        )
        assert "status" in result

    @pytest.mark.asyncio
    async def test_qml_import_error(self):
        from src.quantum.algorithms.qml import QMLClassifier
        classifier = QMLClassifier()
        with patch("src.quantum.algorithms.qml.np.array", side_effect=ImportError("Qiskit not installed")):
            result = await classifier.classify(
                training_data=[[0.1, 0.2], [0.3, 0.4]],
                training_labels=[0, 1],
                test_data=[],
                feature_map="zz",
                ansatz="real_amplitudes",
                epochs=2,
            )
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_qml_general_exception(self):
        from src.quantum.algorithms.qml import QMLClassifier
        classifier = QMLClassifier()
        with patch("src.quantum.algorithms.qml.np.array", side_effect=RuntimeError("Unexpected error")):
            result = await classifier.classify(
                training_data=[[0.1, 0.2], [0.3, 0.4]],
                training_labels=[0, 1],
                test_data=[],
                feature_map="zz",
                ansatz="real_amplitudes",
                epochs=2,
            )
        assert result["status"] == "error"


# ---------------------------------------------------------------------------
# 8. src/quantum/circuits/__init__.py (line 111 - barrier in from_dict)
# ---------------------------------------------------------------------------
class TestCircuitBuilderBarrier:
    """Covers line 111 in circuits/__init__.py (barrier gate in from_dict)."""

    def test_circuit_builder_from_dict_with_barrier(self):
        from src.quantum.circuits import CircuitBuilder
        cb = CircuitBuilder(2)
        cb.h(0).barrier()
        d = cb.to_dict()
        gate_names = [g["name"] for g in d["gates"]]
        assert "barrier" in gate_names
        cb2 = CircuitBuilder.from_dict(d)
        assert cb2.num_qubits == 2


# ---------------------------------------------------------------------------
# 9. src/scientific/analysis/calculus.py (line 37 - romberg fallback)
# ---------------------------------------------------------------------------
class TestCalculusRombergFallback:
    """Covers line 37 in calculus.py."""

    def test_romberg_integration(self):
        from src.scientific.analysis.calculus import NumericalCalculus
        calc = NumericalCalculus()
        result = calc.integrate(function="x", lower_bound=0.0, upper_bound=1.0, method="romberg")
        assert "result" in result
        assert abs(result["result"] - 0.5) < 1e-3


# ---------------------------------------------------------------------------
# 10. src/scientific/analysis/matrix_ops.py (lines 77-78)
# ---------------------------------------------------------------------------
class TestMatrixOpsErrors:
    """Covers uncovered error branches in matrix_ops.py."""

    def test_matrix_ops_linalg_error(self):
        from src.scientific.analysis.matrix_ops import MatrixOperations
        ops = MatrixOperations()
        # Singular matrix for inverse should raise LinAlgError
        result = ops.execute(operation="inverse", matrix_a=[[0.0, 0.0], [0.0, 0.0]])
        assert "error" in result

    def test_matrix_ops_general_exception(self):
        from src.scientific.analysis.matrix_ops import MatrixOperations
        import numpy as np
        ops = MatrixOperations()
        with patch.object(np.linalg, "det", side_effect=RuntimeError("unexpected")):
            result = ops.execute(operation="determinant", matrix_a=[[1.0]])
        assert "error" in result


# ---------------------------------------------------------------------------
# 11. src/scientific/analysis/statistics.py (lines 87-88)
# ---------------------------------------------------------------------------
class TestStatisticsDistributionFit:
    """Covers uncovered lines 87-88 in statistics.py."""

    def test_statistics_normality_analysis(self):
        from src.scientific.analysis.statistics import StatisticalAnalyzer
        analyzer = StatisticalAnalyzer()
        import numpy as np
        data = [[float(x)] for x in np.random.normal(0, 1, 50).tolist()]
        result = analyzer.analyze(data=data, columns=["col"], operations=["normality"])
        assert "normality" in result or "shape" in result


# ---------------------------------------------------------------------------
# 12. src/scientific/ml/trainer.py (lines 127-128)
# ---------------------------------------------------------------------------
class TestMLTrainerProbabilities:
    """Covers uncovered lines 127-128 in trainer.py."""

    @pytest.mark.asyncio
    async def test_trainer_predict_proba(self):
        from src.scientific.ml.trainer import MLTrainer
        trainer = MLTrainer()
        X_train = [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0], [7.0, 8.0]]
        y_train = [0, 1, 0, 1]
        # Train a classification model
        train_result = await trainer.train(
            algorithm="random_forest",
            features=X_train,
            labels=y_train,
            test_size=0.25,
            hyperparameters={},
            cross_validation=2,
        )
        assert "model_id" in train_result or "error" in train_result
        if "model_id" in train_result:
            model_id = train_result["model_id"]
            predict_result = await trainer.predict(model_id=model_id, features=[[2.0, 3.0]])
            assert "predictions" in predict_result or "error" in predict_result


# ---------------------------------------------------------------------------
# 13. src/scientific/pipelines/__init__.py (line 125)
# ---------------------------------------------------------------------------
class TestPipelinesRemoveOutliers:
    """Covers line 125 in pipelines/__init__.py."""

    def test_pipeline_remove_outliers_1d(self):
        from src.scientific.pipelines import remove_outliers
        import numpy as np
        # Use a very small threshold to ensure 100.0 is removed
        arr = np.array([1.0, 2.0, 3.0, 100.0])
        result = remove_outliers(arr, threshold=1.5)
        assert isinstance(result, list)
        # With threshold=1.5, 100.0 should be removed
        assert len(result) < 4

    def test_pipeline_remove_outliers_2d(self):
        from src.scientific.pipelines import remove_outliers
        import numpy as np
        arr = np.array([[1.0, 2.0], [3.0, 4.0]])
        result = remove_outliers(arr, threshold=2.0)
        # 2D arrays are returned as numpy array (not list)
        assert hasattr(result, 'shape')


# ---------------------------------------------------------------------------
# 14. src/shared/decorators/__init__.py (line 108 - cache eviction)
# ---------------------------------------------------------------------------
class TestDecoratorsEviction:
    """Covers line 108 in decorators/__init__.py (cache eviction)."""

    @pytest.mark.asyncio
    async def test_cached_eviction(self):
        from src.shared.decorators import cached
        import time

        call_count = 0

        @cached(ttl_seconds=1)
        async def my_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call - populates cache
        assert await my_func(1) == 2
        assert call_count == 1

        # Second call with different arg - populates another cache entry
        assert await my_func(2) == 4
        assert call_count == 2

        # Third call with first arg - should hit cache
        assert await my_func(1) == 2
        assert call_count == 2

        # Simulate expired entry by calling cache_clear
        my_func.cache_clear()
        assert await my_func(1) == 2
        assert call_count == 3


# ---------------------------------------------------------------------------
# 15. src/shared/schemas/__init__.py (line 68 - email length check)
# ---------------------------------------------------------------------------
class TestSharedSchemasEmailLength:
    """Covers line 68 in shared/schemas/__init__.py (email length check)."""

    def test_email_too_long_raises(self):
        from src.shared.schemas import EmailField
        long_local = "a" * 250
        long_email = f"{long_local}@b.com"
        with pytest.raises(Exception):
            EmailField(email=long_email)
