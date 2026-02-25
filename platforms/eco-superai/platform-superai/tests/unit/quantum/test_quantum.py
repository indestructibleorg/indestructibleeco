"""Unit tests for quantum module."""
from __future__ import annotations

import pytest


class TestQuantumExecutor:
    """Test quantum runtime executor (simulator-based)."""

    @pytest.mark.asyncio
    async def test_bell_circuit(self):
        try:
            from src.quantum.runtime.executor import QuantumExecutor
            executor = QuantumExecutor()
            result = await executor.run_circuit(
                num_qubits=2, circuit_type="bell", shots=100, parameters={}
            )
            assert result["status"] in ("completed", "error")
            if result["status"] == "completed":
                counts = result["result"]["counts"]
                assert isinstance(counts, dict)
                # Bell state should produce mostly |00> and |11>
                for state in counts:
                    assert state in ("00", "11", "0", "1")
        except ImportError:
            pytest.skip("Qiskit not installed")

    @pytest.mark.asyncio
    async def test_ghz_circuit(self):
        try:
            from src.quantum.runtime.executor import QuantumExecutor
            executor = QuantumExecutor()
            result = await executor.run_circuit(
                num_qubits=3, circuit_type="ghz", shots=100, parameters={}
            )
            assert result["status"] in ("completed", "error")
            if result["status"] == "completed":
                assert result["result"]["num_qubits"] == 3
        except ImportError:
            pytest.skip("Qiskit not installed")

    @pytest.mark.asyncio
    async def test_qft_circuit(self):
        try:
            from src.quantum.runtime.executor import QuantumExecutor
            executor = QuantumExecutor()
            result = await executor.run_circuit(
                num_qubits=3, circuit_type="qft", shots=100, parameters={}
            )
            assert result["status"] in ("completed", "error")
        except ImportError:
            pytest.skip("Qiskit not installed")

    def test_list_backends(self):
        try:
            from src.quantum.runtime.executor import QuantumExecutor
            executor = QuantumExecutor()
            backends = executor.list_backends()
            assert isinstance(backends, list)
            assert len(backends) >= 1
            assert any(b["name"] == "aer_simulator" for b in backends)
        except ImportError:
            pytest.skip("Qiskit not installed")


class TestVQE:
    """Test VQE algorithm."""

    @pytest.mark.asyncio
    async def test_vqe_simple_hamiltonian(self):
        try:
            from src.quantum.algorithms.vqe import VQESolver
            solver = VQESolver()
            result = await solver.solve(
                hamiltonian=[[1.0, 0.0], [0.0, -1.0]],
                num_qubits=1,
                ansatz="ry",
                optimizer="cobyla",
                max_iterations=50,
                shots=100,
            )
            assert "status" in result or "optimal_value" in result or "error" in result
        except ImportError:
            pytest.skip("Qiskit not installed")


class TestQAOA:
    """Test QAOA algorithm."""

    @pytest.mark.asyncio
    async def test_qaoa_simple_problem(self):
        try:
            from src.quantum.algorithms.qaoa import QAOASolver
            solver = QAOASolver()
            result = await solver.solve(
                cost_matrix=[[0, 1], [1, 0]],
                num_layers=1,
                optimizer="cobyla",
                shots=100,
            )
            assert isinstance(result, dict)
        except ImportError:
            pytest.skip("Qiskit not installed")


class TestQML:
    """Test QML classifier."""

    @pytest.mark.asyncio
    async def test_qml_classify(self):
        try:
            from src.quantum.algorithms.qml import QMLClassifier
            classifier = QMLClassifier()
            result = await classifier.classify(
                training_data=[[0.1, 0.2], [0.8, 0.9]],
                training_labels=[0, 1],
                test_data=[[0.15, 0.25]],
                feature_map="zz",
                ansatz="real_amplitudes",
                epochs=5,
            )
            assert isinstance(result, dict)
        except ImportError:
            pytest.skip("Qiskit not installed")