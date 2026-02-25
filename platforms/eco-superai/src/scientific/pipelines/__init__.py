"""Scientific data processing pipelines — composable ETL and analysis chains."""
from __future__ import annotations

import time
from typing import Any, Callable

import structlog
import numpy as np

logger = structlog.get_logger(__name__)


class PipelineStep:
    """A single step in a data pipeline."""

    def __init__(self, name: str, func: Callable, params: dict[str, Any] | None = None) -> None:
        self.name = name
        self.func = func
        self.params = params or {}

    def execute(self, data: Any) -> Any:
        return self.func(data, **self.params)


class DataPipeline:
    """Composable data processing pipeline with logging and error handling."""

    def __init__(self, name: str = "pipeline") -> None:
        self._name = name
        self._steps: list[PipelineStep] = []
        self._results: list[dict[str, Any]] = []

    def add_step(self, name: str, func: Callable, params: dict[str, Any] | None = None) -> DataPipeline:
        self._steps.append(PipelineStep(name=name, func=func, params=params))
        return self

    def execute(self, data: Any) -> dict[str, Any]:
        logger.info("pipeline_start", pipeline=self._name, steps=len(self._steps))
        self._results = []
        current_data = data
        total_start = time.perf_counter()

        for i, step in enumerate(self._steps):
            step_start = time.perf_counter()
            try:
                current_data = step.execute(current_data)
                elapsed = (time.perf_counter() - step_start) * 1000
                step_result = {
                    "step": i + 1,
                    "name": step.name,
                    "status": "success",
                    "elapsed_ms": round(elapsed, 2),
                    "output_shape": self._get_shape(current_data),
                }
                self._results.append(step_result)
                logger.info("pipeline_step_complete", **step_result)
            except Exception as e:
                elapsed = (time.perf_counter() - step_start) * 1000
                step_result = {
                    "step": i + 1,
                    "name": step.name,
                    "status": "failed",
                    "elapsed_ms": round(elapsed, 2),
                    "error": str(e),
                }
                self._results.append(step_result)
                logger.error("pipeline_step_failed", **step_result)
                return {
                    "pipeline": self._name,
                    "status": "failed",
                    "failed_at_step": i + 1,
                    "steps": self._results,
                    "total_elapsed_ms": round((time.perf_counter() - total_start) * 1000, 2),
                }

        total_elapsed = (time.perf_counter() - total_start) * 1000
        logger.info("pipeline_complete", pipeline=self._name, total_ms=round(total_elapsed, 2))

        return {
            "pipeline": self._name,
            "status": "success",
            "data": self._serialize(current_data),
            "steps": self._results,
            "total_elapsed_ms": round(total_elapsed, 2),
        }

    @staticmethod
    def _get_shape(data: Any) -> str:
        if isinstance(data, np.ndarray):
            return str(data.shape)
        if isinstance(data, (list, tuple)):
            return f"({len(data)},)"
        if isinstance(data, dict):
            return f"dict[{len(data)} keys]"
        return type(data).__name__

    @staticmethod
    def _serialize(data: Any) -> Any:
        if isinstance(data, np.ndarray):
            return data.tolist()
        if isinstance(data, np.generic):
            return data.item()
        return data


# --- Built-in Pipeline Steps ---

def normalize(data: Any, method: str = "minmax") -> Any:
    """Normalize numerical data."""
    arr = np.array(data, dtype=float)
    if method == "minmax":
        mn, mx = arr.min(), arr.max()
        return ((arr - mn) / (mx - mn + 1e-10)).tolist() if arr.ndim == 1 else ((arr - mn) / (mx - mn + 1e-10))
    elif method == "zscore":
        return ((arr - arr.mean()) / (arr.std() + 1e-10)).tolist() if arr.ndim == 1 else ((arr - arr.mean()) / (arr.std() + 1e-10))
    return arr


def remove_outliers(data: Any, threshold: float = 3.0) -> Any:
    """Remove outliers using z-score method."""
    arr = np.array(data, dtype=float)
    if arr.ndim == 1:
        z = np.abs((arr - arr.mean()) / (arr.std() + 1e-10))
        return arr[z < threshold].tolist()
    return arr


def fill_missing(data: Any, strategy: str = "mean") -> Any:
    """Fill NaN values."""
    arr = np.array(data, dtype=float)
    if strategy == "mean":
        mean_val = np.nanmean(arr)
        arr = np.where(np.isnan(arr), mean_val, arr)
    elif strategy == "median":
        median_val = np.nanmedian(arr)
        arr = np.where(np.isnan(arr), median_val, arr)
    elif strategy == "zero":
        arr = np.where(np.isnan(arr), 0.0, arr)
    return arr.tolist() if arr.ndim == 1 else arr


def downsample(data: Any, factor: int = 2) -> Any:
    """Downsample data by taking every nth element."""
    arr = np.array(data)
    return arr[::factor].tolist() if arr.ndim == 1 else arr[::factor]


__all__ = ["DataPipeline", "PipelineStep", "normalize", "remove_outliers", "fill_missing", "downsample"]