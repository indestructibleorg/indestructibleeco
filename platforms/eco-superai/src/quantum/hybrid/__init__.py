"""Quantum-classical hybrid pipeline — iterative optimization loops."""
from __future__ import annotations

import time
from typing import Any, Callable

import numpy as np
import structlog

logger = structlog.get_logger(__name__)


class HybridPipeline:
    """Classical-quantum hybrid optimization pipeline.

    Implements the variational loop:
    1. Classical optimizer proposes parameters
    2. Quantum circuit evaluates cost function
    3. Classical optimizer updates parameters
    4. Repeat until convergence
    """

    def __init__(
        self,
        num_qubits: int,
        num_parameters: int,
        max_iterations: int = 100,
        convergence_threshold: float = 1e-6,
    ) -> None:
        self._num_qubits = num_qubits
        self._num_parameters = num_parameters
        self._max_iterations = max_iterations
        self._convergence_threshold = convergence_threshold
        self._history: list[dict[str, Any]] = []

    async def run(
        self,
        cost_function: Callable[[np.ndarray], float],
        initial_params: np.ndarray | None = None,
        optimizer: str = "cobyla",
        shots: int = 1024,
    ) -> dict[str, Any]:
        """Execute the hybrid optimization loop."""
        start = time.perf_counter()

        if initial_params is None:
            initial_params = np.random.uniform(-np.pi, np.pi, self._num_parameters)

        self._history = []
        iteration = 0
        current_params = initial_params.copy()
        best_value = float("inf")
        best_params = current_params.copy()

        try:
            from scipy.optimize import minimize as scipy_minimize

            def objective(params: np.ndarray) -> float:
                nonlocal iteration, best_value, best_params
                value = cost_function(params)
                iteration += 1
                self._history.append({
                    "iteration": iteration,
                    "value": float(value),
                    "params": params.tolist(),
                })
                if value < best_value:
                    best_value = value
                    best_params = params.copy()
                return value

            result = scipy_minimize(
                objective,
                current_params,
                method=optimizer.upper() if optimizer != "cobyla" else "COBYLA",
                options={"maxiter": self._max_iterations},
                tol=self._convergence_threshold,
            )

            elapsed = (time.perf_counter() - start) * 1000
            converged = bool(result.success) or (
                len(self._history) >= 2
                and abs(self._history[-1]["value"] - self._history[-2]["value"]) < self._convergence_threshold
            )

            logger.info(
                "hybrid_pipeline_complete",
                iterations=iteration,
                optimal_value=float(best_value),
                converged=converged,
                elapsed_ms=round(elapsed, 2),
            )

            return {
                "status": "completed",
                "optimal_value": float(best_value),
                "optimal_parameters": best_params.tolist(),
                "iterations": iteration,
                "converged": converged,
                "convergence_history": [h["value"] for h in self._history],
                "execution_time_ms": round(elapsed, 2),
                "optimizer": optimizer,
                "num_qubits": self._num_qubits,
            }

        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error("hybrid_pipeline_error", error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "iterations": iteration,
                "best_value": float(best_value) if best_value != float("inf") else None,
                "execution_time_ms": round(elapsed, 2),
            }

    @property
    def history(self) -> list[dict[str, Any]]:
        return self._history


class ParameterShiftGradient:
    """Compute gradients using the parameter-shift rule for quantum circuits."""

    def __init__(self, shift: float = np.pi / 2) -> None:
        self._shift = shift

    def compute(
        self,
        cost_function: Callable[[np.ndarray], float],
        params: np.ndarray,
    ) -> np.ndarray:
        """Compute gradient vector using parameter-shift rule."""
        gradients = np.zeros_like(params)
        for i in range(len(params)):
            shifted_plus = params.copy()
            shifted_plus[i] += self._shift
            shifted_minus = params.copy()
            shifted_minus[i] -= self._shift
            gradients[i] = (cost_function(shifted_plus) - cost_function(shifted_minus)) / (2 * np.sin(self._shift))
        return gradients


__all__ = ["HybridPipeline", "ParameterShiftGradient"]