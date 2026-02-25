"""Quantum circuit builders — abstraction layer for constructing parameterized circuits."""
from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class CircuitBuilder:
    """Fluent API for constructing quantum circuits with backend abstraction."""

    def __init__(self, num_qubits: int) -> None:
        self._num_qubits = num_qubits
        self._gates: list[dict[str, Any]] = []
        self._measurements: bool = False

    @property
    def num_qubits(self) -> int:
        return self._num_qubits

    @property
    def depth(self) -> int:
        return len(self._gates)

    def h(self, qubit: int) -> CircuitBuilder:
        """Add Hadamard gate."""
        self._validate_qubit(qubit)
        self._gates.append({"name": "h", "qubits": [qubit], "params": []})
        return self

    def x(self, qubit: int) -> CircuitBuilder:
        """Add Pauli-X (NOT) gate."""
        self._validate_qubit(qubit)
        self._gates.append({"name": "x", "qubits": [qubit], "params": []})
        return self

    def y(self, qubit: int) -> CircuitBuilder:
        """Add Pauli-Y gate."""
        self._validate_qubit(qubit)
        self._gates.append({"name": "y", "qubits": [qubit], "params": []})
        return self

    def z(self, qubit: int) -> CircuitBuilder:
        """Add Pauli-Z gate."""
        self._validate_qubit(qubit)
        self._gates.append({"name": "z", "qubits": [qubit], "params": []})
        return self

    def rx(self, qubit: int, theta: float) -> CircuitBuilder:
        """Add rotation around X-axis."""
        self._validate_qubit(qubit)
        self._gates.append({"name": "rx", "qubits": [qubit], "params": [theta]})
        return self

    def ry(self, qubit: int, theta: float) -> CircuitBuilder:
        """Add rotation around Y-axis."""
        self._validate_qubit(qubit)
        self._gates.append({"name": "ry", "qubits": [qubit], "params": [theta]})
        return self

    def rz(self, qubit: int, theta: float) -> CircuitBuilder:
        """Add rotation around Z-axis."""
        self._validate_qubit(qubit)
        self._gates.append({"name": "rz", "qubits": [qubit], "params": [theta]})
        return self

    def cx(self, control: int, target: int) -> CircuitBuilder:
        """Add CNOT (controlled-X) gate."""
        self._validate_qubit(control)
        self._validate_qubit(target)
        if control == target:
            raise ValueError("Control and target qubits must differ")
        self._gates.append({"name": "cx", "qubits": [control, target], "params": []})
        return self

    def cz(self, control: int, target: int) -> CircuitBuilder:
        """Add controlled-Z gate."""
        self._validate_qubit(control)
        self._validate_qubit(target)
        self._gates.append({"name": "cz", "qubits": [control, target], "params": []})
        return self

    def swap(self, qubit1: int, qubit2: int) -> CircuitBuilder:
        """Add SWAP gate."""
        self._validate_qubit(qubit1)
        self._validate_qubit(qubit2)
        self._gates.append({"name": "swap", "qubits": [qubit1, qubit2], "params": []})
        return self

    def barrier(self) -> CircuitBuilder:
        """Add barrier (visual separator, no physical effect)."""
        self._gates.append({"name": "barrier", "qubits": list(range(self._num_qubits)), "params": []})
        return self

    def measure_all(self) -> CircuitBuilder:
        """Add measurement on all qubits."""
        self._measurements = True
        return self

    def to_qiskit(self) -> Any:
        """Convert to Qiskit QuantumCircuit."""
        from qiskit import QuantumCircuit
        qc = QuantumCircuit(self._num_qubits)
        for gate in self._gates:
            name = gate["name"]
            qubits = gate["qubits"]
            params = gate["params"]
            if name == "barrier":
                qc.barrier()
            elif params:
                getattr(qc, name)(*params, *qubits)
            else:
                getattr(qc, name)(*qubits)
        if self._measurements:
            qc.measure_all()
        return qc

    def to_dict(self) -> dict[str, Any]:
        """Serialize circuit to dictionary."""
        return {
            "num_qubits": self._num_qubits,
            "gates": self._gates,
            "depth": self.depth,
            "measurements": self._measurements,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CircuitBuilder:
        """Deserialize circuit from dictionary."""
        builder = cls(num_qubits=data["num_qubits"])
        builder._gates = data.get("gates", [])
        builder._measurements = data.get("measurements", False)
        return builder

    def _validate_qubit(self, qubit: int) -> None:
        if qubit < 0 or qubit >= self._num_qubits:
            raise ValueError(f"Qubit {qubit} out of range [0, {self._num_qubits - 1}]")

    # --- Preset Circuits ---

    @classmethod
    def bell_pair(cls) -> CircuitBuilder:
        """Create a Bell state circuit."""
        return cls(2).h(0).cx(0, 1).measure_all()

    @classmethod
    def ghz_state(cls, n: int) -> CircuitBuilder:
        """Create a GHZ state circuit."""
        builder = cls(n).h(0)
        for i in range(n - 1):
            builder.cx(i, i + 1)
        return builder.measure_all()

    @classmethod
    def qft(cls, n: int) -> CircuitBuilder:
        """Create a Quantum Fourier Transform circuit."""
        import math
        builder = cls(n)
        for i in range(n):
            builder.h(i)
            for j in range(i + 1, n):
                angle = math.pi / (2 ** (j - i))
                builder._gates.append({"name": "cp", "qubits": [j, i], "params": [angle]})
        for i in range(n // 2):
            builder.swap(i, n - i - 1)
        return builder.measure_all()


__all__ = ["CircuitBuilder"]