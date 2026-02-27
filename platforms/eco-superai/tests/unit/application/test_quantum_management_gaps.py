"""Targeted tests for remaining uncovered lines in application/use_cases/quantum_management.py.

Covers:
- RunQuantumCircuitUseCase.execute job.fail path (line 60)
- RunVQEUseCase.execute (lines 99-110)
- RunQAOAUseCase.execute (lines 124-133)
- RunQMLUseCase.execute (lines 149-160)
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# RunQuantumCircuitUseCase – job.fail path (line 60)
# ---------------------------------------------------------------------------

class TestSubmitQuantumJobFail:
    """Cover line 60: job.fail when result status is not 'completed'."""

    @pytest.mark.asyncio
    async def test_execute_fails_job_when_result_not_completed(self):
        """Line 60 – job.fail is called when result['status'] != 'completed'."""
        from src.application.use_cases.quantum_management import SubmitQuantumJobUseCase

        mock_executor = AsyncMock()
        mock_executor.run_circuit = AsyncMock(return_value={
            "status": "error",
            "error": "Backend unavailable",
        })

        mock_repo = AsyncMock()
        mock_repo.save = AsyncMock()

        use_case = SubmitQuantumJobUseCase(repo=mock_repo, executor=mock_executor)

        result = await use_case.execute(
            user_id="user-001",
            algorithm="ghz",
            num_qubits=2,
            shots=100,
            backend="aer_simulator",
        )

        # The job should have been failed
        assert result["status"] == "failed"


# ---------------------------------------------------------------------------
# RunVQEUseCase.execute (lines 99-110)
# ---------------------------------------------------------------------------

class TestRunVQEUseCase:
    """Cover lines 99-110: RunVQEUseCase.execute calls VQESolver."""

    @pytest.mark.asyncio
    async def test_execute_calls_vqe_solver(self):
        """Lines 99-110 – VQESolver.solve is called and result is returned."""
        from src.application.use_cases.quantum_management import RunVQEUseCase

        use_case = RunVQEUseCase()

        mock_result = {
            "energy": -1.137,
            "optimal_params": [0.1, 0.2],
            "iterations": 50,
        }

        mock_solver = AsyncMock()
        mock_solver.solve = AsyncMock(return_value=mock_result)

        with patch(
            "src.quantum.algorithms.vqe.VQESolver",
            return_value=mock_solver,
        ):
            result = await use_case.execute(
                user_id="user-001",
                hamiltonian=[[1.0, 0.0], [0.0, -1.0]],
                num_qubits=2,
                ansatz="ry",
                optimizer="cobyla",
                max_iterations=100,
                shots=1024,
            )

        assert result == mock_result


# ---------------------------------------------------------------------------
# RunQAOAUseCase.execute (lines 124-133)
# ---------------------------------------------------------------------------

class TestRunQAOAUseCase:
    """Cover lines 124-133: RunQAOAUseCase.execute calls QAOASolver."""

    @pytest.mark.asyncio
    async def test_execute_calls_qaoa_solver(self):
        """Lines 124-133 – QAOASolver.solve is called and result is returned."""
        from src.application.use_cases.quantum_management import RunQAOAUseCase

        use_case = RunQAOAUseCase()

        mock_result = {
            "optimal_value": 3.5,
            "optimal_assignment": [0, 1, 0, 1],
            "approximation_ratio": 0.87,
        }

        mock_solver = AsyncMock()
        mock_solver.solve = AsyncMock(return_value=mock_result)

        with patch(
            "src.quantum.algorithms.qaoa.QAOASolver",
            return_value=mock_solver,
        ):
            result = await use_case.execute(
                user_id="user-001",
                cost_matrix=[[0, 1], [1, 0]],
                num_layers=2,
                optimizer="cobyla",
                shots=1024,
            )

        assert result == mock_result


# ---------------------------------------------------------------------------
# RunQMLUseCase.execute (lines 149-160)
# ---------------------------------------------------------------------------

class TestRunQMLUseCase:
    """Cover lines 149-160: RunQMLUseCase.execute calls QMLClassifier."""

    @pytest.mark.asyncio
    async def test_execute_calls_qml_classifier(self):
        """Lines 149-160 – QMLClassifier.classify is called and result is returned."""
        from src.application.use_cases.quantum_management import RunQMLUseCase

        use_case = RunQMLUseCase()

        mock_result = {
            "accuracy": 0.92,
            "predictions": [0, 1, 1, 0],
            "training_loss": 0.08,
        }

        mock_classifier = AsyncMock()
        mock_classifier.classify = AsyncMock(return_value=mock_result)

        with patch(
            "src.quantum.algorithms.qml.QMLClassifier",
            return_value=mock_classifier,
        ):
            result = await use_case.execute(
                user_id="user-001",
                training_data=[[0.1, 0.2], [0.3, 0.4]],
                training_labels=[0, 1],
                test_data=[[0.5, 0.6]],
                feature_map="zz",
                ansatz="real_amplitudes",
                epochs=50,
            )

        assert result == mock_result
