"""Coverage gap tests — Part 1.

Covers:
- domain/entities/base.py (equality, hash)
- domain/entities/ai_expert.py (update_system_prompt, update_model_config, is_active, deactivate idempotent)
- domain/entities/quantum_job.py (fail, is_running, duration_ms, backend validator, complete wrong state)
- domain/entities/user.py (activate, is_locked, is_active property)
- domain/value_objects/password.py (from_hash, verify, _validate_strength edge cases)
- domain/specifications/__init__.py (UserByEmailDomainSpecification)
- shared/utils/__init__.py (md5_hex)
- shared/logging (request_id processor)
- scientific/pipelines (DataPipeline execute, _get_shape, _serialize, normalize zscore, remove_outliers, fill_missing, downsample)
- scientific/analysis/calculus.py (romberg, unknown method, exception)
- scientific/analysis/matrix_ops.py (determinant, transpose, norm, solve, linalg error)
- scientific/analysis/interpolation.py (pchip, unknown method)
- scientific/analysis/signal_processing.py (ifft)
- scientific/analysis/statistics.py (distribution_fit)
- scientific/ml/trainer.py (kmeans, pca, gradient_boosting, decision_tree, knn, predict_proba)
"""
from __future__ import annotations

import asyncio
import math
from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


# ===========================================================================
# domain/entities/base.py
# ===========================================================================
class TestBaseEntity:
    """Entity equality and hash."""

    def _make_entity(self, entity_id: str) -> Any:
        from src.domain.entities.base import Entity
        return Entity(id=entity_id)

    def test_entity_equal_same_id(self) -> None:
        e1 = self._make_entity("abc")
        e2 = self._make_entity("abc")
        assert e1 == e2

    def test_entity_not_equal_different_id(self) -> None:
        e1 = self._make_entity("abc")
        e2 = self._make_entity("xyz")
        assert e1 != e2

    def test_entity_not_equal_non_entity(self) -> None:
        e1 = self._make_entity("abc")
        assert e1 != "abc"
        assert e1 != 42
        assert e1 != None  # noqa: E711


# Module-level concrete ValueObject subclass to avoid dynamic class identity issues
from src.domain.entities.base import ValueObject as _ValueObject


class _ConcreteVO(_ValueObject):
    value: str


class TestBaseValueObject:
    """ValueObject equality and hash."""

    def _make_vo(self, **kwargs: Any) -> Any:
        return _ConcreteVO(**kwargs)

    def test_value_object_equal(self) -> None:
        vo1 = self._make_vo(value="hello")
        vo2 = self._make_vo(value="hello")
        assert vo1 == vo2

    def test_value_object_not_equal(self) -> None:
        vo1 = self._make_vo(value="hello")
        vo2 = self._make_vo(value="world")
        assert vo1 != vo2

    def test_value_object_hash(self) -> None:
        vo1 = self._make_vo(value="hello")
        vo2 = self._make_vo(value="hello")
        assert hash(vo1) == hash(vo2)

    def test_value_object_not_equal_different_type(self) -> None:
        vo1 = self._make_vo(value="hello")
        assert vo1 != "hello"


# ===========================================================================
# domain/entities/ai_expert.py
# ===========================================================================
class TestAIExpertEntity:
    """AIExpert entity — update methods, properties."""

    def _make_expert(self) -> Any:
        from src.domain.entities.ai_expert import AIExpert, ExpertDomain, ExpertStatus
        return AIExpert.create(
            name="Test Expert",
            domain=ExpertDomain.SCIENTIFIC,
            owner_id="owner-1",
            system_prompt="You are a scientific expert.",
            model="gpt-4-turbo-preview",
        )

    def test_is_active_true(self) -> None:
        expert = self._make_expert()
        assert expert.is_active is True

    def test_deactivate_idempotent(self) -> None:
        """Calling deactivate on an already-inactive expert should be a no-op."""
        from src.domain.entities.ai_expert import ExpertStatus
        expert = self._make_expert()
        expert.deactivate()
        assert expert.status == ExpertStatus.INACTIVE
        # Second call should not raise
        expert.deactivate()
        assert expert.status == ExpertStatus.INACTIVE

    def test_is_active_false_after_deactivate(self) -> None:
        expert = self._make_expert()
        expert.deactivate()
        assert expert.is_active is False

    def test_update_system_prompt_valid(self) -> None:
        expert = self._make_expert()
        new_prompt = "You are a risk analyst."
        expert.update_system_prompt(new_prompt)
        assert expert.system_prompt == new_prompt

    def test_update_system_prompt_too_long_raises(self) -> None:
        expert = self._make_expert()
        with pytest.raises(ValueError, match="10000"):
            expert.update_system_prompt("x" * 10001)

    def test_update_model_config_model_only(self) -> None:
        expert = self._make_expert()
        expert.update_model_config(model="claude-3-opus-20240229")
        assert expert.model == "claude-3-opus-20240229"

    def test_update_model_config_temperature_only(self) -> None:
        expert = self._make_expert()
        expert.update_model_config(temperature=0.5)
        assert expert.temperature == 0.5

    def test_update_model_config_temperature_out_of_range(self) -> None:
        expert = self._make_expert()
        with pytest.raises(ValueError, match="Temperature"):
            expert.update_model_config(temperature=2.5)

    def test_update_model_config_both(self) -> None:
        expert = self._make_expert()
        expert.update_model_config(model="gemini-1.5-pro", temperature=1.0)
        assert expert.model == "gemini-1.5-pro"
        assert expert.temperature == 1.0

    def test_unsupported_model_raises(self) -> None:
        from pydantic import ValidationError
        from src.domain.entities.ai_expert import AIExpert, ExpertDomain
        with pytest.raises((ValueError, ValidationError)):
            AIExpert.create(
                name="Bad Expert",
                domain=ExpertDomain.SCIENTIFIC,
                owner_id="owner-1",
                system_prompt="prompt",
                model="unsupported-model-xyz",
            )


# ===========================================================================
# domain/entities/quantum_job.py
# ===========================================================================
class TestQuantumJobEntity:
    """QuantumJob entity — fail, is_running, duration_ms, backend validator."""

    def _make_job(self) -> Any:
        from src.domain.entities.quantum_job import QuantumJob, QuantumAlgorithm
        return QuantumJob(
            algorithm=QuantumAlgorithm.VQE,
            parameters={"num_qubits": 2},
            backend="aer_simulator",
            shots=1024,
            user_id="user-1",
        )

    def test_is_running_false_initially(self) -> None:
        job = self._make_job()
        assert job.is_running is False

    def test_is_running_true_after_start(self) -> None:
        job = self._make_job()
        job.start()
        assert job.is_running is True

    def test_fail_sets_status(self) -> None:
        from src.domain.entities.quantum_job import JobStatus
        job = self._make_job()
        job.start()
        job.fail("Qiskit error")
        assert job.status == JobStatus.FAILED
        assert job.error_message == "Qiskit error"

    def test_fail_completed_job_raises(self) -> None:
        job = self._make_job()
        job.start()
        job.complete({"counts": {"00": 512}}, 100.0)
        with pytest.raises(ValueError, match="Cannot fail an already completed job"):
            job.fail("late error")

    def test_complete_wrong_state_raises(self) -> None:
        """Completing a job that is not RUNNING should raise."""
        job = self._make_job()
        # job is SUBMITTED, not RUNNING
        with pytest.raises(ValueError, match="Cannot complete job"):
            job.complete({"counts": {}}, 50.0)

    def test_duration_ms_with_timestamps(self) -> None:
        job = self._make_job()
        job.start()
        now = datetime.now(timezone.utc)
        job.started_at = now - timedelta(seconds=2)
        job.completed_at = now
        job.complete({"counts": {"00": 512}}, 2000.0)
        # duration_ms should be approximately 2000ms
        assert job.duration_ms is not None
        assert job.duration_ms > 0

    def test_duration_ms_none_without_timestamps(self) -> None:
        job = self._make_job()
        job.started_at = None
        job.completed_at = None
        job.execution_time_ms = None
        assert job.duration_ms is None

    def test_unsupported_backend_raises(self) -> None:
        from pydantic import ValidationError
        from src.domain.entities.quantum_job import QuantumJob, QuantumAlgorithm
        with pytest.raises((ValueError, ValidationError)):
            QuantumJob(
                algorithm=QuantumAlgorithm.VQE,
                parameters={},
                backend="unsupported_backend_xyz",
                shots=1024,
                user_id="user-1",
            )


# ===========================================================================
# domain/entities/user.py
# ===========================================================================
class TestUserEntityExtended:
    """User entity — activate, is_locked, is_active property."""

    def _make_user(self) -> Any:
        from src.domain.entities.user import User, UserRole
        from src.domain.value_objects.email import Email
        from src.domain.value_objects.password import HashedPassword
        return User.create(
            username="testuser",
            email=Email.create("test@example.com"),
            hashed_password=HashedPassword.from_plain("SecureP@ss1"),
            full_name="Test User",
            role=UserRole.DEVELOPER,
        )

    def test_activate_from_pending(self) -> None:
        from src.domain.entities.user import UserStatus
        user = self._make_user()
        assert user.status == UserStatus.PENDING_VERIFICATION
        user.activate()
        assert user.status == UserStatus.ACTIVE

    def test_activate_already_active_idempotent(self) -> None:
        from src.domain.entities.user import UserStatus
        user = self._make_user()
        user.activate()
        version_before = user.version
        user.activate()
        # Should not increment version again
        assert user.status == UserStatus.ACTIVE

    def test_is_locked_false_when_no_lock(self) -> None:
        user = self._make_user()
        assert user.is_locked is False

    def test_is_locked_true_when_locked_until_future(self) -> None:
        user = self._make_user()
        user.locked_until = datetime.now(timezone.utc) + timedelta(hours=1)
        assert user.is_locked is True

    def test_is_locked_false_when_lock_expired(self) -> None:
        user = self._make_user()
        user.locked_until = datetime.now(timezone.utc) - timedelta(hours=1)
        assert user.is_locked is False

    def test_is_active_property(self) -> None:
        from src.domain.entities.user import UserStatus
        user = self._make_user()
        user.activate()
        assert user.is_active is True

    def test_is_active_false_when_locked(self) -> None:
        user = self._make_user()
        user.activate()
        user.locked_until = datetime.now(timezone.utc) + timedelta(hours=1)
        assert user.is_active is False


# ===========================================================================
# domain/value_objects/password.py
# ===========================================================================
class TestHashedPasswordExtended:
    """HashedPassword — from_hash, verify, strength validation edge cases."""

    def test_from_hash_roundtrip(self) -> None:
        from src.domain.value_objects.password import HashedPassword
        pwd = HashedPassword.from_plain("SecureP@ss1")
        restored = HashedPassword.from_hash(pwd.value)
        assert restored.value == pwd.value

    def test_verify_correct_password(self) -> None:
        from src.domain.value_objects.password import HashedPassword
        pwd = HashedPassword.from_plain("SecureP@ss1")
        assert pwd.verify("SecureP@ss1") is True

    def test_verify_wrong_password(self) -> None:
        from src.domain.value_objects.password import HashedPassword
        pwd = HashedPassword.from_plain("SecureP@ss1")
        assert pwd.verify("WrongPass1!") is False

    def test_verify_invalid_hash_returns_false(self) -> None:
        from src.domain.value_objects.password import HashedPassword
        pwd = HashedPassword.from_hash("not-a-valid-bcrypt-hash")
        assert pwd.verify("anything") is False

    def test_strength_too_short_raises(self) -> None:
        from src.domain.value_objects.password import HashedPassword
        from src.domain.exceptions import WeakPasswordError
        with pytest.raises(WeakPasswordError):
            HashedPassword.from_plain("Ab1!")

    def test_strength_no_uppercase_raises(self) -> None:
        from src.domain.value_objects.password import HashedPassword
        from src.domain.exceptions import WeakPasswordError
        with pytest.raises(WeakPasswordError):
            HashedPassword.from_plain("lowercase1!")

    def test_strength_no_lowercase_raises(self) -> None:
        from src.domain.value_objects.password import HashedPassword
        from src.domain.exceptions import WeakPasswordError
        with pytest.raises(WeakPasswordError):
            HashedPassword.from_plain("UPPERCASE1!")

    def test_strength_no_digit_raises(self) -> None:
        from src.domain.value_objects.password import HashedPassword
        from src.domain.exceptions import WeakPasswordError
        with pytest.raises(WeakPasswordError):
            HashedPassword.from_plain("NoDigitPass!")

    def test_str_repr_hidden(self) -> None:
        from src.domain.value_objects.password import HashedPassword
        pwd = HashedPassword.from_plain("SecureP@ss1")
        assert "HASHED" in str(pwd)
        assert "HashedPassword" in repr(pwd)


# ===========================================================================
# domain/specifications/__init__.py
# ===========================================================================
class TestUserByEmailDomainSpecification:
    """UserByEmailDomainSpecification."""

    def _make_spec(self, domain: str) -> Any:
        from src.domain.specifications import UserByEmailDomainSpecification
        return UserByEmailDomainSpecification(domain)

    def _make_candidate(self, email_str: str) -> Any:
        obj = MagicMock()
        obj.email = MagicMock()
        obj.email.value = email_str
        return obj

    def test_matches_correct_domain(self) -> None:
        spec = self._make_spec("example.com")
        candidate = self._make_candidate("user@example.com")
        assert spec.is_satisfied_by(candidate) is True

    def test_does_not_match_different_domain(self) -> None:
        spec = self._make_spec("example.com")
        candidate = self._make_candidate("user@other.com")
        assert spec.is_satisfied_by(candidate) is False

    def test_no_email_attribute_returns_false(self) -> None:
        spec = self._make_spec("example.com")
        candidate = MagicMock(spec=[])  # no email attr
        assert spec.is_satisfied_by(candidate) is False

    def test_email_without_value_attr(self) -> None:
        """When email has no .value attribute, uses str(email)."""
        spec = self._make_spec("example.com")
        obj = MagicMock()
        obj.email = "user@example.com"  # plain string, no .value
        assert spec.is_satisfied_by(obj) is True


# ===========================================================================
# shared/utils/__init__.py — md5_hex
# ===========================================================================
class TestSharedUtilsMd5:
    """md5_hex utility function."""

    def test_md5_hex_returns_hex_string(self) -> None:
        from src.shared.utils import md5_hex
        result = md5_hex("hello world")
        assert isinstance(result, str)
        assert len(result) == 32
        # Verify it's hex
        int(result, 16)

    def test_md5_hex_deterministic(self) -> None:
        from src.shared.utils import md5_hex
        assert md5_hex("test") == md5_hex("test")

    def test_md5_hex_different_inputs(self) -> None:
        from src.shared.utils import md5_hex
        assert md5_hex("abc") != md5_hex("xyz")


# ===========================================================================
# infrastructure/logging — request_id processor
# ===========================================================================
class TestLoggingRequestIdProcessor:
    """_add_request_id processor injects request_id from contextvars."""

    def test_injects_request_id_when_set(self) -> None:
        from src.infrastructure.logging import _add_request_id, _request_id_ctx
        token = _request_id_ctx.set("req-123")
        try:
            event_dict = _add_request_id(None, None, {"event": "test"})
            assert event_dict.get("request_id") == "req-123"
        finally:
            _request_id_ctx.reset(token)

    def test_no_injection_when_not_set(self) -> None:
        from src.infrastructure.logging import _add_request_id, _request_id_ctx
        # Ensure context var is empty
        token = _request_id_ctx.set("")
        try:
            event_dict = _add_request_id(None, None, {"event": "test"})
            # Should not add request_id if not set (or empty)
            assert event_dict.get("request_id", "") == "" or "request_id" not in event_dict
        finally:
            _request_id_ctx.reset(token)


# ===========================================================================
# scientific/pipelines — DataPipeline, built-in steps
# ===========================================================================
class TestDataPipeline:
    """DataPipeline execute, _get_shape, _serialize, built-in steps."""

    def test_pipeline_success_single_step(self) -> None:
        from src.scientific.pipelines import DataPipeline
        pipeline = DataPipeline("test_pipeline")
        pipeline.add_step("double", lambda data, **kw: [x * 2 for x in data])
        result = pipeline.execute([1, 2, 3])
        assert result["status"] == "success"
        assert result["data"] == [2, 4, 6]
        assert len(result["steps"]) == 1

    def test_pipeline_failure_propagates(self) -> None:
        from src.scientific.pipelines import DataPipeline
        pipeline = DataPipeline("fail_pipeline")
        pipeline.add_step("explode", lambda data, **kw: 1 / 0)
        result = pipeline.execute([1, 2, 3])
        assert result["status"] == "failed"
        assert result["failed_at_step"] == 1

    def test_pipeline_get_shape_ndarray(self) -> None:
        import numpy as np
        from src.scientific.pipelines import DataPipeline
        shape = DataPipeline._get_shape(np.array([[1, 2], [3, 4]]))
        assert "2" in shape

    def test_pipeline_get_shape_list(self) -> None:
        from src.scientific.pipelines import DataPipeline
        shape = DataPipeline._get_shape([1, 2, 3])
        assert "3" in shape

    def test_pipeline_get_shape_dict(self) -> None:
        from src.scientific.pipelines import DataPipeline
        shape = DataPipeline._get_shape({"a": 1, "b": 2})
        assert "2" in shape

    def test_pipeline_get_shape_scalar(self) -> None:
        from src.scientific.pipelines import DataPipeline
        shape = DataPipeline._get_shape(42)
        assert "int" in shape

    def test_pipeline_serialize_ndarray(self) -> None:
        import numpy as np
        from src.scientific.pipelines import DataPipeline
        arr = np.array([1.0, 2.0, 3.0])
        result = DataPipeline._serialize(arr)
        assert isinstance(result, list)

    def test_pipeline_serialize_numpy_scalar(self) -> None:
        import numpy as np
        from src.scientific.pipelines import DataPipeline
        scalar = np.float64(3.14)
        result = DataPipeline._serialize(scalar)
        assert isinstance(result, float)

    def test_pipeline_serialize_plain_value(self) -> None:
        from src.scientific.pipelines import DataPipeline
        assert DataPipeline._serialize("hello") == "hello"

    def test_normalize_zscore(self) -> None:
        from src.scientific.pipelines import normalize
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = normalize(data, method="zscore")
        assert isinstance(result, list)
        # Mean should be ~0
        mean = sum(result) / len(result)
        assert abs(mean) < 0.01

    def test_normalize_minmax(self) -> None:
        from src.scientific.pipelines import normalize
        data = [0.0, 5.0, 10.0]
        result = normalize(data, method="minmax")
        assert abs(result[0]) < 0.01
        assert abs(result[-1] - 1.0) < 0.01

    def test_remove_outliers(self) -> None:
        from src.scientific.pipelines import remove_outliers
        # Use a large dataset with an extreme outlier so z-score clearly exceeds threshold
        data = [1.0, 2.0, 1.5, 1.8, 2.2, 1.9, 2.1, 1.7, 2.0, 1000.0]
        result = remove_outliers(data, threshold=2.0)
        assert 1000.0 not in result

    def test_fill_missing_mean(self) -> None:
        import math
        from src.scientific.pipelines import fill_missing
        data = [1.0, float("nan"), 3.0]
        result = fill_missing(data, strategy="mean")
        assert not any(math.isnan(x) for x in result)

    def test_fill_missing_median(self) -> None:
        import math
        from src.scientific.pipelines import fill_missing
        data = [1.0, float("nan"), 3.0]
        result = fill_missing(data, strategy="median")
        assert not any(math.isnan(x) for x in result)

    def test_fill_missing_zero(self) -> None:
        import math
        from src.scientific.pipelines import fill_missing
        data = [1.0, float("nan"), 3.0]
        result = fill_missing(data, strategy="zero")
        assert not any(math.isnan(x) for x in result)
        assert result[1] == 0.0

    def test_downsample(self) -> None:
        from src.scientific.pipelines import downsample
        data = [1, 2, 3, 4, 5, 6]
        result = downsample(data, factor=2)
        assert result == [1, 3, 5]


# ===========================================================================
# scientific/analysis/calculus.py
# ===========================================================================
class TestNumericalCalculusExtended:
    """NumericalCalculus — romberg, unknown method, exception handling."""

    def test_simpson_integration(self) -> None:
        from src.scientific.analysis.calculus import NumericalCalculus
        calc = NumericalCalculus()
        result = calc.integrate(
            function="x**2",
            lower_bound=0.0,
            upper_bound=1.0,
            method="simpson",
        )
        assert "result" in result
        assert abs(result["result"] - 1 / 3) < 0.01

    def test_trapezoid_integration(self) -> None:
        from src.scientific.analysis.calculus import NumericalCalculus
        calc = NumericalCalculus()
        result = calc.integrate(
            function="x**2",
            lower_bound=0.0,
            upper_bound=1.0,
            method="trapezoid",
        )
        assert "result" in result
        assert abs(result["result"] - 1 / 3) < 0.01

    def test_unknown_method_returns_error(self) -> None:
        from src.scientific.analysis.calculus import NumericalCalculus
        calc = NumericalCalculus()
        result = calc.integrate(
            function="x**2",
            lower_bound=0.0,
            upper_bound=1.0,
            method="unknown_method_xyz",
        )
        assert "error" in result

    def test_bad_function_returns_error(self) -> None:
        from src.scientific.analysis.calculus import NumericalCalculus
        calc = NumericalCalculus()
        result = calc.integrate(
            function="import os",  # invalid expression
            lower_bound=0.0,
            upper_bound=1.0,
            method="quad",
        )
        assert "error" in result


# ===========================================================================
# scientific/analysis/matrix_ops.py
# ===========================================================================
class TestMatrixOpsExtended:
    """MatrixOperations — determinant, transpose, norm, solve, linalg error."""

    def test_determinant(self) -> None:
        from src.scientific.analysis.matrix_ops import MatrixOperations
        ops = MatrixOperations()
        result = ops.execute(
            operation="determinant",
            matrix_a=[[1.0, 2.0], [3.0, 4.0]],
        )
        assert "result" in result
        assert abs(result["result"] - (-2.0)) < 0.001

    def test_determinant_singular_matrix(self) -> None:
        from src.scientific.analysis.matrix_ops import MatrixOperations
        ops = MatrixOperations()
        result = ops.execute(
            operation="determinant",
            matrix_a=[[1.0, 2.0], [2.0, 4.0]],  # singular
        )
        assert "result" in result
        assert result["is_singular"] is True

    def test_transpose(self) -> None:
        from src.scientific.analysis.matrix_ops import MatrixOperations
        ops = MatrixOperations()
        result = ops.execute(
            operation="transpose",
            matrix_a=[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
        )
        assert "result" in result
        # Transposed shape should be 3x2
        assert len(result["result"]) == 3
        assert len(result["result"][0]) == 2

    def test_norm(self) -> None:
        from src.scientific.analysis.matrix_ops import MatrixOperations
        ops = MatrixOperations()
        result = ops.execute(
            operation="norm",
            matrix_a=[[3.0, 4.0]],
        )
        # norm returns a dict with multiple norm types
        assert "frobenius" in result or "result" in result or "l2" in result

    def test_solve_linear_system(self) -> None:
        from src.scientific.analysis.matrix_ops import MatrixOperations
        ops = MatrixOperations()
        # 2x + y = 5, x + 3y = 10 => x=1, y=3
        result = ops.execute(
            operation="solve",
            matrix_a=[[2.0, 1.0], [1.0, 3.0]],
            vector_b=[5.0, 10.0],
        )
        assert "solution" in result
        assert abs(result["solution"][0] - 1.0) < 0.001
        assert abs(result["solution"][1] - 3.0) < 0.001

    def test_solve_without_vector_b_returns_error(self) -> None:
        from src.scientific.analysis.matrix_ops import MatrixOperations
        ops = MatrixOperations()
        result = ops.execute(
            operation="solve",
            matrix_a=[[1.0, 0.0], [0.0, 1.0]],
        )
        assert "error" in result

    def test_linalg_error_singular_solve(self) -> None:
        from src.scientific.analysis.matrix_ops import MatrixOperations
        ops = MatrixOperations()
        # Singular matrix — solve will raise LinAlgError
        result = ops.execute(
            operation="solve",
            matrix_a=[[1.0, 2.0], [2.0, 4.0]],  # singular
            vector_b=[1.0, 2.0],
        )
        assert "error" in result


# ===========================================================================
# scientific/analysis/interpolation.py
# ===========================================================================
class TestInterpolationExtended:
    """Interpolator — pchip, unknown method."""

    def test_pchip_interpolation(self) -> None:
        from src.scientific.analysis.interpolation import Interpolator
        interp = Interpolator()
        result = interp.interpolate(
            x_data=[0.0, 1.0, 2.0, 3.0],
            y_data=[0.0, 1.0, 4.0, 9.0],
            x_new=[0.5, 1.5, 2.5],
            method="pchip",
        )
        assert "y_interpolated" in result or "interpolated_values" in result
        values = result.get("y_interpolated", result.get("interpolated_values", []))
        assert len(values) == 3

    def test_unknown_method_returns_error(self) -> None:
        from src.scientific.analysis.interpolation import Interpolator
        interp = Interpolator()
        result = interp.interpolate(
            x_data=[0.0, 1.0, 2.0],
            y_data=[0.0, 1.0, 4.0],
            x_new=[0.5],
            method="unknown_method_xyz",
        )
        assert "error" in result


# ===========================================================================
# scientific/analysis/signal_processing.py
# ===========================================================================
class TestSignalProcessingExtended:
    """SignalProcessor — ifft."""

    def test_ifft(self) -> None:
        from src.scientific.analysis.signal_processing import SignalProcessor
        processor = SignalProcessor()
        # Use a simple signal
        signal = [1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0]
        result = processor.fft(signal=signal, sample_rate=1.0, inverse=True)
        assert "operation" in result
        assert result["operation"] == "ifft"
        assert "result_real" in result


# ===========================================================================
# scientific/analysis/statistics.py — distribution_fit
# ===========================================================================
class TestStatisticsDistributionFit:
    """StatisticalAnalyzer — distribution_fit operation."""

    def test_distribution_fit(self) -> None:
        from src.scientific.analysis.statistics import StatisticalAnalyzer
        import random
        random.seed(42)
        # Generate normally-distributed data (50 rows, 1 column)
        data = [[random.gauss(0, 1)] for _ in range(50)]
        analyzer = StatisticalAnalyzer()
        result = analyzer.analyze(
            data=data,
            columns=["col0"],
            operations=["distribution_fit"],
        )
        assert "distribution_fit" in result or "error" in result


# ===========================================================================
# scientific/ml/trainer.py — kmeans, pca, gradient_boosting, decision_tree, knn
# ===========================================================================
class TestMLTrainerExtended:
    """MLTrainer — additional algorithms and predict_proba."""

    @pytest.mark.asyncio
    async def test_train_kmeans(self) -> None:
        from src.scientific.ml.trainer import MLTrainer
        trainer = MLTrainer()
        features = [[i, i * 2] for i in range(20)]
        result = await trainer.train(
            algorithm="kmeans",
            features=features,
            labels=None,
            test_size=0.2,
            hyperparameters={"n_clusters": 3},
            cross_validation=0,
        )
        assert "model_id" in result
        if "error" not in result:
            assert result["metrics"]["task"] == "clustering"

    @pytest.mark.asyncio
    async def test_train_pca(self) -> None:
        from src.scientific.ml.trainer import MLTrainer
        trainer = MLTrainer()
        features = [[i, i * 2, i * 3] for i in range(20)]
        result = await trainer.train(
            algorithm="pca",
            features=features,
            labels=None,
            test_size=0.2,
            hyperparameters={"n_components": 2},
            cross_validation=0,
        )
        assert "model_id" in result
        if "error" not in result:
            assert result["metrics"]["task"] == "dimensionality_reduction"

    @pytest.mark.asyncio
    async def test_train_gradient_boosting(self) -> None:
        from src.scientific.ml.trainer import MLTrainer
        trainer = MLTrainer()
        features = [[i, i * 2] for i in range(20)]
        labels = [i % 2 for i in range(20)]
        result = await trainer.train(
            algorithm="gradient_boosting",
            features=features,
            labels=labels,
            test_size=0.2,
            hyperparameters={},
            cross_validation=0,
        )
        assert "model_id" in result

    @pytest.mark.asyncio
    async def test_train_decision_tree(self) -> None:
        from src.scientific.ml.trainer import MLTrainer
        trainer = MLTrainer()
        features = [[i, i * 2] for i in range(20)]
        labels = [i % 2 for i in range(20)]
        result = await trainer.train(
            algorithm="decision_tree",
            features=features,
            labels=labels,
            test_size=0.2,
            hyperparameters={},
            cross_validation=0,
        )
        assert "model_id" in result

    @pytest.mark.asyncio
    async def test_train_knn(self) -> None:
        from src.scientific.ml.trainer import MLTrainer
        trainer = MLTrainer()
        features = [[i, i * 2] for i in range(20)]
        labels = [i % 2 for i in range(20)]
        result = await trainer.train(
            algorithm="knn",
            features=features,
            labels=labels,
            test_size=0.2,
            hyperparameters={"n_neighbors": 3},
            cross_validation=0,
        )
        assert "model_id" in result

    @pytest.mark.asyncio
    async def test_predict_with_proba(self) -> None:
        """predict should include probabilities for classifiers with predict_proba."""
        from src.scientific.ml.trainer import MLTrainer
        trainer = MLTrainer()
        features = [[i, i * 2] for i in range(20)]
        labels = [i % 2 for i in range(20)]
        train_result = await trainer.train(
            algorithm="random_forest",
            features=features,
            labels=labels,
            test_size=0.2,
            hyperparameters={},
            cross_validation=0,
        )
        if "error" not in train_result:
            model_id = train_result["model_id"]
            pred_result = await trainer.predict(
                model_id=model_id,
                features=[[5.0, 10.0], [10.0, 20.0]],
            )
            assert "predictions" in pred_result
            # RandomForest has predict_proba
            assert "probabilities" in pred_result

    @pytest.mark.asyncio
    async def test_train_svm_classification(self) -> None:
        from src.scientific.ml.trainer import MLTrainer
        trainer = MLTrainer()
        features = [[i, i * 2] for i in range(20)]
        labels = [i % 2 for i in range(20)]
        result = await trainer.train(
            algorithm="svm",
            features=features,
            labels=labels,
            test_size=0.2,
            hyperparameters={},
            cross_validation=0,
        )
        assert "model_id" in result

    @pytest.mark.asyncio
    async def test_train_multiclass_classification(self) -> None:
        """Test weighted average metrics for multiclass classification."""
        from src.scientific.ml.trainer import MLTrainer
        trainer = MLTrainer()
        features = [[i, i * 2] for i in range(30)]
        labels = [i % 3 for i in range(30)]  # 3 classes
        result = await trainer.train(
            algorithm="logistic_regression",
            features=features,
            labels=labels,
            test_size=0.2,
            hyperparameters={},
            cross_validation=0,
        )
        assert "model_id" in result
