"""Scientific Computing API routes -- statistics, linear algebra, optimization,
interpolation, signal processing, integration, and ML training/prediction."""
from __future__ import annotations

import structlog
from typing import Any

from fastapi import APIRouter, Depends, Query, Request, status
from pydantic import BaseModel, Field

from src.application.services import AuditService
from src.domain.value_objects.role import Permission
from src.presentation.api.dependencies import (
    get_client_ip,
    get_current_user,
    require_permission,
)

logger = structlog.get_logger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class MatrixOperationRequest(BaseModel):
    """Request body for matrix/linear-algebra operations."""
    operation: str = Field(
        ...,
        pattern=r"^(multiply|inverse|eigenvalues|svd|determinant|transpose|norm|solve)$",
        description="Matrix operation to perform",
    )
    matrix_a: list[list[float]] = Field(..., description="Primary matrix")
    matrix_b: list[list[float]] | None = Field(None, description="Secondary matrix (for multiply/solve)")
    vector_b: list[float] | None = Field(None, description="Vector b (for solving Ax=b)")


class StatisticsRequest(BaseModel):
    """Request body for statistical analysis."""
    data: list[list[float]] = Field(..., description="Data matrix (rows=samples, cols=features)")
    columns: list[str] = Field(default_factory=list, description="Column names")
    operations: list[str] = Field(
        default=["describe"],
        description="Operations: describe, correlation, covariance, histogram, outliers",
    )


class OptimizationRequest(BaseModel):
    """Request body for numerical optimization."""
    method: str = Field(default="minimize", pattern=r"^(minimize|curve_fit|root|linprog|milp)$")
    objective: str = Field(..., description="Objective function as string expression")
    bounds: list[list[float]] = Field(default_factory=list)
    constraints: list[dict[str, Any]] = Field(default_factory=list)
    initial_guess: list[float] = Field(default_factory=list)
    parameters: dict[str, Any] = Field(default_factory=dict)


class InterpolationRequest(BaseModel):
    """Request body for data interpolation."""
    x_data: list[float] = Field(..., description="Known x values")
    y_data: list[float] = Field(..., description="Known y values")
    x_new: list[float] = Field(..., description="New x values to interpolate")
    method: str = Field(default="cubic", pattern=r"^(linear|cubic|quadratic|nearest|pchip)$")


class FFTRequest(BaseModel):
    """Request body for FFT / IFFT analysis."""
    signal: list[float] = Field(..., description="Input signal")
    sample_rate: float = Field(default=1.0, gt=0, description="Sampling rate (Hz)")
    inverse: bool = Field(default=False, description="Perform inverse FFT")


class IntegrationRequest(BaseModel):
    """Request body for numerical integration."""
    function: str = Field(..., description="Function expression (variable: x)")
    lower_bound: float
    upper_bound: float
    method: str = Field(default="quad", pattern=r"^(quad|trapezoid|simpson|romberg)$")


class MLTrainRequest(BaseModel):
    """Request body for training a scikit-learn model."""
    algorithm: str = Field(
        ...,
        pattern=r"^(linear_regression|logistic_regression|random_forest|svm|kmeans|pca|gradient_boosting|decision_tree|knn)$",
    )
    features: list[list[float]] = Field(..., description="Feature matrix")
    labels: list[float] | list[int] | None = Field(None, description="Labels (None for unsupervised)")
    test_size: float = Field(default=0.2, ge=0.05, le=0.5)
    hyperparameters: dict[str, Any] = Field(default_factory=dict)
    cross_validation: int = Field(default=0, ge=0, le=20, description="K-fold CV (0=disabled)")


class MLPredictRequest(BaseModel):
    """Request body for model prediction."""
    model_id: str = Field(..., description="Trained model identifier")
    features: list[list[float]] = Field(..., description="Feature matrix for prediction")


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class MatrixResultResponse(BaseModel):
    """Matrix operation result."""
    operation: str
    result: Any
    shape: list[int] = Field(default_factory=list)
    execution_time_ms: float = 0.0


class StatisticsResultResponse(BaseModel):
    """Statistical analysis result."""
    operations: list[str]
    results: dict[str, Any]
    row_count: int = 0
    column_count: int = 0


class OptimizationResultResponse(BaseModel):
    """Optimization result."""
    method: str
    success: bool = False
    result: Any = None
    iterations: int = 0
    message: str = ""


class InterpolationResultResponse(BaseModel):
    """Interpolation result."""
    method: str
    x_new: list[float]
    y_new: list[float]


class FFTResultResponse(BaseModel):
    """FFT analysis result."""
    frequencies: list[float] = Field(default_factory=list)
    magnitudes: list[float] = Field(default_factory=list)
    phases: list[float] = Field(default_factory=list)
    dominant_frequency: float = 0.0


class IntegrationResultResponse(BaseModel):
    """Numerical integration result."""
    method: str
    value: float
    error: float = 0.0


class MLTrainResultResponse(BaseModel):
    """ML training result."""
    model_id: str
    algorithm: str
    metrics: dict[str, Any] = Field(default_factory=dict)
    feature_importance: list[float] = Field(default_factory=list)
    cross_validation_scores: list[float] = Field(default_factory=list)


class MLPredictResultResponse(BaseModel):
    """ML prediction result."""
    model_id: str
    predictions: list[float]
    probabilities: list[list[float]] = Field(default_factory=list)


class MLModelInfoResponse(BaseModel):
    """Trained model descriptor."""
    model_id: str
    algorithm: str
    created_at: str = ""
    metrics: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Statistics endpoint
# ---------------------------------------------------------------------------


@router.post(
    "/statistics",
    response_model=StatisticsResultResponse,
    summary="Compute statistical analysis",
)
async def compute_statistics(
    body: StatisticsRequest,
    current_user: dict[str, Any] = Depends(require_permission(Permission.SCIENTIFIC_EXECUTE)),
) -> dict[str, Any]:
    """Run descriptive and inferential statistics on tabular data using
    Pandas and SciPy.

    Requires ``scientific:execute`` permission.
    """
    from src.scientific.analysis.statistics import StatisticalAnalyzer
    analyzer = StatisticalAnalyzer()
    return analyzer.analyze(
        data=body.data,
        columns=body.columns,
        operations=body.operations,
    )


# ---------------------------------------------------------------------------
# Matrix / linear algebra endpoint
# ---------------------------------------------------------------------------


@router.post(
    "/matrix",
    response_model=MatrixResultResponse,
    summary="Perform matrix operations",
)
async def matrix_operation(
    body: MatrixOperationRequest,
    current_user: dict[str, Any] = Depends(require_permission(Permission.SCIENTIFIC_EXECUTE)),
) -> dict[str, Any]:
    """Execute linear algebra operations (multiply, inverse, eigenvalues, SVD,
    determinant, transpose, norm, solve) using NumPy.

    Requires ``scientific:execute`` permission.
    """
    from src.scientific.analysis.matrix_ops import MatrixOperations
    ops = MatrixOperations()
    return ops.execute(
        operation=body.operation,
        matrix_a=body.matrix_a,
        matrix_b=body.matrix_b,
        vector_b=body.vector_b,
    )


# ---------------------------------------------------------------------------
# Optimization endpoint
# ---------------------------------------------------------------------------


@router.post(
    "/optimize",
    response_model=OptimizationResultResponse,
    summary="Run numerical optimization",
)
async def optimize(
    body: OptimizationRequest,
    current_user: dict[str, Any] = Depends(require_permission(Permission.SCIENTIFIC_EXECUTE)),
) -> dict[str, Any]:
    """Solve optimization problems (minimize, curve fit, root finding, linear
    programming, MILP) using SciPy.

    Requires ``scientific:execute`` permission.
    """
    from src.scientific.analysis.optimizer import ScientificOptimizer
    optimizer = ScientificOptimizer()
    return optimizer.solve(
        method=body.method,
        objective=body.objective,
        bounds=body.bounds,
        constraints=body.constraints,
        initial_guess=body.initial_guess,
        parameters=body.parameters,
    )


# ---------------------------------------------------------------------------
# Interpolation endpoint
# ---------------------------------------------------------------------------


@router.post(
    "/interpolation",
    response_model=InterpolationResultResponse,
    summary="Perform data interpolation",
)
async def interpolate(
    body: InterpolationRequest,
    current_user: dict[str, Any] = Depends(require_permission(Permission.SCIENTIFIC_EXECUTE)),
) -> dict[str, Any]:
    """Interpolate data points using linear, cubic, quadratic, nearest-neighbour,
    or PCHIP methods via SciPy.

    Requires ``scientific:execute`` permission.
    """
    from src.scientific.analysis.interpolation import Interpolator
    interp = Interpolator()
    return interp.interpolate(
        x_data=body.x_data,
        y_data=body.y_data,
        x_new=body.x_new,
        method=body.method,
    )


# ---------------------------------------------------------------------------
# Signal processing / FFT endpoint
# ---------------------------------------------------------------------------


@router.post(
    "/fft",
    response_model=FFTResultResponse,
    summary="Perform FFT / IFFT analysis",
)
async def fft_analysis(
    body: FFTRequest,
    current_user: dict[str, Any] = Depends(require_permission(Permission.SCIENTIFIC_EXECUTE)),
) -> dict[str, Any]:
    """Run Fast Fourier Transform (or inverse FFT) on a discrete signal.

    Requires ``scientific:execute`` permission.
    """
    from src.scientific.analysis.signal_processing import SignalProcessor
    processor = SignalProcessor()
    return processor.fft(
        signal=body.signal,
        sample_rate=body.sample_rate,
        inverse=body.inverse,
    )


# ---------------------------------------------------------------------------
# Numerical integration endpoint
# ---------------------------------------------------------------------------


@router.post(
    "/integrate",
    response_model=IntegrationResultResponse,
    summary="Perform numerical integration",
)
async def integrate(
    body: IntegrationRequest,
    current_user: dict[str, Any] = Depends(require_permission(Permission.SCIENTIFIC_EXECUTE)),
) -> dict[str, Any]:
    """Evaluate a definite integral numerically using quad, trapezoid, Simpson,
    or Romberg methods via SciPy.

    Requires ``scientific:execute`` permission.
    """
    from src.scientific.analysis.calculus import NumericalCalculus
    calc = NumericalCalculus()
    return calc.integrate(
        function=body.function,
        lower_bound=body.lower_bound,
        upper_bound=body.upper_bound,
        method=body.method,
    )


# ---------------------------------------------------------------------------
# Machine Learning -- train, predict, list models
# ---------------------------------------------------------------------------


@router.post(
    "/ml/train",
    response_model=MLTrainResultResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Train a machine learning model",
)
async def train_model(
    body: MLTrainRequest,
    request: Request,
    current_user: dict[str, Any] = Depends(require_permission(Permission.SCIENTIFIC_EXECUTE)),
    client_ip: str = Depends(get_client_ip),
) -> dict[str, Any]:
    """Train a scikit-learn model (classification, regression, clustering, or
    dimensionality reduction).

    Requires ``scientific:execute`` permission.
    """
    from src.scientific.ml.trainer import MLTrainer
    trainer = MLTrainer()
    result = await trainer.train(
        algorithm=body.algorithm,
        features=body.features,
        labels=body.labels,
        test_size=body.test_size,
        hyperparameters=body.hyperparameters,
        cross_validation=body.cross_validation,
    )
    await AuditService.log(
        action="scientific.ml_trained",
        resource_type="MLModel",
        resource_id=result.get("model_id"),
        user_id=current_user["user_id"],
        details={"algorithm": body.algorithm, "features": len(body.features)},
        ip_address=client_ip,
        user_agent=request.headers.get("User-Agent"),
    )
    return result


@router.post(
    "/ml/predict",
    response_model=MLPredictResultResponse,
    summary="Run predictions on a trained model",
)
async def predict(
    body: MLPredictRequest,
    current_user: dict[str, Any] = Depends(require_permission(Permission.SCIENTIFIC_EXECUTE)),
) -> dict[str, Any]:
    """Generate predictions from a previously trained model.

    Requires ``scientific:execute`` permission.
    """
    from src.scientific.ml.trainer import MLTrainer
    trainer = MLTrainer()
    return await trainer.predict(model_id=body.model_id, features=body.features)


@router.get(
    "/ml/models",
    response_model=list[MLModelInfoResponse],
    summary="List trained ML models",
)
async def list_models(
    current_user: dict[str, Any] = Depends(require_permission(Permission.SCIENTIFIC_READ)),
) -> list[dict[str, Any]]:
    """List all trained machine learning models stored on the platform.

    Requires ``scientific:read`` permission.
    """
    from src.scientific.ml.trainer import MLTrainer
    trainer = MLTrainer()
    return await trainer.list_models()
