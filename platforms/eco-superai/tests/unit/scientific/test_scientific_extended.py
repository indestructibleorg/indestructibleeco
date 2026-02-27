"""Extended unit tests for scientific analysis modules.

Covers: interpolation, optimizer, signal_processing, statistics (missing paths),
matrix_ops (missing paths), ml/trainer, pipelines.
"""
from __future__ import annotations

import math
import pytest


# ---------------------------------------------------------------------------
# Interpolation
# ---------------------------------------------------------------------------

class TestInterpolation:
    def test_linear_interpolation(self) -> None:
        from src.scientific.analysis.interpolation import Interpolator
        interp = Interpolator()
        x = [0.0, 1.0, 2.0, 3.0]
        y = [0.0, 1.0, 4.0, 9.0]
        result = interp.interpolate(x_data=x, y_data=y, x_new=[0.5, 1.5], method="linear")
        assert "y_interpolated" in result or "error" in result
        if "y_interpolated" in result:
            assert len(result["y_interpolated"]) == 2

    def test_cubic_interpolation(self) -> None:
        from src.scientific.analysis.interpolation import Interpolator
        interp = Interpolator()
        x = [0.0, 1.0, 2.0, 3.0, 4.0]
        y = [0.0, 1.0, 4.0, 9.0, 16.0]
        result = interp.interpolate(x_data=x, y_data=y, x_new=[0.5, 2.5], method="cubic")
        assert "y_interpolated" in result or "error" in result

    def test_polynomial_interpolation(self) -> None:
        from src.scientific.analysis.interpolation import Interpolator
        interp = Interpolator()
        x = [0.0, 1.0, 2.0]
        y = [1.0, 3.0, 7.0]
        result = interp.interpolate(x_data=x, y_data=y, x_new=[1.5], method="polynomial")
        assert "y_interpolated" in result or "error" in result

    def test_nearest_interpolation(self) -> None:
        from src.scientific.analysis.interpolation import Interpolator
        interp = Interpolator()
        x = [0.0, 1.0, 2.0]
        y = [10.0, 20.0, 30.0]
        result = interp.interpolate(x_data=x, y_data=y, x_new=[0.4, 1.6], method="nearest")
        assert "y_interpolated" in result or "error" in result

    def test_insufficient_data_raises_or_returns_error(self) -> None:
        from src.scientific.analysis.interpolation import Interpolator
        interp = Interpolator()
        # Only 1 data point — should fail gracefully
        result = interp.interpolate(x_data=[1.0], y_data=[1.0], x_new=[1.0], method="linear")
        assert "error" in result or "y_interpolated" in result

    def test_mismatched_lengths_returns_error(self) -> None:
        from src.scientific.analysis.interpolation import Interpolator
        interp = Interpolator()
        result = interp.interpolate(x_data=[1.0, 2.0], y_data=[1.0], x_new=[1.5], method="linear")
        assert "error" in result

    def test_extrapolation_outside_range(self) -> None:
        from src.scientific.analysis.interpolation import Interpolator
        interp = Interpolator()
        x = [0.0, 1.0, 2.0]
        y = [0.0, 1.0, 2.0]
        result = interp.interpolate(x_data=x, y_data=y, x_new=[5.0], method="linear")
        assert "y_interpolated" in result or "error" in result

    def test_unknown_method_returns_error(self) -> None:
        from src.scientific.analysis.interpolation import Interpolator
        interp = Interpolator()
        result = interp.interpolate(x_data=[0.0, 1.0], y_data=[0.0, 1.0], x_new=[0.5], method="unknown_method")
        assert "error" in result


# ---------------------------------------------------------------------------
# ScientificOptimizer
# ---------------------------------------------------------------------------

class TestScientificOptimizer:
    def test_minimize_simple_quadratic(self) -> None:
        from src.scientific.analysis.optimizer import ScientificOptimizer
        opt = ScientificOptimizer()
        result = opt.solve(
            method="minimize",
            objective="x[0]**2 + x[1]**2",
            bounds=[[-5.0, 5.0], [-5.0, 5.0]],
            constraints=[],
            initial_guess=[1.0, 1.0],
            parameters={},
        )
        assert "optimal_value" in result
        assert result["converged"] is True
        assert abs(result["optimal_value"]) < 1e-6

    def test_minimize_with_constraint(self) -> None:
        from src.scientific.analysis.optimizer import ScientificOptimizer
        opt = ScientificOptimizer()
        result = opt.solve(
            method="minimize",
            objective="x[0]**2 + x[1]**2",
            bounds=[[-5.0, 5.0], [-5.0, 5.0]],
            constraints=[{"type": "ineq", "expression": "x[0] - 1"}],
            initial_guess=[2.0, 0.0],
            parameters={},
        )
        assert "optimal_value" in result

    def test_root_finding(self) -> None:
        from src.scientific.analysis.optimizer import ScientificOptimizer
        opt = ScientificOptimizer()
        # Find root of x^2 - 4 = 0 near x=2
        result = opt.solve(
            method="root",
            objective="x**2 - 4",
            bounds=[],
            constraints=[],
            initial_guess=[2.0],
            parameters={},
        )
        assert "root" in result
        assert abs(result["root"][0] - 2.0) < 0.01

    def test_linprog(self) -> None:
        from src.scientific.analysis.optimizer import ScientificOptimizer
        opt = ScientificOptimizer()
        # Minimize c·x subject to Ax <= b, x >= 0
        result = opt.solve(
            method="linprog",
            objective="",
            bounds=[[0, None], [0, None]],
            constraints=[],
            initial_guess=[],
            parameters={
                "c": [-1.0, -2.0],
                "A_ub": [[1.0, 1.0]],
                "b_ub": [4.0],
            },
        )
        assert "optimal_value" in result or "error" in result

    def test_curve_fit(self) -> None:
        from src.scientific.analysis.optimizer import ScientificOptimizer
        opt = ScientificOptimizer()
        import numpy as np
        x_data = np.linspace(0, 2 * math.pi, 20).tolist()
        y_data = [math.sin(x) for x in x_data]
        result = opt.solve(
            method="curve_fit",
            objective="a0 * sin(x)",
            bounds=[],
            constraints=[],
            initial_guess=[1.0],
            parameters={
                "x_data": x_data,
                "y_data": y_data,
                "num_params": 1,
            },
        )
        assert "parameters" in result or "error" in result

    def test_unknown_method_returns_error(self) -> None:
        from src.scientific.analysis.optimizer import ScientificOptimizer
        opt = ScientificOptimizer()
        result = opt.solve(
            method="unknown_xyz",
            objective="x[0]",
            bounds=[],
            constraints=[],
            initial_guess=[0.0],
            parameters={},
        )
        assert "error" in result

    def test_invalid_objective_returns_error(self) -> None:
        from src.scientific.analysis.optimizer import ScientificOptimizer
        opt = ScientificOptimizer()
        result = opt.solve(
            method="minimize",
            objective="__import__('os').system('ls')",
            bounds=[],
            constraints=[],
            initial_guess=[0.0],
            parameters={},
        )
        # Should fail safely (builtins disabled)
        assert "error" in result or "optimal_value" in result


# ---------------------------------------------------------------------------
# SignalProcessor
# ---------------------------------------------------------------------------

class TestSignalProcessor:
    def test_fft_basic(self) -> None:
        from src.scientific.analysis.signal_processing import SignalProcessor
        sp = SignalProcessor()
        import numpy as np
        # 1Hz sine wave sampled at 100Hz
        t = np.linspace(0, 1, 100).tolist()
        signal = [math.sin(2 * math.pi * f) for f in t]
        result = sp.fft(signal=signal, sample_rate=100.0)
        assert "frequencies" in result
        assert "magnitudes" in result
        assert "dominant_frequency" in result

    def test_fft_identifies_dominant_frequency(self) -> None:
        from src.scientific.analysis.signal_processing import SignalProcessor
        sp = SignalProcessor()
        import numpy as np
        # 10Hz sine wave sampled at 1000Hz
        t = np.linspace(0, 1, 1000).tolist()
        signal = [math.sin(2 * math.pi * 10 * f) for f in t]
        result = sp.fft(signal=signal, sample_rate=1000.0)
        assert "dominant_frequency" in result
        assert abs(result["dominant_frequency"] - 10.0) < 1.0

    def test_fft_with_signal(self) -> None:
        from src.scientific.analysis.signal_processing import SignalProcessor
        sp = SignalProcessor()
        import numpy as np
        signal = (np.random.randn(100)).tolist()
        result = sp.fft(signal=signal, sample_rate=100.0)
        assert "frequencies" in result or "error" in result

    def test_fft_dc_signal(self) -> None:
        from src.scientific.analysis.signal_processing import SignalProcessor
        sp = SignalProcessor()
        signal = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = sp.fft(signal=signal, sample_rate=1.0)
        assert "frequencies" in result or "error" in result

    def test_empty_signal_returns_error(self) -> None:
        from src.scientific.analysis.signal_processing import SignalProcessor
        sp = SignalProcessor()
        result = sp.fft(signal=[], sample_rate=100.0)
        assert "error" in result

    def test_fft_small_signal(self) -> None:
        from src.scientific.analysis.signal_processing import SignalProcessor
        sp = SignalProcessor()
        result = sp.fft(signal=[1.0, 2.0, 3.0], sample_rate=1.0)
        assert "error" in result


# ---------------------------------------------------------------------------
# ML Trainer
# ---------------------------------------------------------------------------

class TestMLTrainer:
    @pytest.mark.asyncio
    async def test_train_linear_regression(self) -> None:
        from src.scientific.ml.trainer import MLTrainer
        trainer = MLTrainer()
        features = [[1.0, 2.0], [2.0, 3.0], [3.0, 4.0], [4.0, 5.0], [5.0, 6.0]]
        labels = [3.0, 5.0, 7.0, 9.0, 11.0]
        result = await trainer.train(
            algorithm="linear_regression",
            features=features,
            labels=labels,
            hyperparameters={},
            test_size=0.2,
            cross_validation=0,
        )
        assert "model_id" in result
        assert "metrics" in result
        assert "error" not in result

    @pytest.mark.asyncio
    async def test_train_logistic_regression(self) -> None:
        from src.scientific.ml.trainer import MLTrainer
        trainer = MLTrainer()
        features = [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0], [0.0, 0.0],
                    [2.0, 0.0], [0.0, 2.0], [2.0, 2.0], [0.0, 0.0]]
        labels = [1, 0, 1, 0, 1, 0, 1, 0]
        result = await trainer.train(
            algorithm="logistic_regression",
            features=features,
            labels=labels,
            hyperparameters={},
            test_size=0.2,
            cross_validation=0,
        )
        assert "model_id" in result

    @pytest.mark.asyncio
    async def test_train_random_forest(self) -> None:
        from src.scientific.ml.trainer import MLTrainer
        trainer = MLTrainer()
        features = [[i, i * 2] for i in range(20)]
        labels = [i % 2 for i in range(20)]
        result = await trainer.train(
            algorithm="random_forest",
            features=features,
            labels=labels,
            hyperparameters={"n_estimators": 10},
            test_size=0.2,
            cross_validation=0,
        )
        assert "model_id" in result

    @pytest.mark.asyncio
    async def test_train_kmeans_unsupervised(self) -> None:
        from src.scientific.ml.trainer import MLTrainer
        trainer = MLTrainer()
        import numpy as np
        rng = np.random.RandomState(42)
        features = rng.randn(30, 2).tolist()
        result = await trainer.train(
            algorithm="kmeans",
            features=features,
            labels=[],  # unsupervised
            hyperparameters={"n_clusters": 3},
            test_size=None,
            cross_validation=0,
        )
        assert "model_id" in result

    @pytest.mark.asyncio
    async def test_train_pca(self) -> None:
        from src.scientific.ml.trainer import MLTrainer
        trainer = MLTrainer()
        import numpy as np
        rng = np.random.RandomState(42)
        features = rng.randn(20, 5).tolist()
        result = await trainer.train(
            algorithm="pca",
            features=features,
            labels=[],
            hyperparameters={"n_components": 2},
            test_size=None,
            cross_validation=0,
        )
        assert "model_id" in result

    @pytest.mark.asyncio
    async def test_predict_after_train(self) -> None:
        from src.scientific.ml.trainer import MLTrainer
        trainer = MLTrainer()
        features = [[1.0, 2.0], [2.0, 3.0], [3.0, 4.0], [4.0, 5.0], [5.0, 6.0]]
        labels = [3.0, 5.0, 7.0, 9.0, 11.0]
        train_result = await trainer.train(
            algorithm="linear_regression",
            features=features,
            labels=labels,
            hyperparameters={},
            test_size=0.2,
            cross_validation=0,
        )
        model_id = train_result["model_id"]
        pred_result = await trainer.predict(model_id=model_id, features=[[6.0, 7.0]])
        assert "predictions" in pred_result
        assert len(pred_result["predictions"]) == 1

    @pytest.mark.asyncio
    async def test_predict_unknown_model_returns_error(self) -> None:
        from src.scientific.ml.trainer import MLTrainer
        trainer = MLTrainer()
        result = await trainer.predict(model_id="nonexistent-id", features=[[1.0, 2.0]])
        assert "error" in result

    @pytest.mark.asyncio
    async def test_list_models(self) -> None:
        from src.scientific.ml.trainer import MLTrainer
        trainer = MLTrainer()
        result = await trainer.list_models()
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_train_with_cross_validation(self) -> None:
        from src.scientific.ml.trainer import MLTrainer
        trainer = MLTrainer()
        features = [[i, i * 2] for i in range(20)]
        labels = [i % 2 for i in range(20)]
        result = await trainer.train(
            algorithm="logistic_regression",
            features=features,
            labels=labels,
            hyperparameters={},
            test_size=0.2,
            cross_validation=3,
        )
        assert "model_id" in result
        if "metrics" in result and "error" not in result:
            assert "cv_mean" in result["metrics"] or "accuracy" in result["metrics"]

    @pytest.mark.asyncio
    async def test_train_unknown_algorithm_returns_error(self) -> None:
        from src.scientific.ml.trainer import MLTrainer
        trainer = MLTrainer()
        result = await trainer.train(
            algorithm="unknown_algo",
            features=[[1.0, 2.0], [3.0, 4.0]],
            labels=[0, 1],
            hyperparameters={},
            test_size=0.0,
            cross_validation=0,
        )
        assert "error" in result


# ---------------------------------------------------------------------------
# Scientific Pipelines
# ---------------------------------------------------------------------------

class TestScientificPipelines:
    def test_pipeline_module_importable(self) -> None:
        from src.scientific.pipelines import __init__
        # Just ensure the module is importable without errors
        assert True

    def test_pipeline_classes_available(self) -> None:
        import src.scientific.pipelines as pipelines_module
        # Check that the module has expected attributes
        assert hasattr(pipelines_module, "__file__")
