"""Quantum Circuit Executor - Qiskit Runtime integration."""
from __future__ import annotations

import time
import uuid
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class QuantumExecutor:
    """Execute quantum circuits on local simulator or IBM Quantum backends."""

    def __init__(self) -> None:
        from src.infrastructure.config import get_settings
        self._settings = get_settings().quantum

    async def run_circuit(self, num_qubits: int, circuit_type: str, shots: int, parameters: dict[str, Any]) -> dict[str, Any]:
        start = time.perf_counter()
        job_id = str(uuid.uuid4())

        try:
            from qiskit import QuantumCircuit
            from qiskit_aer import AerSimulator

            qc = self._build_circuit(num_qubits, circuit_type, parameters)
            qc.measure_all()

            simulator = AerSimulator()
            from qiskit import transpile
            transpiled = transpile(qc, simulator, optimization_level=self._settings.optimization_level)
            result = simulator.run(transpiled, shots=shots).result()
            counts = result.get_counts()

            elapsed = (time.perf_counter() - start) * 1000
            logger.info("quantum_circuit_executed", job_id=job_id, circuit_type=circuit_type, qubits=num_qubits, shots=shots, elapsed_ms=elapsed)

            return {
                "job_id": job_id,
                "status": "completed",
                "result": {
                    "counts": counts,
                    "num_qubits": num_qubits,
                    "depth": transpiled.depth(),
                    "gate_count": transpiled.size(),
                    "shots": shots,
                },
                "metadata": {"circuit_type": circuit_type, "backend": "aer_simulator", "optimization_level": self._settings.optimization_level},
                "execution_time_ms": round(elapsed, 2),
            }
        except ImportError:
            return {"job_id": job_id, "status": "error", "result": {"error": "Qiskit not installed. Install with: pip install qiskit qiskit-aer"}, "metadata": {}, "execution_time_ms": 0}
        except Exception as e:
            logger.error("quantum_circuit_error", error=str(e))
            return {"job_id": job_id, "status": "error", "result": {"error": str(e)}, "metadata": {}, "execution_time_ms": 0}

    def _build_circuit(self, num_qubits: int, circuit_type: str, parameters: dict[str, Any]) -> Any:
        from qiskit import QuantumCircuit
        import math

        if circuit_type == "bell":
            qc = QuantumCircuit(2)
            qc.h(0)
            qc.cx(0, 1)
            return qc

        elif circuit_type == "ghz":
            qc = QuantumCircuit(num_qubits)
            qc.h(0)
            for i in range(num_qubits - 1):
                qc.cx(i, i + 1)
            return qc

        elif circuit_type == "qft":
            qc = QuantumCircuit(num_qubits)
            for i in range(num_qubits):
                qc.h(i)
                for j in range(i + 1, num_qubits):
                    qc.cp(math.pi / (2 ** (j - i)), j, i)
            for i in range(num_qubits // 2):
                qc.swap(i, num_qubits - i - 1)
            return qc

        elif circuit_type == "grover":
            n = num_qubits
            qc = QuantumCircuit(n)
            qc.h(range(n))
            # Oracle: mark state |11...1>
            qc.x(range(n))
            qc.h(n - 1)
            qc.mcx(list(range(n - 1)), n - 1)
            qc.h(n - 1)
            qc.x(range(n))
            # Diffusion
            qc.h(range(n))
            qc.x(range(n))
            qc.h(n - 1)
            qc.mcx(list(range(n - 1)), n - 1)
            qc.h(n - 1)
            qc.x(range(n))
            qc.h(range(n))
            return qc

        else:  # custom
            qc = QuantumCircuit(num_qubits)
            gates = parameters.get("gates", [])
            for gate in gates:
                gate_name = gate.get("name", "h")
                qubits = gate.get("qubits", [0])
                params = gate.get("params", [])
                getattr(qc, gate_name)(*params, *qubits) if params else getattr(qc, gate_name)(*qubits)
            return qc

    def list_backends(self) -> list[dict[str, Any]]:
        backends = [
            {"name": "aer_simulator", "type": "simulator", "qubits": 30, "status": "available", "local": True},
            {"name": "statevector_simulator", "type": "simulator", "qubits": 30, "status": "available", "local": True},
        ]
        if self._settings.ibm_token:
            backends.append({"name": "ibm_quantum", "type": "hardware", "status": "configured", "local": False})
        return backends