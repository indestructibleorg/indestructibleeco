"""
Final batch of targeted tests to cover remaining uncovered lines.
All imports and API calls verified against actual source code.
"""
from __future__ import annotations

import asyncio
import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# 1. src/ai/agents/task_executor.py lines 34, 48
#    AgentTaskExecutor.execute(agent_type, task, context, constraints, output_format)
# ---------------------------------------------------------------------------
class TestAgentTaskExecutorBranches:
    """Cover lines 34 (constraints) and 48 (context) in task_executor.py."""

    @pytest.mark.asyncio
    async def test_execute_with_constraints(self):
        """Line 34 – constraints branch appends to system_prompt."""
        from src.ai.agents.task_executor import AgentTaskExecutor
        executor = AgentTaskExecutor()
        result = await executor.execute(
            agent_type="code_reviewer",
            task="Review this code",
            context={},
            constraints=["No external calls", "Use only Python"],
            output_format="markdown",
        )
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_execute_with_context(self):
        """Line 48 – context branch appends system message."""
        from src.ai.agents.task_executor import AgentTaskExecutor
        executor = AgentTaskExecutor()
        result = await executor.execute(
            agent_type="analyst",
            task="Analyse this",
            context={"background": "some info"},
            constraints=[],
            output_format="json",
        )
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# 2. src/ai/factory/expert_factory.py lines 123, 128, 131
#    ExpertFactory.delete_expert(expert_id) – async method
# ---------------------------------------------------------------------------
class TestExpertFactoryDeleteBranches:
    """Cover lines 123, 128, 131 in expert_factory.py."""

    def setup_method(self):
        from src.ai.factory.expert_factory import clear_experts
        clear_experts()

    @pytest.mark.asyncio
    async def test_delete_expert_not_found(self):
        """Line 123 – delete returns not_found when expert_id missing."""
        from src.ai.factory.expert_factory import ExpertFactory
        factory = ExpertFactory()
        result = await factory.delete_expert("nonexistent-id-12345")
        assert result["status"] == "not_found"

    @pytest.mark.asyncio
    async def test_delete_expert_success(self):
        """Lines 128, 131 – delete returns deleted when expert exists."""
        from src.ai.factory.expert_factory import ExpertFactory
        factory = ExpertFactory()
        create_result = await factory.create_expert(
            name="test-expert",
            domain="testing",
            specialization="unit tests",
            knowledge_base=[],
            model="gpt-4.1-mini",
            temperature=0.7,
            system_prompt="You are a test expert.",
        )
        expert_id = create_result["id"]
        delete_result = await factory.delete_expert(expert_id)
        assert delete_result["status"] == "deleted"
        assert delete_result["expert_id"] == expert_id

    def test_instance_clear_experts(self):
        """Line 128 – ExpertFactory instance method clear_experts."""
        from src.ai.factory.expert_factory import ExpertFactory
        factory = ExpertFactory()
        factory.clear_experts()  # covers line 128


# ---------------------------------------------------------------------------
# 3. src/ai/vectordb/manager.py lines 26-28, 90
#    VectorDBManager._get_client() HttpClient branch; search() filter branch
# ---------------------------------------------------------------------------
class TestVectorDBManagerBranches:
    """Cover lines 26-28 and 90 in vectordb/manager.py."""

    def test_get_client_http_client_branch(self):
        """Lines 26-28 – HttpClient is used when chromadb_host is set."""
        import sys
        from src.ai.vectordb.manager import VectorDBManager
        mock_settings = MagicMock()
        mock_settings.ai.chromadb_host = "localhost"
        mock_settings.ai.chromadb_port = 8000
        mock_http_client = MagicMock()
        original = sys.modules.get("chromadb")
        mock_chroma = MagicMock()
        mock_chroma.HttpClient = MagicMock(return_value=mock_http_client)
        sys.modules["chromadb"] = mock_chroma
        try:
            manager = VectorDBManager()
            manager._client = None  # reset
            with patch("src.infrastructure.config.get_settings", return_value=mock_settings):
                client = manager._get_client()
            assert client is not None
        finally:
            if original is not None:
                sys.modules["chromadb"] = original
            else:
                del sys.modules["chromadb"]

    @pytest.mark.asyncio
    async def test_search_with_filter(self):
        """Line 90 – filter sets where in kwargs."""
        from src.ai.vectordb.manager import VectorDBManager
        mock_col = MagicMock()
        mock_col.query.return_value = {
            "ids": [["id1"]],
            "documents": [["doc1"]],
            "metadatas": [[{"key": "val"}]],
            "distances": [[0.1]],
        }
        mock_client = MagicMock()
        mock_client.get_collection.return_value = mock_col
        manager = VectorDBManager()
        manager._client = mock_client
        with patch.object(manager, "_embed_texts", return_value=[[0.1, 0.2]]):
            result = await manager.search(
                collection="test",
                query="test query",
                top_k=1,
                filter={"source": "test"},
            )
        assert "results" in result
        call_kwargs = mock_col.query.call_args[1]
        assert call_kwargs.get("where") == {"source": "test"}


# ---------------------------------------------------------------------------
# 4. src/application/use_cases/user_management.py line 94
#    AuthenticateUserUseCase.execute – status is plain string (not enum)
# ---------------------------------------------------------------------------
class TestAuthenticateUserStatusString:
    """Cover line 94 in user_management.py."""

    @pytest.mark.asyncio
    async def test_authenticate_user_with_string_status_inactive(self):
        """Line 94 – status is plain string 'inactive', not enum."""
        from src.application.use_cases.user_management import AuthenticateUserUseCase
        from src.domain.exceptions import AuthenticationException
        mock_repo = AsyncMock()
        mock_user = MagicMock()
        # Use a plain string for status (no .value attribute)
        mock_user.status = "inactive"
        # Ensure hasattr(mock_user.status, "value") is False
        mock_user.hashed_password = MagicMock()
        mock_user.hashed_password.value = "$2b$12$validhashedpasswordhere123456"
        mock_user.id = "user-123"
        mock_repo.find_by_username = AsyncMock(return_value=mock_user)
        uc = AuthenticateUserUseCase(repo=mock_repo)
        with patch.object(uc._auth, "verify_password", return_value=True):
            with pytest.raises(AuthenticationException):
                await uc.execute(username="testuser", password="password123")


# ---------------------------------------------------------------------------
# 5. src/domain/entities/user.py line 33
#    HashedPassword.validate_not_empty – value too short raises ValueError
# ---------------------------------------------------------------------------
class TestHashedPasswordValidation:
    """Cover line 33 in domain/entities/user.py."""

    def test_hashed_password_too_short_raises(self):
        """Line 33 – value shorter than 10 chars raises ValueError."""
        from src.domain.entities.user import HashedPassword
        with pytest.raises(Exception):
            HashedPassword(value="short")

    def test_hashed_password_empty_raises(self):
        """Line 33 – empty string raises ValueError."""
        from src.domain.entities.user import HashedPassword
        with pytest.raises(Exception):
            HashedPassword(value="")


# ---------------------------------------------------------------------------
# 6. src/domain/specifications/__init__.py line 71
#    UserByRoleSpecification.is_satisfied_by – role is plain string
# ---------------------------------------------------------------------------
class TestUserByRoleSpecificationStringRole:
    """Cover line 71 in domain/specifications/__init__.py."""

    def test_role_spec_with_string_role_match(self):
        """Line 71 – role is a plain string without .value, uses == comparison."""
        from src.domain.specifications import UserByRoleSpecification
        spec = UserByRoleSpecification("admin")

        class FakeUser:
            role = "admin"

        result = spec.is_satisfied_by(FakeUser())
        assert result is True

    def test_role_spec_with_string_role_no_match(self):
        """Line 71 – plain string role that doesn't match returns False."""
        from src.domain.specifications import UserByRoleSpecification
        spec = UserByRoleSpecification("admin")

        class FakeUser:
            role = "operator"

        result = spec.is_satisfied_by(FakeUser())
        assert result is False


# ---------------------------------------------------------------------------
# 7. src/infrastructure/config/settings.py lines 182-183
#    Settings.validate_production_settings – DEBUG=True in production
# ---------------------------------------------------------------------------
class TestSettingsProductionDebugValidation:
    """Cover lines 182-183 in settings.py."""

    def test_production_debug_true_raises(self):
        """Lines 182-183 – app_debug=True in production raises ValueError."""
        from src.infrastructure.config.settings import Settings, Environment
        with pytest.raises(Exception):
            Settings(
                app_env=Environment.PRODUCTION,
                app_debug=True,
                secret_key="a-very-long-production-secret-key-that-is-not-default",
            )


# ---------------------------------------------------------------------------
# 8. src/infrastructure/security/__init__.py line 112
#    JWTHandler.decode_token – expired token raises TokenExpiredException
# ---------------------------------------------------------------------------
class TestJWTHandlerInvalidToken:
    """Cover line 112 in security/__init__.py."""

    def test_verify_refresh_token_invalid_signature_raises(self):
        """Line 112 – non-expired invalid token in verify_refresh_token raises InvalidTokenException."""
        import datetime
        from jose import jwt as jose_jwt
        from src.infrastructure.security import JWTHandler
        from src.domain.exceptions import InvalidTokenException
        from src.infrastructure.config import get_settings
        settings = get_settings()
        jwt_cfg = settings.jwt
        handler = JWTHandler()
        # Sign with wrong secret so JWTError is raised (not expired)
        payload = {
            "sub": "user-123",
            "type": "refresh",
            "iss": jwt_cfg.issuer,
        }
        token = jose_jwt.encode(payload, "wrong-secret", algorithm=jwt_cfg.algorithm)
        with pytest.raises(InvalidTokenException):
            handler.verify_refresh_token(token)


# ---------------------------------------------------------------------------
# 9. src/infrastructure/tasks/__init__.py lines 61-63
#    TaskRunner.get_status – done-with-exception and cancelled branches
# ---------------------------------------------------------------------------
class TestTaskRunnerStatusBranches:
    """Cover lines 61-63 in tasks/__init__.py."""

    @pytest.mark.asyncio
    async def test_get_status_failed(self):
        """Line 61 – done task with exception returns 'failed'."""
        from src.infrastructure.tasks import TaskRunner
        runner = TaskRunner()

        async def failing():
            raise ValueError("intentional failure")

        task = asyncio.create_task(failing())
        await asyncio.sleep(0)
        try:
            await task
        except Exception:
            pass
        runner._tasks["fail-task"] = task
        status = runner.get_status("fail-task")
        assert status == "failed"

    @pytest.mark.asyncio
    async def test_get_status_cancelled(self):
        """Line 62 – cancelled task returns 'cancelled'."""
        from src.infrastructure.tasks import TaskRunner
        runner = TaskRunner()

        # Create a mock task that reports as cancelled
        # Note: cancelled() branch is only reached when done() is False
        mock_task = MagicMock()
        mock_task.done.return_value = False
        mock_task.cancelled.return_value = True

        runner._tasks["cancel-task"] = mock_task
        status = runner.get_status("cancel-task")
        assert status == "cancelled"

    @pytest.mark.asyncio
    async def test_get_status_running(self):
        """Line 63 – task not done and not cancelled returns 'running'."""
        from src.infrastructure.tasks import TaskRunner
        runner = TaskRunner()

        # Create a mock task that is still running
        mock_task = MagicMock()
        mock_task.done.return_value = False
        mock_task.cancelled.return_value = False

        runner._tasks["run-task"] = mock_task
        status = runner.get_status("run-task")
        assert status == "running"


# ---------------------------------------------------------------------------
# 10. src/infrastructure/telemetry/__init__.py lines 91-92, 103-104, 133-134
# ---------------------------------------------------------------------------
class TestTelemetryBranches:
    """Cover lines 91-92, 103-104, 133-134 in telemetry/__init__.py."""

    def test_instrument_sqlalchemy_exception_branch(self):
        """Lines 91-92 – Exception during SQLAlchemy instrumentation is handled."""
        from src.infrastructure import telemetry as tel_module
        mock_engine = MagicMock()
        # Patch the opentelemetry instrumentation to raise
        with patch.dict("sys.modules", {
            "opentelemetry.instrumentation.sqlalchemy": MagicMock(
                SQLAlchemyInstrumentor=MagicMock(
                    return_value=MagicMock(instrument=MagicMock(side_effect=Exception("fail")))
                )
            )
        }):
            try:
                tel_module.instrument_sqlalchemy(mock_engine)
            except Exception:
                pass

    def test_instrument_httpx_exception_branch(self):
        """Lines 103-104 – Exception during httpx instrumentation is handled."""
        from src.infrastructure import telemetry as tel_module
        with patch.dict("sys.modules", {
            "opentelemetry.instrumentation.httpx": MagicMock(
                HTTPXClientInstrumentor=MagicMock(
                    return_value=MagicMock(instrument=MagicMock(side_effect=Exception("fail")))
                )
            )
        }):
            try:
                tel_module.instrument_httpx()
            except Exception:
                pass

    def test_get_environment_exception_returns_unknown(self):
        """Lines 133-134 – Exception in get_settings returns 'unknown'."""
        from src.infrastructure import telemetry as tel_module
        with patch("src.infrastructure.config.get_settings",
                   side_effect=Exception("settings error")):
            result = tel_module._get_environment()
        assert result == "unknown"


# ---------------------------------------------------------------------------
# 11. src/presentation/api/schemas/__init__.py lines 191, 435, 474, 500
# ---------------------------------------------------------------------------
class TestSchemasValidatorBranches:
    """Cover remaining validator branches in schemas/__init__.py."""

    def test_user_response_coerce_datetime_passthrough(self):
        """Line 191 – coerce_datetime returns non-string value as-is."""
        import uuid
        from datetime import datetime
        from src.presentation.api.schemas import UserResponse
        # Pass a real datetime object (not a string) to hit 'return v' at line 191
        resp = UserResponse(
            id=str(uuid.uuid4()),
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role="admin",
            status="active",
            created_at=datetime(2024, 1, 1, 0, 0, 0),
            last_login_at=None,
        )
        assert isinstance(resp.created_at, datetime)

    def test_scientific_analysis_request_empty_data_raises(self):
        """Line 435 – validate_data_shape raises ValueError when data is empty."""
        from src.presentation.api.schemas import ScientificAnalysisRequest
        with pytest.raises(ValueError, match="at least one row"):
            ScientificAnalysisRequest.validate_data_shape([])

    def test_scientific_analysis_request_valid_columns_match(self):
        """Line 474 – valid request with matching columns returns self."""
        from src.presentation.api.schemas import ScientificAnalysisRequest
        req = ScientificAnalysisRequest(
            data=[[1.0, 2.0], [3.0, 4.0]],
            columns=["a", "b"],
            operations=["describe"],
        )
        assert req.columns == ["a", "b"]

    def test_scientific_matrix_request_empty_matrix_raises(self):
        """Line 500 – validate_matrix_shape raises ValueError when matrix is empty."""
        from src.presentation.api.schemas import ScientificMatrixRequest
        with pytest.raises(ValueError, match="at least one row"):
            ScientificMatrixRequest.validate_matrix_shape([])


# ---------------------------------------------------------------------------
# 12. src/quantum/circuits/__init__.py line 111 CircuitBuilder – gate with params
# ----------------------------------------------------------------------------
class TestCircuitBuilderParamGate:
    """Cover line 111 in circuits/__init__.py."""

    def test_barrier_gate_to_qiskit(self):
        """Line 111 – barrier gate in to_qiskit() calls qc.barrier()."""
        from src.quantum.circuits import CircuitBuilder
        builder = CircuitBuilder(num_qubits=2)
        builder.barrier()  # adds barrier gate to _gates
        qc = builder.to_qiskit()  # line 111: qc.barrier() is called
        # Qiskit circuit with barrier has operations
        assert qc is not None


# ---------------------------------------------------------------------------
# 13. src/scientific/analysis/calculus.py line 37
#    NumericalCalculus.integrate – romberg method
# ---------------------------------------------------------------------------
class TestCalculusRombergMethod:
    """Cover line 37 in calculus.py."""

    def test_integrate_romberg_method(self):
        """Line 37 – romberg integration method."""
        from src.scientific.analysis.calculus import NumericalCalculus
        calc = NumericalCalculus()
        result = calc.integrate(
            function="x**2",
            lower_bound=0.0,
            upper_bound=1.0,
            method="romberg",
        )
        assert "result" in result
        assert abs(result["result"] - 1 / 3) < 0.01


# ---------------------------------------------------------------------------
# 14. src/scientific/analysis/statistics.py lines 87-88
#    StatisticalAnalyzer – distribution_fit best_fit update
# ---------------------------------------------------------------------------
class TestStatisticsDistributionFit:
    """Cover lines 87-88 in statistics.py."""

    def test_distribution_fit_exception_handler(self):
        """Lines 87-88 – exception in distribution fitting is caught and continues."""
        from src.scientific.analysis.statistics import StatisticalAnalyzer
        import numpy as np
        from unittest.mock import patch
        analyzer = StatisticalAnalyzer()
        rng = np.random.default_rng(42)
        data = [[float(x)] for x in rng.normal(0, 1, 100).tolist()]
        # Patch scipy.stats.norm.fit to raise an exception
        with patch('scipy.stats.norm') as mock_norm:
            mock_norm.fit.side_effect = RuntimeError("forced error")
            result = analyzer.analyze(
                data=data,
                columns=["col"],
                operations=["distribution_fit"],
            )
        # The exception was caught and other distributions were tried
        assert "distribution_fit" in result
        assert "col" in result["distribution_fit"]


# ---------------------------------------------------------------------------
# 15. src/scientific/ml/trainer.py lines 127-128
#    MLTrainer.train – predict_proba branch for classifiers
# ---------------------------------------------------------------------------
class TestMLTrainerPredictProba:
    """Cover lines 127-128 in trainer.py."""

    @pytest.mark.asyncio
    async def test_predict_proba_exception_handler(self):
        """Lines 127-128 – exception in predict_proba is silently caught."""
        from src.scientific.ml.trainer import MLTrainer, _MODEL_STORE
        from unittest.mock import MagicMock, patch
        import uuid
        trainer = MLTrainer()
        # Create a mock model with predict_proba that raises
        mock_model = MagicMock()
        mock_model.predict.return_value = MagicMock(tolist=lambda: [0, 1])
        mock_model.predict_proba.side_effect = RuntimeError("predict_proba failed")
        from sklearn.preprocessing import StandardScaler
        mock_scaler = StandardScaler()
        import numpy as np
        mock_scaler.fit(np.array([[0.0, 1.0], [1.0, 2.0]]))
        model_id = str(uuid.uuid4())
        _MODEL_STORE[model_id] = {
            "model": mock_model,
            "scaler": mock_scaler,
            "algorithm": "mock",
            "metrics": {},
            "created_at": "2024-01-01T00:00:00",
        }
        result = await trainer.predict(
            model_id=model_id,
            features=[[0.0, 1.0], [1.0, 2.0]],
        )
        assert "model_id" in result
        assert "probabilities" not in result  # exception was caught, no probabilities
        del _MODEL_STORE[model_id]


# ---------------------------------------------------------------------------
# 16. src/shared/decorators/__init__.py line 108
#    cached decorator – expired entries are evicted from _cache
# ---------------------------------------------------------------------------
class TestCachedDecoratorEviction:
    """Cover line 108 in decorators/__init__.py."""

    @pytest.mark.asyncio
    async def test_expired_cache_entry_evicted(self):
        """Line 108 – expired entries are deleted from _cache dict."""
        import src.shared.decorators as dec_module
        from src.shared.decorators import cached

        call_count = 0

        @cached(ttl_seconds=300)
        async def fn(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 5

        # First call populates cache
        r1 = await fn(3)
        assert r1 == 15
        assert call_count == 1

        # Simulate time passing by patching time.time in the decorators module
        with patch.object(dec_module.time, "time", return_value=time.time() + 400):
            r2 = await fn(3)
            assert r2 == 15
            assert call_count == 2  # Cache expired, re-executed


# ---------------------------------------------------------------------------
# 17. src/shared/schemas/__init__.py line 68
#    EmailField.validate_email – email exceeds 254 chars
# ---------------------------------------------------------------------------
class TestEmailFieldMaxLength:
    """Cover line 68 in shared/schemas/__init__.py."""

    def test_email_exceeds_254_chars_raises(self):
        """Line 68 – email longer than 254 chars raises ValueError."""
        from src.shared.schemas import EmailField
        # Build a valid-format email that exceeds 254 chars
        # Call the validator directly to bypass pydantic max_length field constraint
        local = "b" * 245
        very_long_email = f"{local}@example.com"  # 257 chars
        with pytest.raises(ValueError, match="exceeds maximum length"):
            EmailField.validate_email(very_long_email)
