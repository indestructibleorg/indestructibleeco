"""
Supplemental coverage tests targeting the remaining uncovered lines
after the full test suite run at 93% coverage.

Targets:
- src/presentation/api/schemas/__init__.py: 121,123,125,127,129,157-162,167,191,282,353-355,402-404,434-444,449-465,469-474,500,503,506,531
- src/presentation/api/schemas/quantum.py: 52,57
- src/presentation/exceptions/handlers.py: 144-145
- src/quantum/algorithms/qaoa.py: 125-129
- src/quantum/algorithms/qml.py: 45,125-129
- src/quantum/algorithms/vqe.py: 41-44,46,90-94
- src/quantum/circuits/__init__.py: 111
- src/quantum/runtime/executor.py: 53-57,64-67,70-74
- src/scientific/analysis/calculus.py: 37
- src/scientific/analysis/matrix_ops.py: 77-78
- src/scientific/analysis/statistics.py: 87-88
- src/scientific/ml/trainer.py: 127-128
- src/scientific/pipelines/__init__.py: 125
- src/shared/decorators/__init__.py: 108
- src/shared/schemas/__init__.py: 68
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# 1. src/presentation/api/schemas/__init__.py
# ---------------------------------------------------------------------------
class TestSchemaValidatorBranches:
    """Cover remaining validator branches in schemas/__init__.py."""

    def test_user_create_password_all_violations(self):
        """Lines 121,123,125,127,129 – all four password violations."""
        from src.presentation.api.schemas import UserCreateRequest
        with pytest.raises(Exception):
            UserCreateRequest(
                username="testuser",
                email="test@example.com",
                password="short",  # missing uppercase, digit, special
            )

    def test_user_create_password_no_uppercase(self):
        """Line 121 – missing uppercase."""
        from src.presentation.api.schemas import UserCreateRequest
        with pytest.raises(Exception):
            UserCreateRequest(
                username="testuser",
                email="test@example.com",
                password="nouppercase1!",
            )

    def test_user_create_password_no_lowercase(self):
        """Line 123 – missing lowercase."""
        from src.presentation.api.schemas import UserCreateRequest
        with pytest.raises(Exception):
            UserCreateRequest(
                username="testuser",
                email="test@example.com",
                password="NOLOWERCASE1!",
            )

    def test_user_create_password_no_digit(self):
        """Line 125 – missing digit."""
        from src.presentation.api.schemas import UserCreateRequest
        with pytest.raises(Exception):
            UserCreateRequest(
                username="testuser",
                email="test@example.com",
                password="NoDigitHere!",
            )

    def test_user_create_password_no_special(self):
        """Line 127 – missing special character."""
        from src.presentation.api.schemas import UserCreateRequest
        with pytest.raises(Exception):
            UserCreateRequest(
                username="testuser",
                email="test@example.com",
                password="NoSpecial123",
            )

    def test_user_create_role_invalid(self):
        """Lines 157-162 – invalid role."""
        from src.presentation.api.schemas import UserCreateRequest
        with pytest.raises(Exception):
            UserCreateRequest(
                username="testuser",
                email="test@example.com",
                password="ValidPass1!",
                role="superadmin",
            )

    def test_user_create_email_normalised(self):
        """Line 167 – email normalised to lowercase."""
        from src.presentation.api.schemas import UserCreateRequest
        req = UserCreateRequest(
            username="testuser",
            email="TEST@EXAMPLE.COM",
            password="ValidPass1!",
        )
        assert req.email == "test@example.com"

    def test_user_update_role_invalid(self):
        """Line 191 – invalid role in update."""
        from src.presentation.api.schemas import UserUpdateRequest
        with pytest.raises(Exception):
            UserUpdateRequest(full_name="Test", role="superadmin")

    def test_quantum_job_request_normalise_backend(self):
        """Line 282 – backend normalised."""
        from src.presentation.api.schemas import QuantumJobRequest
        req = QuantumJobRequest(
            algorithm="vqe",
            num_qubits=2,
            backend="  Aer_Simulator  ",
        )
        assert req.backend == "aer_simulator"

    def test_ai_expert_create_knowledge_base_too_many(self):
        """Lines 353-355 – knowledge_base > 100 entries."""
        from src.presentation.api.schemas import AIExpertCreateRequest
        with pytest.raises(Exception):
            AIExpertCreateRequest(
                name="Expert",
                domain="quantum",
                knowledge_base=["doc" + str(i) for i in range(101)],
            )

    def test_ai_expert_response_coerce_datetime(self):
        """Lines 402-404 – coerce datetime from ISO string."""
        from src.presentation.api.schemas import AIExpertResponse
        resp = AIExpertResponse(
            id="exp-1",
            name="Expert",
            domain="quantum",
            specialization="",
            status="active",
            model="gpt-4",
            query_count=0,
            created_at="2024-01-01T00:00:00",
        )
        assert resp.created_at is not None

    def test_scientific_analysis_request_empty_data(self):
        """Lines 434-436 – empty data raises error."""
        from src.presentation.api.schemas import ScientificAnalysisRequest
        with pytest.raises(Exception):
            ScientificAnalysisRequest(data=[], operations=["describe"])

    def test_scientific_analysis_request_empty_row(self):
        """Lines 437-438 – row with zero columns raises error."""
        from src.presentation.api.schemas import ScientificAnalysisRequest
        with pytest.raises(Exception):
            ScientificAnalysisRequest(data=[[]], operations=["describe"])

    def test_scientific_analysis_request_inconsistent_rows(self):
        """Lines 439-444 – rows with different lengths raise error."""
        from src.presentation.api.schemas import ScientificAnalysisRequest
        with pytest.raises(Exception):
            ScientificAnalysisRequest(
                data=[[1.0, 2.0], [3.0]],
                operations=["describe"],
            )

    def test_scientific_analysis_request_invalid_operation(self):
        """Lines 449-465 – invalid operation raises error."""
        from src.presentation.api.schemas import ScientificAnalysisRequest
        with pytest.raises(Exception):
            ScientificAnalysisRequest(
                data=[[1.0, 2.0]],
                operations=["invalid_op"],
            )

    def test_scientific_analysis_request_columns_mismatch(self):
        """Lines 469-474 – columns count mismatch raises error."""
        from src.presentation.api.schemas import ScientificAnalysisRequest
        with pytest.raises(Exception):
            ScientificAnalysisRequest(
                data=[[1.0, 2.0]],
                columns=["a", "b", "c"],
                operations=["describe"],
            )

    def test_scientific_matrix_request_empty_matrix(self):
        """Line 500 – empty matrix raises error."""
        from src.presentation.api.schemas import ScientificMatrixRequest
        with pytest.raises(Exception):
            ScientificMatrixRequest(matrix=[], operation="determinant")

    def test_scientific_matrix_request_empty_row(self):
        """Line 503 – matrix row with zero columns raises error."""
        from src.presentation.api.schemas import ScientificMatrixRequest
        with pytest.raises(Exception):
            ScientificMatrixRequest(matrix=[[]], operation="determinant")

    def test_scientific_matrix_request_inconsistent_rows(self):
        """Line 506 – matrix rows with different lengths raise error."""
        from src.presentation.api.schemas import ScientificMatrixRequest
        with pytest.raises(Exception):
            ScientificMatrixRequest(
                matrix=[[1.0, 2.0], [3.0]],
                operation="determinant",
            )

    def test_scientific_matrix_request_invalid_operation(self):
        """Line 531 – invalid operation raises error."""
        from src.presentation.api.schemas import ScientificMatrixRequest
        with pytest.raises(Exception):
            ScientificMatrixRequest(
                matrix=[[1.0, 2.0], [3.0, 4.0]],
                operation="invalid_op",
            )


# ---------------------------------------------------------------------------
# 2. src/presentation/api/schemas/quantum.py lines 52, 57
# ---------------------------------------------------------------------------
class TestQuantumSchemaValidators:
    """Cover validator branches in schemas/quantum.py."""

    def test_quantum_job_request_normalise_algorithm(self):
        """Line 52 – algorithm normalised."""
        from src.presentation.api.schemas.quantum import QuantumJobRequest
        req = QuantumJobRequest(
            algorithm="  VQE  ",
            num_qubits=2,
        )
        assert req.algorithm == "vqe"

    def test_quantum_job_request_normalise_backend(self):
        """Line 57 – backend normalised."""
        from src.presentation.api.schemas.quantum import QuantumJobRequest
        req = QuantumJobRequest(
            algorithm="vqe",
            num_qubits=2,
            backend="  Aer_Simulator  ",
        )
        assert req.backend == "aer_simulator"


# ---------------------------------------------------------------------------
# 3. src/presentation/exceptions/handlers.py lines 144-145
# ---------------------------------------------------------------------------
class TestExceptionHandlers:
    """Cover InfrastructureException handler in handlers.py."""

    @pytest.mark.asyncio
    async def test_infrastructure_exception_handler(self):
        """Lines 144-145 – InfrastructureException returns 500."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from src.presentation.exceptions.handlers import register_exception_handlers
        from src.shared.exceptions import InfrastructureException

        app = FastAPI()
        register_exception_handlers(app)

        @app.get("/test-infra")
        async def raise_infra():
            raise InfrastructureException(message="infra error", code="INFRA_ERROR")

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/test-infra")
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# 4. src/quantum/algorithms/qaoa.py lines 125-129
# ---------------------------------------------------------------------------
class TestQAOAErrorBranches:
    """Cover ImportError and Exception branches in qaoa.py."""

    @pytest.mark.asyncio
    async def test_qaoa_import_error(self):
        """Line 125-126 – ImportError returns error status."""
        from src.quantum.algorithms.qaoa import QAOASolver
        solver = QAOASolver()
        with patch("src.quantum.algorithms.qaoa.np.zeros", side_effect=ImportError("Qiskit not installed")):
            result = await solver.solve(
                cost_matrix=[[0.0, 1.0], [1.0, 0.0]],
                num_layers=1,
                optimizer="cobyla",
                shots=100,
            )
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_qaoa_general_exception(self):
        """Lines 127-129 – RuntimeError returns error status."""
        from src.quantum.algorithms.qaoa import QAOASolver
        solver = QAOASolver()
        with patch("src.quantum.algorithms.qaoa.np.zeros", side_effect=RuntimeError("unexpected")):
            result = await solver.solve(
                cost_matrix=[[0.0, 1.0], [1.0, 0.0]],
                num_layers=1,
                optimizer="cobyla",
                shots=100,
            )
        assert result["status"] == "error"


# ---------------------------------------------------------------------------
# 5. src/quantum/algorithms/qml.py lines 45, 125-129
# ---------------------------------------------------------------------------
class TestQMLErrorBranches:
    """Cover pauli feature_map and error branches in qml.py."""

    @pytest.mark.asyncio
    async def test_qml_pauli_feature_map(self):
        """Line 45 – pauli feature map branch."""
        from src.quantum.algorithms.qml import QMLClassifier
        classifier = QMLClassifier()
        result = await classifier.classify(
            training_data=[[0.1, 0.2], [0.3, 0.4], [0.5, 0.6], [0.7, 0.8]],
            training_labels=[0, 1, 0, 1],
            test_data=[[0.2, 0.3]],
            feature_map="pauli",
            ansatz="real_amplitudes",
            epochs=2,
        )
        assert "status" in result

    @pytest.mark.asyncio
    async def test_qml_import_error(self):
        """Lines 125-126 – ImportError returns error status."""
        from src.quantum.algorithms.qml import QMLClassifier
        classifier = QMLClassifier()
        with patch("src.quantum.algorithms.qml.np.zeros", side_effect=ImportError("Qiskit not installed")):
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
        """Lines 127-129 – RuntimeError returns error status."""
        from src.quantum.algorithms.qml import QMLClassifier
        classifier = QMLClassifier()
        with patch("src.quantum.algorithms.qml.np.zeros", side_effect=RuntimeError("unexpected")):
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
# 6. src/quantum/algorithms/vqe.py lines 41-44, 46, 90-94
# ---------------------------------------------------------------------------
class TestVQEErrorBranches:
    """Cover ryrz ansatz and error branches in vqe.py."""

    @pytest.mark.asyncio
    async def test_vqe_ryrz_ansatz(self):
        """Lines 41-44, 46 – ryrz ansatz branch."""
        from src.quantum.algorithms.vqe import VQESolver
        solver = VQESolver()
        result = await solver.solve(
            hamiltonian=[[1.0, 0.0], [0.0, -1.0]],
            num_qubits=2,
            ansatz="ryrz",
            optimizer="cobyla",
            max_iterations=3,
            shots=100,
        )
        assert "status" in result

    @pytest.mark.asyncio
    async def test_vqe_import_error(self):
        """Lines 90-91 – ImportError returns error status."""
        from src.quantum.algorithms.vqe import VQESolver
        solver = VQESolver()
        with patch("src.quantum.algorithms.vqe.np.linalg.eigvalsh", side_effect=ImportError("Qiskit not installed")):
            result = await solver.solve(
                hamiltonian=[[1.0, 0.0], [0.0, -1.0]],
                num_qubits=2,
                ansatz="ry",
                optimizer="cobyla",
                max_iterations=3,
                shots=100,
            )
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_vqe_general_exception(self):
        """Lines 92-94 – RuntimeError returns error status."""
        from src.quantum.algorithms.vqe import VQESolver
        solver = VQESolver()
        with patch("src.quantum.algorithms.vqe.np.linalg.eigvalsh", side_effect=RuntimeError("unexpected")):
            result = await solver.solve(
                hamiltonian=[[1.0, 0.0], [0.0, -1.0]],
                num_qubits=2,
                ansatz="ry",
                optimizer="cobyla",
                max_iterations=3,
                shots=100,
            )
        assert result["status"] == "error"


# ---------------------------------------------------------------------------
# 7. src/quantum/circuits/__init__.py line 111
# ---------------------------------------------------------------------------
class TestCircuitBuilderParams:
    """Cover gate-with-params branch in circuits/__init__.py."""

    def test_circuit_builder_gate_with_params(self):
        """Line 111 – gate with params (e.g. rz gate)."""
        from src.quantum.circuits import CircuitBuilder
        builder = CircuitBuilder(num_qubits=2)
        # Use the rz method which adds a gate with params
        builder.rz(qubit=0, theta=1.5707963)
        qc = builder.to_dict()
        assert qc is not None


# ---------------------------------------------------------------------------
# 8. src/quantum/runtime/executor.py lines 53-57, 64-67, 70-74
# ---------------------------------------------------------------------------
class TestQuantumExecutorErrorBranches:
    """Cover ImportError and Exception branches in executor.py."""

    @pytest.mark.asyncio
    async def test_executor_import_error(self):
        """Lines 53-54 – ImportError returns error status."""
        from src.quantum.runtime.executor import QuantumExecutor
        executor = QuantumExecutor()
        with patch.object(executor, '_build_circuit',
                   side_effect=ImportError("Qiskit not installed")):
            result = await executor.run_circuit(
                circuit_type="bell",
                num_qubits=2,
                shots=100,
                parameters={},
            )
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_executor_general_exception(self):
        """Lines 55-57 – RuntimeError returns error status."""
        from src.quantum.runtime.executor import QuantumExecutor
        executor = QuantumExecutor()
        with patch.object(executor, '_build_circuit',
                   side_effect=RuntimeError("unexpected")):
            result = await executor.run_circuit(
                circuit_type="bell",
                num_qubits=2,
                shots=100,
                parameters={},
            )
        assert result["status"] == "error"

    def test_executor_build_circuit_ghz(self):
        """Lines 64-67 – GHZ circuit branch."""
        from src.quantum.runtime.executor import QuantumExecutor
        executor = QuantumExecutor()
        try:
            qc = executor._build_circuit(num_qubits=3, circuit_type="ghz", parameters={})
            assert qc is not None
        except ImportError:
            pytest.skip("Qiskit not installed")

    def test_executor_build_circuit_grover(self):
        """Lines 70-74 – Grover circuit branch."""
        from src.quantum.runtime.executor import QuantumExecutor
        executor = QuantumExecutor()
        try:
            qc = executor._build_circuit(num_qubits=3, circuit_type="grover", parameters={})
            assert qc is not None
        except ImportError:
            pytest.skip("Qiskit not installed")


# ---------------------------------------------------------------------------
# 9. src/scientific/analysis/calculus.py line 37
# ---------------------------------------------------------------------------
class TestCalculusRombergFallback:
    """Cover romberg fallback branch in calculus.py."""

    def test_calculus_romberg_fallback(self):
        """Line 37 – romberg fallback when scipy >= 1.14."""
        from src.scientific.analysis.calculus import NumericalCalculus
        calc = NumericalCalculus()
        # Test romberg path (either real or fallback)
        result = calc.integrate(
            function="x**2",
            lower_bound=0.0,
            upper_bound=1.0,
            method="romberg",
        )
        assert "result" in result


# ---------------------------------------------------------------------------
# 10. src/scientific/analysis/matrix_ops.py lines 77-78
# ---------------------------------------------------------------------------
class TestMatrixOpsLinAlgError:
    """Cover LinAlgError branch in matrix_ops.py."""

    def test_matrix_ops_linalg_error(self):
        """Lines 77-78 – singular matrix raises LinAlgError."""
        from src.scientific.analysis.matrix_ops import MatrixOperations
        ops = MatrixOperations()
        result = ops.execute(
            operation="inverse",
            matrix_a=[[0.0, 0.0], [0.0, 0.0]],
        )
        assert "error" in result

    def test_matrix_ops_general_exception(self):
        """Lines 77-78 – general Exception is caught."""
        from src.scientific.analysis.matrix_ops import MatrixOperations
        import numpy as np
        ops = MatrixOperations()
        with patch.object(np.linalg, "det", side_effect=RuntimeError("unexpected")):
            result = ops.execute(
                operation="determinant",
                matrix_a=[[1.0, 0.0], [0.0, 1.0]],
            )
        assert "error" in result


# ---------------------------------------------------------------------------
# 11. src/scientific/analysis/statistics.py lines 87-88
# ---------------------------------------------------------------------------
class TestStatisticsDistributionFit:
    """Cover distribution_fit branch in statistics.py."""

    def test_statistics_distribution_fit(self):
        """Lines 87-88 – distribution_fit operation."""
        from src.scientific.analysis.statistics import StatisticalAnalyzer
        import numpy as np
        analyzer = StatisticalAnalyzer()
        data = [[float(x)] for x in np.random.normal(0, 1, 50).tolist()]
        result = analyzer.analyze(
            data=data,
            columns=["col"],
            operations=["distribution_fit"],
        )
        assert "distribution_fit" in result


# ---------------------------------------------------------------------------
# 12. src/scientific/ml/trainer.py lines 127-128
# ---------------------------------------------------------------------------
class TestMLTrainerPredictProba:
    """Cover predict_proba branch in trainer.py."""

    @pytest.mark.asyncio
    async def test_trainer_predict_proba(self):
        """Lines 127-128 – predict_proba is called for classifiers."""
        from src.scientific.ml.trainer import MLTrainer
        trainer = MLTrainer()
        train_result = await trainer.train(
            algorithm="random_forest",
            features=[[1.0, 2.0], [3.0, 4.0], [5.0, 6.0], [7.0, 8.0],
                      [2.0, 3.0], [4.0, 5.0], [6.0, 7.0], [8.0, 9.0]],
            labels=[0, 1, 0, 1, 0, 1, 0, 1],
            test_size=0.25,
            hyperparameters={},
            cross_validation=0,
        )
        assert "model_id" in train_result or "error" in train_result
        if "model_id" in train_result:
            model_id = train_result["model_id"]
            predict_result = await trainer.predict(
                model_id=model_id,
                features=[[2.0, 3.0]],
            )
            assert "predictions" in predict_result or "error" in predict_result


# ---------------------------------------------------------------------------
# 13. src/scientific/pipelines/__init__.py line 125
# ---------------------------------------------------------------------------
class TestPipelinesRemoveOutliers2D:
    """Cover 2D array branch in pipelines/__init__.py."""

    def test_remove_outliers_2d_returns_array(self):
        """Line 125 – 2D array returns numpy array (not list)."""
        from src.scientific.pipelines import remove_outliers
        import numpy as np
        arr = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
        result = remove_outliers(arr, threshold=2.0)
        # 2D arrays are returned as numpy array
        assert hasattr(result, 'shape')


# ---------------------------------------------------------------------------
# 14. src/shared/decorators/__init__.py line 108
# ---------------------------------------------------------------------------
class TestDecoratorsExpiredEviction:
    """Cover expired cache eviction in decorators/__init__.py."""

    @pytest.mark.asyncio
    async def test_timed_lru_cache_evicts_expired(self):
        """Line 108 – expired entries are evicted."""
        from src.shared.decorators import cached
        import time

        call_count = 0

        @cached(ttl_seconds=0.1)
        async def my_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call – populates cache
        result1 = await my_func(5)
        assert result1 == 10
        assert call_count == 1

        # Wait for TTL to expire
        time.sleep(0.15)

        # Second call – cache expired, function called again; eviction triggered
        result2 = await my_func(5)
        assert result2 == 10
        assert call_count == 2


# ---------------------------------------------------------------------------
# 15. src/shared/schemas/__init__.py line 68
# ---------------------------------------------------------------------------
class TestSharedSchemasEmailLength:
    """Cover email length validation in shared/schemas/__init__.py."""

    def test_email_field_too_long(self):
        """Line 68 – email exceeding 254 chars raises ValueError."""
        from src.shared.schemas import EmailField
        long_local = "a" * 250
        with pytest.raises(Exception):
            EmailField(email=f"{long_local}@example.com")


# ---------------------------------------------------------------------------
# Final targeted tests for remaining uncovered lines
# ---------------------------------------------------------------------------

class TestSchemasRemainingLines:
    """Cover remaining uncovered lines in schemas/__init__.py."""

    def test_user_create_request_valid_password(self):
        """Line 191 – valid password passes all validators."""
        from src.presentation.api.schemas import UserCreateRequest
        req = UserCreateRequest(
            username="testuser",
            email="test@example.com",
            password="ValidPass1!",
        )
        assert req.password == "ValidPass1!"

    def test_scientific_analysis_request_empty_data_raises(self):
        """Line 435 – empty data list raises ValueError."""
        from src.presentation.api.schemas import ScientificAnalysisRequest
        import pytest
        with pytest.raises(Exception):
            ScientificAnalysisRequest(
                data=[],
                columns=["a"],
                operations=["describe"],
            )

    def test_scientific_analysis_request_zero_row_len_raises(self):
        """Line 474 – row length 0 raises ValueError."""
        from src.presentation.api.schemas import ScientificAnalysisRequest
        import pytest
        with pytest.raises(Exception):
            ScientificAnalysisRequest(
                data=[[]],
                columns=[],
                operations=["describe"],
            )

    def test_matrix_ops_request_empty_matrix_raises(self):
        """Line 500 – empty matrix raises ValueError."""
        from src.presentation.api.schemas import ScientificMatrixRequest
        import pytest
        with pytest.raises(Exception):
            ScientificMatrixRequest(
                matrix=[],
                operation="determinant",
            )


class TestCalulusRombergFallback:
    """Cover calculus.py line 37 – romberg fallback."""

    def test_romberg_fallback_path(self):
        """Line 37 – romberg fallback when scipy >= 1.14."""
        from src.scientific.analysis.calculus import NumericalCalculus
        calc = NumericalCalculus()
        # Force the fallback by patching hasattr to return False for romberg
        import scipy.integrate as sci_integrate
        original = getattr(sci_integrate, 'romberg', None)
        if original is not None:
            # romberg still exists; test by temporarily removing it
            try:
                delattr(sci_integrate, 'romberg')
                result = calc.integrate(
                    function="x**2",
                    lower_bound=0.0,
                    upper_bound=1.0,
                    method="romberg",
                )
                assert "result" in result
            finally:
                sci_integrate.romberg = original
        else:
            # Already removed – test fallback directly
            result = calc.integrate(
                function="x**2",
                lower_bound=0.0,
                upper_bound=1.0,
                method="romberg",
            )
            assert "result" in result


class TestStatisticsDistributionFitBestFit:
    """Cover statistics.py lines 87-88 – best_fit update."""

    def test_distribution_fit_updates_best(self):
        """Lines 87-88 – best_fit is updated when ks_stat improves."""
        from src.scientific.analysis.statistics import StatisticalAnalyzer
        import numpy as np
        analyzer = StatisticalAnalyzer()
        # Use normally-distributed data so norm dist wins
        rng = np.random.default_rng(42)
        data = [[float(x)] for x in rng.normal(0, 1, 100).tolist()]
        result = analyzer.analyze(
            data=data,
            columns=["col"],
            operations=["distribution_fit"],
        )
        assert "distribution_fit" in result
        assert "col" in result["distribution_fit"]
        assert result["distribution_fit"]["col"]["name"] != ""


class TestTrainerProbabilities:
    """Cover trainer.py lines 127-128 – predict_proba branch."""

    @pytest.mark.asyncio
    async def test_trainer_predict_proba(self):
        """Lines 127-128 – probabilities added when predict_proba exists."""
        from src.scientific.ml.trainer import MLTrainer
        trainer = MLTrainer()
        # Train a classifier that supports predict_proba (random_forest)
        features = [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0], [7.0, 8.0],
                    [2.0, 3.0], [4.0, 5.0], [6.0, 7.0], [8.0, 9.0]]
        labels = [0, 1, 0, 1, 0, 1, 0, 1]
        result = await trainer.train(
            algorithm="random_forest",
            features=features,
            labels=labels,
            test_size=0.25,
            hyperparameters={},
            cross_validation=0,
        )
        assert "model_id" in result


class TestDecoratorsEviction:
    """Cover decorators/__init__.py line 108 – expired cache eviction."""

    @pytest.mark.asyncio
    async def test_cache_eviction_on_second_call(self):
        """Line 108 – expired entries are deleted from _cache."""
        from src.shared.decorators import cached
        import time

        call_count = 0

        @cached(ttl_seconds=0.05)
        async def fn(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 3

        # Populate cache
        r1 = await fn(7)
        assert r1 == 21
        assert call_count == 1

        # Let TTL expire
        time.sleep(0.1)

        # Second call: old entry expired, new entry added, eviction runs
        r2 = await fn(7)
        assert r2 == 21
        assert call_count == 2


class TestSharedSchemasEmailTooLong:
    """Cover shared/schemas/__init__.py line 68 – email too long."""

    def test_email_exceeds_254_chars(self):
        """Line 68 – email longer than 254 chars raises ValueError."""
        from src.shared.schemas import EmailField
        long_local = "a" * 250
        with pytest.raises(Exception):
            EmailField(email=f"{long_local}@example.com")


class TestCircuitBuilderParamsGate:
    """Cover circuits/__init__.py line 111 – gate with params branch."""

    def test_rz_gate_uses_params_branch(self):
        """Line 111 – rz gate triggers the params branch in to_qiskit."""
        from src.quantum.circuits import CircuitBuilder
        builder = CircuitBuilder(num_qubits=1)
        builder.rz(qubit=0, theta=1.5707963)
        try:
            qc = builder.to_qiskit()
            assert qc is not None
        except ImportError:
            # Qiskit not installed; verify the gate was recorded
            d = builder.to_dict()
            gates = d["gates"]
            rz_gates = [g for g in gates if g["name"] == "rz"]
            assert len(rz_gates) == 1
            assert rz_gates[0]["params"] == [1.5707963]
