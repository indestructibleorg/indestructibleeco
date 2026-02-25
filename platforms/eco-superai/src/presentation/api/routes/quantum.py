"""Quantum Computing API routes -- job submission, monitoring, and backend management."""
from __future__ import annotations

import structlog
from typing import Any

from fastapi import APIRouter, Depends, Query, Request, status
from pydantic import BaseModel, Field

from src.application.services import AuditService
from src.application.use_cases.quantum_management import (
    ListQuantumBackendsUseCase,
    RunQAOAUseCase,
    RunQMLUseCase,
    RunVQEUseCase,
    SubmitQuantumJobUseCase,
)
from src.domain.value_objects.role import Permission
from src.presentation.api.dependencies import (
    get_client_ip,
    get_current_user,
    require_permission,
)
from src.presentation.api.schemas import (
    CircuitRequest,
    QAOARequest,
    QMLRequest,
    QuantumResultResponse,
    VQERequest,
)

logger = structlog.get_logger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Additional response schemas specific to routing
# ---------------------------------------------------------------------------


class QuantumJobListResponse(BaseModel):
    """Paginated list of quantum jobs."""
    items: list[QuantumResultResponse]
    total: int
    skip: int
    limit: int


class QuantumBackendResponse(BaseModel):
    """Quantum backend descriptor."""
    name: str
    provider: str
    num_qubits: int = 0
    status: str = "available"
    description: str = ""


class CancelJobResponse(BaseModel):
    """Confirmation of a job cancellation request."""
    job_id: str
    status: str
    message: str


# ---------------------------------------------------------------------------
# Submit job
# ---------------------------------------------------------------------------


@router.post(
    "/jobs",
    response_model=QuantumResultResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a quantum circuit job",
)
async def submit_job(
    body: CircuitRequest,
    request: Request,
    current_user: dict[str, Any] = Depends(require_permission(Permission.QUANTUM_EXECUTE)),
    client_ip: str = Depends(get_client_ip),
) -> dict[str, Any]:
    """Submit a quantum circuit for execution on the configured backend.

    Requires ``quantum:execute`` permission.
    """
    use_case = SubmitQuantumJobUseCase(repo=None)
    result = await use_case.execute(
        user_id=current_user["user_id"],
        algorithm=body.circuit_type,
        num_qubits=body.num_qubits,
        shots=body.shots,
        parameters=body.parameters,
    )
    await AuditService.log(
        action="quantum.job_submitted",
        resource_type="QuantumJob",
        resource_id=result.get("job_id"),
        user_id=current_user["user_id"],
        details={
            "circuit_type": body.circuit_type,
            "num_qubits": body.num_qubits,
            "shots": body.shots,
        },
        ip_address=client_ip,
        user_agent=request.headers.get("User-Agent"),
    )
    return result


# ---------------------------------------------------------------------------
# Get single job
# ---------------------------------------------------------------------------


@router.get(
    "/jobs/{job_id}",
    response_model=QuantumResultResponse,
    summary="Get quantum job status and results",
)
async def get_job(
    job_id: str,
    current_user: dict[str, Any] = Depends(require_permission(Permission.QUANTUM_READ)),
) -> dict[str, Any]:
    """Retrieve the status and results of a previously submitted quantum job.

    Requires ``quantum:read`` permission.
    """
    from src.quantum.runtime.executor import QuantumExecutor
    executor = QuantumExecutor()
    result = await executor.get_job(job_id)
    if result is None:
        from src.domain.exceptions import EntityNotFoundException
        raise EntityNotFoundException("QuantumJob", job_id)
    return result


# ---------------------------------------------------------------------------
# List jobs
# ---------------------------------------------------------------------------


@router.get(
    "/jobs",
    response_model=QuantumJobListResponse,
    summary="List quantum jobs (paginated)",
)
async def list_jobs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Page size"),
    status_filter: str | None = Query(
        None,
        alias="status",
        description="Filter by job status (submitted, running, completed, failed, cancelled)",
    ),
    current_user: dict[str, Any] = Depends(require_permission(Permission.QUANTUM_READ)),
) -> dict[str, Any]:
    """List the authenticated user's quantum jobs with optional status filtering.

    Requires ``quantum:read`` permission.
    """
    from src.quantum.runtime.executor import QuantumExecutor
    executor = QuantumExecutor()
    jobs = await executor.list_jobs(
        user_id=current_user["user_id"],
        skip=skip,
        limit=limit,
        status=status_filter,
    )
    return {
        "items": jobs.get("items", []),
        "total": jobs.get("total", 0),
        "skip": skip,
        "limit": limit,
    }


# ---------------------------------------------------------------------------
# Cancel job
# ---------------------------------------------------------------------------


@router.post(
    "/jobs/{job_id}/cancel",
    response_model=CancelJobResponse,
    summary="Cancel a running quantum job",
)
async def cancel_job(
    job_id: str,
    request: Request,
    current_user: dict[str, Any] = Depends(require_permission(Permission.QUANTUM_EXECUTE)),
    client_ip: str = Depends(get_client_ip),
) -> dict[str, Any]:
    """Request cancellation of a running quantum job.

    Requires ``quantum:execute`` permission.
    """
    from src.quantum.runtime.executor import QuantumExecutor
    executor = QuantumExecutor()
    result = await executor.cancel_job(job_id)
    if result is None:
        from src.domain.exceptions import EntityNotFoundException
        raise EntityNotFoundException("QuantumJob", job_id)

    await AuditService.log(
        action="quantum.job_cancelled",
        resource_type="QuantumJob",
        resource_id=job_id,
        user_id=current_user["user_id"],
        ip_address=client_ip,
        user_agent=request.headers.get("User-Agent"),
    )
    return result


# ---------------------------------------------------------------------------
# List backends
# ---------------------------------------------------------------------------


@router.get(
    "/backends",
    response_model=list[QuantumBackendResponse],
    summary="List available quantum backends",
)
async def list_backends(
    current_user: dict[str, Any] = Depends(require_permission(Permission.QUANTUM_READ)),
) -> list[dict[str, Any]]:
    """Return a list of available quantum computing backends (simulators and
    real hardware).

    Requires ``quantum:read`` permission.
    """
    use_case = ListQuantumBackendsUseCase()
    return await use_case.execute()


# ---------------------------------------------------------------------------
# Algorithm-specific endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/vqe/solve",
    response_model=QuantumResultResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Run a VQE computation",
)
async def solve_vqe(
    body: VQERequest,
    request: Request,
    current_user: dict[str, Any] = Depends(require_permission(Permission.QUANTUM_EXECUTE)),
    client_ip: str = Depends(get_client_ip),
) -> dict[str, Any]:
    """Execute a Variational Quantum Eigensolver (VQE) computation.

    Requires ``quantum:execute`` permission.
    """
    use_case = RunVQEUseCase()
    result = await use_case.execute(
        user_id=current_user["user_id"],
        hamiltonian=body.hamiltonian,
        num_qubits=body.num_qubits,
        ansatz=body.ansatz,
        optimizer=body.optimizer,
        max_iterations=body.max_iterations,
        shots=body.shots,
    )
    await AuditService.log(
        action="quantum.vqe_executed",
        resource_type="QuantumJob",
        resource_id=result.get("job_id"),
        user_id=current_user["user_id"],
        details={"num_qubits": body.num_qubits, "ansatz": body.ansatz, "optimizer": body.optimizer},
        ip_address=client_ip,
        user_agent=request.headers.get("User-Agent"),
    )
    return result


@router.post(
    "/qaoa/optimize",
    response_model=QuantumResultResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Run a QAOA optimization",
)
async def optimize_qaoa(
    body: QAOARequest,
    request: Request,
    current_user: dict[str, Any] = Depends(require_permission(Permission.QUANTUM_EXECUTE)),
    client_ip: str = Depends(get_client_ip),
) -> dict[str, Any]:
    """Execute a Quantum Approximate Optimization Algorithm (QAOA) computation
    for combinatorial optimization.

    Requires ``quantum:execute`` permission.
    """
    use_case = RunQAOAUseCase()
    result = await use_case.execute(
        user_id=current_user["user_id"],
        cost_matrix=body.cost_matrix,
        num_layers=body.num_layers,
        optimizer=body.optimizer,
        shots=body.shots,
    )
    await AuditService.log(
        action="quantum.qaoa_executed",
        resource_type="QuantumJob",
        resource_id=result.get("job_id"),
        user_id=current_user["user_id"],
        details={"num_layers": body.num_layers, "optimizer": body.optimizer},
        ip_address=client_ip,
        user_agent=request.headers.get("User-Agent"),
    )
    return result


@router.post(
    "/qml/classify",
    response_model=QuantumResultResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Run a QML classification task",
)
async def qml_classify(
    body: QMLRequest,
    request: Request,
    current_user: dict[str, Any] = Depends(require_permission(Permission.QUANTUM_EXECUTE)),
    client_ip: str = Depends(get_client_ip),
) -> dict[str, Any]:
    """Train and run a Quantum Machine Learning (QML) classifier.

    Requires ``quantum:execute`` permission.
    """
    use_case = RunQMLUseCase()
    result = await use_case.execute(
        user_id=current_user["user_id"],
        training_data=body.training_data,
        training_labels=body.training_labels,
        test_data=body.test_data,
        feature_map=body.feature_map,
        ansatz=body.ansatz,
        epochs=body.epochs,
    )
    await AuditService.log(
        action="quantum.qml_executed",
        resource_type="QuantumJob",
        resource_id=result.get("job_id"),
        user_id=current_user["user_id"],
        details={"feature_map": body.feature_map, "epochs": body.epochs},
        ip_address=client_ip,
        user_agent=request.headers.get("User-Agent"),
    )
    return result
