"""Quantum Approximate Optimization Algorithm (QAOA) implementation."""
from __future__ import annotations

import time
import uuid
from typing import Any

import numpy as np
import structlog

logger = structlog.get_logger(__name__)


class QAOASolver:
    """QAOA solver for combinatorial optimization problems."""

    async def solve(self, cost_matrix: list[list[float]], num_layers: int, optimizer: str, shots: int) -> dict[str, Any]:
        """Alias for ``optimize`` used by the application use-case layer."""
        return await self.optimize(
            cost_matrix=cost_matrix,
            num_layers=num_layers,
            optimizer=optimizer,
            shots=shots,
        )

    async def optimize(self, cost_matrix: list[list[float]], num_layers: int, optimizer: str, shots: int) -> dict[str, Any]:
        start = time.perf_counter()
        job_id = str(uuid.uuid4())

        try:
            from qiskit import QuantumCircuit, transpile
            from qiskit_aer import AerSimulator
            from scipy.optimize import minimize as scipy_minimize

            C = np.array(cost_matrix)
            n = C.shape[0]
            num_params = 2 * num_layers  # gamma and beta per layer

            def build_qaoa_circuit(params: np.ndarray) -> QuantumCircuit:
                gammas = params[:num_layers]
                betas = params[num_layers:]
                qc = QuantumCircuit(n)
                # Initial superposition
                qc.h(range(n))
                for layer in range(num_layers):
                    # Cost unitary
                    for i in range(n):
                        for j in range(i + 1, n):
                            if C[i][j] != 0:
                                qc.rzz(gammas[layer] * C[i][j], i, j)
                    # Mixer unitary
                    for i in range(n):
                        qc.rx(2 * betas[layer], i)
                return qc

            def cost_function(params: np.ndarray) -> float:
                qc = build_qaoa_circuit(params)
                qc.measure_all()
                simulator = AerSimulator()
                t_qc = transpile(qc, simulator)
                result = simulator.run(t_qc, shots=shots).result()
                counts = result.get_counts()

                total_cost = 0.0
                for bitstring, count in counts.items():
                    bits = [int(b) for b in bitstring[::-1]]
                    cost = 0.0
                    for i in range(n):
                        for j in range(i + 1, n):
                            cost += C[i][j] * bits[i] * bits[j]
                    total_cost += cost * count
                return total_cost / shots

            initial_params = np.random.uniform(0, 2 * np.pi, num_params)
            optimizer_map = {"cobyla": "COBYLA", "spsa": "Nelder-Mead", "adam": "Powell"}
            scipy_method = optimizer_map.get(optimizer, "COBYLA")

            result = scipy_minimize(cost_function, initial_params, method=scipy_method, options={"maxiter": 200})

            # Get final distribution
            final_qc = build_qaoa_circuit(result.x)
            final_qc.measure_all()
            simulator = AerSimulator()
            t_qc = transpile(final_qc, simulator)
            final_result = simulator.run(t_qc, shots=shots).result()
            final_counts = final_result.get_counts()

            # Find best solution
            best_bitstring = max(final_counts, key=final_counts.get)  # type: ignore
            best_bits = [int(b) for b in best_bitstring[::-1]]
            best_cost = sum(C[i][j] * best_bits[i] * best_bits[j] for i in range(n) for j in range(i + 1, n))

            # Brute force for comparison (small problems only)
            brute_force_best = None
            if n <= 15:
                bf_min = float("inf")
                bf_bits = []
                for state in range(2**n):
                    bits = [(state >> i) & 1 for i in range(n)]
                    cost = sum(C[i][j] * bits[i] * bits[j] for i in range(n) for j in range(i + 1, n))
                    if cost < bf_min:
                        bf_min = cost
                        bf_bits = bits
                brute_force_best = {"cost": bf_min, "solution": bf_bits}

            elapsed = (time.perf_counter() - start) * 1000
            logger.info("qaoa_completed", job_id=job_id, best_cost=best_cost, layers=num_layers)

            return {
                "job_id": job_id,
                "status": "completed",
                "result": {
                    "best_solution": best_bits,
                    "best_cost": float(best_cost),
                    "optimal_params": {"gammas": result.x[:num_layers].tolist(), "betas": result.x[num_layers:].tolist()},
                    "distribution": dict(sorted(final_counts.items(), key=lambda x: x[1], reverse=True)[:20]),
                    "num_iterations": int(result.nfev),
                    "converged": result.success,
                    "brute_force_optimal": brute_force_best,
                    "approximation_ratio": round(best_cost / brute_force_best["cost"], 4) if brute_force_best and brute_force_best["cost"] != 0 else None,
                },
                "metadata": {"num_qubits": n, "num_layers": num_layers, "optimizer": optimizer, "shots": shots},
                "execution_time_ms": round(elapsed, 2),
            }
        except ImportError:
            return {"job_id": job_id, "status": "error", "result": {"error": "Qiskit not installed"}, "metadata": {}, "execution_time_ms": 0}
        except Exception as e:
            logger.error("qaoa_error", error=str(e))
            return {"job_id": job_id, "status": "error", "result": {"error": str(e)}, "metadata": {}, "execution_time_ms": 0}