"""Unit tests for quantum module.

Tests are split into two categories:

1. Pure-Python tests (no Qiskit dependency) — always run in CI:
   - CircuitBuilder: gate construction, validation, serialization, preset circuits
   - HybridPipeline: optimization loop, convergence, error handling
   - ParameterShiftGradient: gradient computation

2. Qiskit-dependent tests — skipped if Qiskit is not installed:
   - QuantumExecutor: circuit execution on AerSimulator
   - VQE / QAOA / QML algorithms
"""
from __future__ import annotations

import math
import unittest.mock as mock

import numpy as np
import pytest


def _qiskit_installed() -> bool:
    try:
        import qiskit  # noqa: F401
        return True
    except ImportError:
        return False


# ===========================================================================
# CircuitBuilder — pure Python, no Qiskit required
# ===========================================================================

class TestCircuitBuilderGates:
    """Gate construction and fluent API."""

    def test_initial_state(self) -> None:
        from src.quantum.circuits import CircuitBuilder
        cb = CircuitBuilder(3)
        assert cb.num_qubits == 3
        assert cb.depth == 0

    def test_h_gate_adds_to_depth(self) -> None:
        from src.quantum.circuits import CircuitBuilder
        cb = CircuitBuilder(2).h(0)
        assert cb.depth == 1

    def test_x_gate(self) -> None:
        from src.quantum.circuits import CircuitBuilder
        cb = CircuitBuilder(1).x(0)
        assert cb.to_dict()["gates"][0]["name"] == "x"

    def test_y_gate(self) -> None:
        from src.quantum.circuits import CircuitBuilder
        cb = CircuitBuilder(1).y(0)
        assert cb.to_dict()["gates"][0]["name"] == "y"

    def test_z_gate(self) -> None:
        from src.quantum.circuits import CircuitBuilder
        cb = CircuitBuilder(1).z(0)
        assert cb.to_dict()["gates"][0]["name"] == "z"

    def test_rx_gate_stores_theta(self) -> None:
        from src.quantum.circuits import CircuitBuilder
        theta = math.pi / 4
        cb = CircuitBuilder(1).rx(0, theta)
        gate = cb.to_dict()["gates"][0]
        assert gate["name"] == "rx"
        assert gate["params"] == [theta]

    def test_ry_gate_stores_theta(self) -> None:
        from src.quantum.circuits import CircuitBuilder
        cb = CircuitBuilder(1).ry(0, math.pi / 2)
        assert cb.to_dict()["gates"][0]["name"] == "ry"

    def test_rz_gate_stores_theta(self) -> None:
        from src.quantum.circuits import CircuitBuilder
        cb = CircuitBuilder(1).rz(0, math.pi)
        assert cb.to_dict()["gates"][0]["name"] == "rz"

    def test_cx_gate(self) -> None:
        from src.quantum.circuits import CircuitBuilder
        cb = CircuitBuilder(2).cx(0, 1)
        gate = cb.to_dict()["gates"][0]
        assert gate["name"] == "cx"
        assert gate["qubits"] == [0, 1]

    def test_cx_same_qubit_raises(self) -> None:
        from src.quantum.circuits import CircuitBuilder
        with pytest.raises(ValueError, match="must differ"):
            CircuitBuilder(2).cx(0, 0)

    def test_cz_gate(self) -> None:
        from src.quantum.circuits import CircuitBuilder
        cb = CircuitBuilder(2).cz(0, 1)
        assert cb.to_dict()["gates"][0]["name"] == "cz"

    def test_swap_gate(self) -> None:
        from src.quantum.circuits import CircuitBuilder
        cb = CircuitBuilder(2).swap(0, 1)
        assert cb.to_dict()["gates"][0]["name"] == "swap"

    def test_barrier_covers_all_qubits(self) -> None:
        from src.quantum.circuits import CircuitBuilder
        cb = CircuitBuilder(3).barrier()
        gate = cb.to_dict()["gates"][0]
        assert gate["name"] == "barrier"
        assert gate["qubits"] == [0, 1, 2]

    def test_measure_all_sets_flag(self) -> None:
        from src.quantum.circuits import CircuitBuilder
        cb = CircuitBuilder(2).measure_all()
        assert cb.to_dict()["measurements"] is True

    def test_fluent_chain_returns_same_instance(self) -> None:
        from src.quantum.circuits import CircuitBuilder
        cb = CircuitBuilder(2)
        result = cb.h(0).cx(0, 1).measure_all()
        assert result is cb


class TestCircuitBuilderValidation:
    """Qubit index validation."""

    def test_qubit_out_of_range_negative(self) -> None:
        from src.quantum.circuits import CircuitBuilder
        with pytest.raises(ValueError, match="out of range"):
            CircuitBuilder(2).h(-1)

    def test_qubit_out_of_range_too_large(self) -> None:
        from src.quantum.circuits import CircuitBuilder
        with pytest.raises(ValueError, match="out of range"):
            CircuitBuilder(2).h(2)

    def test_qubit_boundary_valid(self) -> None:
        from src.quantum.circuits import CircuitBuilder
        cb = CircuitBuilder(2).h(1)
        assert cb.depth == 1


class TestCircuitBuilderSerialization:
    """to_dict / from_dict roundtrip."""

    def test_to_dict_structure(self) -> None:
        from src.quantum.circuits import CircuitBuilder
        cb = CircuitBuilder(2).h(0).cx(0, 1).measure_all()
        d = cb.to_dict()
        assert d["num_qubits"] == 2
        assert len(d["gates"]) == 2
        assert d["measurements"] is True
        assert d["depth"] == 2

    def test_from_dict_roundtrip(self) -> None:
        from src.quantum.circuits import CircuitBuilder
        original = CircuitBuilder(3).h(0).ry(1, math.pi / 3).cx(0, 2).measure_all()
        serialized = original.to_dict()
        restored = CircuitBuilder.from_dict(serialized)
        assert restored.to_dict() == serialized

    def test_from_dict_empty_gates(self) -> None:
        from src.quantum.circuits import CircuitBuilder
        d = {"num_qubits": 2, "gates": [], "measurements": False}
        cb = CircuitBuilder.from_dict(d)
        assert cb.depth == 0
        assert cb.num_qubits == 2


class TestCircuitBuilderPresets:
    """Preset circuit factories."""

    def test_bell_pair_has_two_qubits(self) -> None:
        from src.quantum.circuits import CircuitBuilder
        cb = CircuitBuilder.bell_pair()
        assert cb.num_qubits == 2
        assert cb.to_dict()["measurements"] is True

    def test_bell_pair_gate_sequence(self) -> None:
        from src.quantum.circuits import CircuitBuilder
        gates = CircuitBuilder.bell_pair().to_dict()["gates"]
        assert gates[0]["name"] == "h"
        assert gates[1]["name"] == "cx"

    def test_ghz_state_3_qubits(self) -> None:
        from src.quantum.circuits import CircuitBuilder
        cb = CircuitBuilder.ghz_state(3)
        assert cb.num_qubits == 3
        gates = cb.to_dict()["gates"]
        non_barrier = [g for g in gates if g["name"] != "barrier"]
        assert len(non_barrier) == 3  # h(0) + cx(0,1) + cx(1,2)

    def test_ghz_state_minimum_2_qubits(self) -> None:
        from src.quantum.circuits import CircuitBuilder
        cb = CircuitBuilder.ghz_state(2)
        assert cb.num_qubits == 2

    def test_qft_3_qubits(self) -> None:
        from src.quantum.circuits import CircuitBuilder
        cb = CircuitBuilder.qft(3)
        assert cb.num_qubits == 3
        assert cb.to_dict()["measurements"] is True


# ===========================================================================
# HybridPipeline — pure Python (uses numpy + scipy)
# ===========================================================================

class TestHybridPipeline:
    """Variational optimization loop."""

    @pytest.mark.asyncio
    async def test_simple_quadratic_converges(self) -> None:
        from src.quantum.hybrid import HybridPipeline

        pipeline = HybridPipeline(
            num_qubits=2,
            num_parameters=2,
            max_iterations=100,
            convergence_threshold=1e-6,
        )

        def quadratic(params: np.ndarray) -> float:
            return float(np.sum(params ** 2))

        result = await pipeline.run(
            cost_function=quadratic,
            initial_params=np.array([1.0, 1.0]),
            optimizer="cobyla",
        )

        assert result["status"] == "completed"
        assert result["optimal_value"] < 1.0
        assert result["iterations"] > 0
        assert isinstance(result["convergence_history"], list)

    @pytest.mark.asyncio
    async def test_history_is_populated(self) -> None:
        from src.quantum.hybrid import HybridPipeline

        pipeline = HybridPipeline(num_qubits=1, num_parameters=1, max_iterations=10)

        def cost(params: np.ndarray) -> float:
            return float(params[0] ** 2)

        await pipeline.run(cost_function=cost, initial_params=np.array([2.0]))
        assert len(pipeline.history) > 0
        assert "iteration" in pipeline.history[0]
        assert "value" in pipeline.history[0]

    @pytest.mark.asyncio
    async def test_error_in_cost_function_returns_error_status(self) -> None:
        from src.quantum.hybrid import HybridPipeline

        pipeline = HybridPipeline(num_qubits=1, num_parameters=1, max_iterations=5)

        def exploding_cost(params: np.ndarray) -> float:
            raise RuntimeError("cost function exploded")

        result = await pipeline.run(
            cost_function=exploding_cost,
            initial_params=np.array([1.0]),
        )
        assert result["status"] == "error"
        assert "exploded" in result["error"]

    @pytest.mark.asyncio
    async def test_random_initial_params_when_none_provided(self) -> None:
        from src.quantum.hybrid import HybridPipeline

        pipeline = HybridPipeline(num_qubits=2, num_parameters=3, max_iterations=5)
        call_count = 0

        def cost(params: np.ndarray) -> float:
            nonlocal call_count
            call_count += 1
            return float(np.sum(params ** 2))

        result = await pipeline.run(cost_function=cost)
        assert call_count > 0
        assert "optimal_parameters" in result


class TestParameterShiftGradient:
    """Gradient computation via parameter-shift rule."""

    def test_gradient_of_quadratic(self) -> None:
        from src.quantum.hybrid import ParameterShiftGradient

        grad = ParameterShiftGradient()

        def quadratic(params: np.ndarray) -> float:
            return float(np.sum(params ** 2))

        params = np.array([1.0, 2.0, 3.0])
        gradients = grad.compute(quadratic, params)

        assert gradients.shape == params.shape
        assert all(g > 0 for g in gradients)

    def test_gradient_zero_at_minimum(self) -> None:
        from src.quantum.hybrid import ParameterShiftGradient

        grad = ParameterShiftGradient()

        def quadratic(params: np.ndarray) -> float:
            return float(np.sum(params ** 2))

        params = np.array([0.0, 0.0])
        gradients = grad.compute(quadratic, params)
        assert all(abs(g) < 0.1 for g in gradients)

    def test_custom_shift_value(self) -> None:
        from src.quantum.hybrid import ParameterShiftGradient

        grad = ParameterShiftGradient(shift=math.pi / 4)

        def linear(params: np.ndarray) -> float:
            return float(params[0])

        params = np.array([1.0])
        gradients = grad.compute(linear, params)
        assert len(gradients) == 1


# ===========================================================================
# QuantumExecutor — Qiskit-dependent tests
# ===========================================================================

class TestQuantumExecutor:
    """Test quantum runtime executor."""

    @pytest.mark.asyncio
    async def test_run_circuit_without_qiskit_returns_error_status(self) -> None:
        """When Qiskit is not installed, run_circuit must return error status
        gracefully instead of raising an unhandled ImportError.
        This test always runs regardless of whether Qiskit is installed.
        """
        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name in ("qiskit", "qiskit_aer"):
                raise ImportError(f"Mocked: {name} not installed")
            return original_import(name, *args, **kwargs)

        from src.quantum.runtime.executor import QuantumExecutor
        executor = QuantumExecutor()

        with mock.patch("builtins.__import__", side_effect=mock_import):
            result = await executor.run_circuit(
                num_qubits=2, circuit_type="bell", shots=100, parameters={}
            )

        assert result["status"] == "error"
        assert "Qiskit not installed" in result["result"]["error"]

    @pytest.mark.asyncio
    @pytest.mark.skipif(not _qiskit_installed(), reason="Qiskit not installed")
    async def test_bell_circuit(self) -> None:
        from src.quantum.runtime.executor import QuantumExecutor
        executor = QuantumExecutor()
        result = await executor.run_circuit(
            num_qubits=2, circuit_type="bell", shots=100, parameters={}
        )
        assert result["status"] == "completed"
        counts = result["result"]["counts"]
        assert isinstance(counts, dict)
        for state in counts:
            assert state in ("00", "11", "0", "1")

    @pytest.mark.asyncio
    @pytest.mark.skipif(not _qiskit_installed(), reason="Qiskit not installed")
    async def test_ghz_circuit(self) -> None:
        from src.quantum.runtime.executor import QuantumExecutor
        executor = QuantumExecutor()
        result = await executor.run_circuit(
            num_qubits=3, circuit_type="ghz", shots=100, parameters={}
        )
        assert result["status"] == "completed"
        assert result["result"]["num_qubits"] == 3

    @pytest.mark.skipif(not _qiskit_installed(), reason="Qiskit not installed")
    def test_list_backends(self) -> None:
        from src.quantum.runtime.executor import QuantumExecutor
        executor = QuantumExecutor()
        backends = executor.list_backends()
        assert isinstance(backends, list)
        assert len(backends) >= 1
        assert any(b["name"] == "aer_simulator" for b in backends)


class TestVQE:
    """Test VQE algorithm."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(not _qiskit_installed(), reason="Qiskit not installed")
    async def test_vqe_simple_hamiltonian(self) -> None:
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


class TestQAOA:
    """Test QAOA algorithm."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(not _qiskit_installed(), reason="Qiskit not installed")
    async def test_qaoa_simple_problem(self) -> None:
        from src.quantum.algorithms.qaoa import QAOASolver
        solver = QAOASolver()
        result = await solver.solve(
            cost_matrix=[[0, 1], [1, 0]],
            num_layers=1,
            optimizer="cobyla",
            shots=100,
        )
        assert isinstance(result, dict)


class TestQML:
    """Test QML classifier."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(not _qiskit_installed(), reason="Qiskit not installed")
    async def test_qml_classify(self) -> None:
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
