"""Quantum job management use cases — orchestrate quantum computation lifecycle."""
from __future__ import annotations

import json
from typing import Any

import structlog

from src.application.dto import QuantumJobDTO
from src.application.events import get_event_bus
from src.domain.entities.quantum_job import JobStatus, QuantumAlgorithm, QuantumJob
from src.domain.exceptions import EntityNotFoundException, BusinessRuleViolation
from src.quantum.runtime.executor import QuantumExecutor

logger = structlog.get_logger(__name__)


class SubmitQuantumJobUseCase:
    """Submit a new quantum circuit for execution."""

    def __init__(self, repo: Any, executor: QuantumExecutor | None = None) -> None:
        self._repo = repo
        self._bus = get_event_bus()
        self._executor = executor or QuantumExecutor()

    async def execute(
        self,
        user_id: str,
        algorithm: str,
        num_qubits: int = 2,
        shots: int = 1024,
        backend: str = "aer_simulator",
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        job = QuantumJob.submit(
            user_id=user_id,
            algorithm=algorithm,
            num_qubits=num_qubits,
            shots=shots,
            backend=backend,
            parameters=parameters,
        )

        await self._bus.publish_all(job.collect_events())

        job.start()
        try:
            result = await self._executor.run_circuit(
                num_qubits=num_qubits,
                circuit_type=algorithm,
                shots=shots,
                parameters=parameters or {},
            )
            if result.get("status") == "completed":
                job.complete(
                    result=result.get("result", {}),
                    execution_time_ms=result.get("execution_time_ms", 0.0),
                )
            else:
                job.fail(result.get("error", "Unknown error"))
        except Exception as e:
            job.fail(str(e))

        await self._bus.publish_all(job.collect_events())

        logger.info(
            "quantum_job_processed",
            job_id=job.id,
            algorithm=algorithm,
            status=job.status.value,
        )

        return {
            "job_id": job.id,
            "status": job.status.value,
            "algorithm": job.algorithm.value,
            "num_qubits": job.num_qubits,
            "shots": job.shots,
            "backend": job.backend,
            "result": job.result,
            "error_message": job.error_message,
            "execution_time_ms": job.execution_time_ms,
        }


class RunVQEUseCase:
    """Execute a Variational Quantum Eigensolver computation."""

    async def execute(
        self,
        user_id: str,
        hamiltonian: list[list[float]],
        num_qubits: int,
        ansatz: str = "ry",
        optimizer: str = "cobyla",
        max_iterations: int = 100,
        shots: int = 1024,
    ) -> dict[str, Any]:
        from src.quantum.algorithms.vqe import VQESolver
        solver = VQESolver()
        result = await solver.solve(
            hamiltonian=hamiltonian,
            num_qubits=num_qubits,
            ansatz=ansatz,
            optimizer=optimizer,
            max_iterations=max_iterations,
            shots=shots,
        )
        logger.info("vqe_completed", user_id=user_id, num_qubits=num_qubits)
        return result


class RunQAOAUseCase:
    """Execute a Quantum Approximate Optimization Algorithm computation."""

    async def execute(
        self,
        user_id: str,
        cost_matrix: list[list[float]],
        num_layers: int = 2,
        optimizer: str = "cobyla",
        shots: int = 1024,
    ) -> dict[str, Any]:
        from src.quantum.algorithms.qaoa import QAOASolver
        solver = QAOASolver()
        result = await solver.solve(
            cost_matrix=cost_matrix,
            num_layers=num_layers,
            optimizer=optimizer,
            shots=shots,
        )
        logger.info("qaoa_completed", user_id=user_id, layers=num_layers)
        return result


class RunQMLUseCase:
    """Execute a Quantum Machine Learning classification task."""

    async def execute(
        self,
        user_id: str,
        training_data: list[list[float]],
        training_labels: list[int],
        test_data: list[list[float]] | None = None,
        feature_map: str = "zz",
        ansatz: str = "real_amplitudes",
        epochs: int = 50,
    ) -> dict[str, Any]:
        from src.quantum.algorithms.qml import QMLClassifier
        classifier = QMLClassifier()
        result = await classifier.classify(
            training_data=training_data,
            training_labels=training_labels,
            test_data=test_data or [],
            feature_map=feature_map,
            ansatz=ansatz,
            epochs=epochs,
        )
        logger.info("qml_completed", user_id=user_id, epochs=epochs)
        return result


class ListQuantumBackendsUseCase:
    """List available quantum computing backends."""

    async def execute(self) -> list[dict[str, Any]]:
        executor = QuantumExecutor()
        return executor.list_backends()


__all__ = [
    "SubmitQuantumJobUseCase",
    "RunVQEUseCase",
    "RunQAOAUseCase",
    "RunQMLUseCase",
    "ListQuantumBackendsUseCase",
]
