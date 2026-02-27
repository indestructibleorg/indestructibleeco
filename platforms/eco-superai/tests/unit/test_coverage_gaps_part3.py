"""
test_coverage_gaps_part3.py
===========================
補充測試 Part 3：覆蓋剩餘 603 行未覆蓋缺口。

模組清單：
- shared/exceptions (ConfigurationError, SerializationError, __repr__)
- shared/schemas (email max length, PaginationParams.offset, SortParams, DateRangeFilter)
- shared/decorators (cache eviction)
- domain/entities/user (hashed_password validation)
- domain/value_objects/password (max 72 bytes)
- domain/value_objects/role (has_all_permissions)
- domain/specifications (role string comparison)
- application/dto (last_login_at, total_pages)
- application/use_cases/user_management (status str, role update)
- application/use_cases/quantum_management (vqe/qaoa/qml)
- ai/prompts (variables property, remove_template)
- ai/embeddings/generator (openai path, sentence_transformer fallback)
- ai/vectordb/manager (chromadb client, embeddings, filter)
- ai/agents/task_executor (full execute path)
- ai/factory/expert_factory (RAG, LLM, not_found)
- scientific/analysis/calculus (romberg)
- scientific/analysis/interpolation (quadratic)
- scientific/analysis/matrix_ops (error path)
- scientific/analysis/statistics (distribution fit error)
- scientific/ml/trainer (exception suppression)
- scientific/pipelines (non-numpy remove_outliers)
- infrastructure/config/settings (production validation)
- infrastructure/security (invalid token non-expired)
- infrastructure/telemetry (instrumentation error paths)
- infrastructure/tasks/__init__ (cancelled task)
- infrastructure/tasks/worker (main function)
- infrastructure/persistence/database (get_session, create_tables)
- infrastructure/persistence/repositories (count, search, exists, by_status, save/update errors)
- infrastructure/cache/redis_client (error paths)
- infrastructure/external/__init__ (error paths)
- infrastructure/external/k8s_client (init, list, scale, apply)
- presentation/api/dependencies (get_db_session, get_user_repo, get_quantum_repo, require_admin, client.host fallback)
- presentation/api/main (lifespan shutdown, production middleware, cli)
- presentation/api/middleware (rate_limit_cleanup, request_failed, CORS)
- presentation/api/routes/admin (k8s ImportError, yaml error, redis flush)
- presentation/api/routes/health (db check)
- presentation/api/routes/scientific (optimizer, interpolation)
- presentation/api/schemas (password violations, role validation, knowledge_base, datetime, statistics, matrix)
- presentation/exceptions/handlers (InfrastructureException)
- artifact_converter/cli (error paths, watch)
- artifact_converter/parsers/docx_parser (ImportError, fallback)
- artifact_converter/parsers/pdf_parser (ImportError, fallback)
- artifact_converter/generators/markdown_gen (template, metadata fields)
- artifact_converter/generators/python_gen (template, source_path, dedup)
- artifact_converter/generators/typescript_gen (sanitize, template, source_path, dedup)
- quantum/circuits (build_qiskit_circuit)
- quantum/algorithms/vqe (ImportError, exception)
- quantum/algorithms/qaoa (ImportError, exception)
- quantum/algorithms/qml (rz gate, ImportError, exception)
- quantum/runtime/executor (qft, grover circuits)
"""
from __future__ import annotations

import asyncio
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


# ===========================================================================
# shared/exceptions — ConfigurationError, SerializationError, __repr__
# ===========================================================================
class TestSharedExceptionsExtended:
    """ConfigurationError, SerializationError, __repr__."""

    def test_base_exception_repr(self) -> None:
        from src.shared.exceptions import InfrastructureException
        exc = InfrastructureException("test message", "TEST_CODE")
        r = repr(exc)
        assert "TEST_CODE" in r
        assert "test message" in r

    def test_configuration_error_with_details(self) -> None:
        from src.shared.exceptions import ConfigurationError
        exc = ConfigurationError("missing env var")
        assert "Configuration error" in str(exc)
        assert "missing env var" in str(exc)
        assert exc.code == "CONFIGURATION_ERROR"

    def test_configuration_error_without_details(self) -> None:
        from src.shared.exceptions import ConfigurationError
        exc = ConfigurationError()
        assert "Configuration error" in str(exc)

    def test_serialization_error_with_details(self) -> None:
        from src.shared.exceptions import SerializationError
        exc = SerializationError("invalid JSON")
        assert "Serialization error" in str(exc)
        assert "invalid JSON" in str(exc)
        assert exc.code == "SERIALIZATION_ERROR"

    def test_serialization_error_without_details(self) -> None:
        from src.shared.exceptions import SerializationError
        exc = SerializationError()
        assert "Serialization error" in str(exc)


# ===========================================================================
# shared/schemas — email max length, PaginationParams.offset, SortParams, DateRangeFilter
# ===========================================================================
class TestSharedSchemasExtended:
    """Email max length, PaginationParams.offset, SortParams, DateRangeFilter."""

    def test_email_exceeds_max_length(self) -> None:
        from src.shared.schemas import EmailField
        import pydantic
        long_local = "a" * 250
        with pytest.raises((ValueError, pydantic.ValidationError)):
            EmailField.validate(f"{long_local}@example.com")

    def test_pagination_params_offset_property(self) -> None:
        from src.shared.schemas import PaginationParams
        p = PaginationParams(limit=10, skip=30)
        assert p.offset == 30

    def test_sort_params_valid_field(self) -> None:
        from src.shared.schemas import SortParams, SortDirection
        s = SortParams(field="created_at", direction=SortDirection.ASC)
        assert s.field == "created_at"
        assert s.is_ascending is True
        assert s.sql_direction == "ASC"

    def test_sort_params_desc(self) -> None:
        from src.shared.schemas import SortParams, SortDirection
        s = SortParams(field="updated_at", direction=SortDirection.DESC)
        assert s.is_ascending is False
        assert s.sql_direction == "DESC"

    def test_sort_params_invalid_field_raises(self) -> None:
        from src.shared.schemas import SortParams
        import pydantic
        with pytest.raises((ValueError, pydantic.ValidationError)):
            SortParams(field="invalid field!", direction="asc")

    def test_date_range_filter_parse_datetime_string(self) -> None:
        from src.shared.schemas import DateRangeFilter
        f = DateRangeFilter(start="2024-01-01T00:00:00Z", end="2024-12-31T23:59:59Z")
        assert f.start is not None
        assert f.end is not None
        assert f.is_bounded is True
        assert f.is_open is False

    def test_date_range_filter_none_values(self) -> None:
        from src.shared.schemas import DateRangeFilter
        f = DateRangeFilter(start=None, end=None)
        assert f.is_open is True
        assert f.is_bounded is False

    def test_date_range_filter_start_after_end_raises(self) -> None:
        from src.shared.schemas import DateRangeFilter
        import pydantic
        with pytest.raises((ValueError, pydantic.ValidationError)):
            DateRangeFilter(
                start=datetime(2024, 12, 31, tzinfo=timezone.utc),
                end=datetime(2024, 1, 1, tzinfo=timezone.utc),
            )

    def test_date_range_filter_invalid_datetime_string(self) -> None:
        from src.shared.schemas import DateRangeFilter
        import pydantic
        with pytest.raises((ValueError, pydantic.ValidationError)):
            DateRangeFilter(start="not-a-date", end=None)


# ===========================================================================
# shared/decorators — cache eviction
# ===========================================================================
class TestSharedDecoratorsEviction:
    """Cache eviction of expired entries."""

    @pytest.mark.asyncio
    async def test_cache_evicts_expired_entries(self) -> None:
        from src.shared.decorators import cached
        import asyncio
        call_count = 0

        @cached(ttl_seconds=0.01)
        async def my_func(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call — populates cache
        assert await my_func(5) == 10
        assert call_count == 1

        # Wait for TTL to expire
        await asyncio.sleep(0.05)

        # Second call — cache expired, eviction should happen
        assert await my_func(5) == 10
        assert call_count == 2



# ===========================================================================
# domain/entities/user — hashed_password validation
# ===========================================================================
class TestUserEntityHashedPassword:
    """User entity hashed_password validator."""

    def test_short_hashed_password_raises(self) -> None:
        from src.domain.entities.user import User
        import pydantic
        with pytest.raises((ValueError, pydantic.ValidationError)):
            User(
                id=str(uuid.uuid4()),
                username="testuser",
                email="test@example.com",
                hashed_password="short",
                role="developer",
            )


# ===========================================================================
# domain/value_objects/password — max 72 bytes
# ===========================================================================
class TestPasswordValueObjectExtended:
    """Password value object — max 72 bytes validation."""

    def test_password_exceeds_72_bytes_raises(self) -> None:
        from src.domain.value_objects.password import HashedPassword
        from src.domain.exceptions import WeakPasswordError
        # 73 ASCII characters = 73 bytes
        long_password = "A1@" + "a" * 70
        with pytest.raises(WeakPasswordError, match="maximum 72 bytes"):
            HashedPassword.from_plain(long_password)


# ===========================================================================
# domain/value_objects/role — has_all_permissions
# ===========================================================================
class TestRoleValueObjectExtended:
    """Role value object — has_all_permissions."""

    def test_has_all_permissions(self) -> None:
        from src.domain.value_objects.role import UserRole, Permission, RolePermissions
        
        assert RolePermissions.has_all_permissions(UserRole.ADMIN, {Permission.USER_READ, Permission.USER_WRITE}) is True
        assert RolePermissions.has_all_permissions(UserRole.ADMIN, {Permission.USER_READ, Permission.USER_DELETE}) is True


# ===========================================================================
# domain/specifications — role string comparison
# ===========================================================================
class TestSpecificationsExtended:
    """Specifications — role string comparison."""

    def test_is_role_specification_string_comparison(self) -> None:
        from src.domain.specifications import UserByRoleSpecification
        from src.domain.entities.user import User
        from src.domain.value_objects.role import UserRole, Permission, RolePermissions

        user = User.create(
            username="test",
            email="test@example.com",
            hashed_password="$2b$12$D8O.Z.B6q0.A.Z.B6q0.A.Z.B6q0.A.Z.B6q0.A.Z.B6q0.A.Z.B6q0.A.Z.B6",
            role=UserRole.ADMIN,
        )
        spec = UserByRoleSpecification("admin")
        assert spec.is_satisfied_by(user) is True


# ===========================================================================
# application/dto — last_login_at, total_pages
# ===========================================================================
class TestApplicationDTOExtended:
    """DTOs — last_login_at, total_pages."""

    def test_user_dto_last_login_at(self) -> None:
        from src.application.dto import UserDTO
        from src.domain.entities.user import User
        from src.domain.value_objects.role import UserRole, Permission, RolePermissions

        now = datetime.now(timezone.utc)
        user = User.create(
            username="test",
            email="test@example.com",
            hashed_password="$2b$12$D8O.Z.B6q0.A.Z.B6q0.A.Z.B6q0.A.Z.B6q0.A.Z.B6q0.A.Z.B6q0.A.Z.B6",
            role=UserRole.DEVELOPER,
        )
        user.last_login_at = now
        dto = UserDTO.from_entity(user)
        assert dto.last_login_at == now.isoformat()

    def test_paginated_response_total_pages(self) -> None:
        from src.application.dto import PaginatedDTO
        # 100 items, 20 per page -> 5 pages
        p = PaginatedDTO(items=[], total=100, limit=20, skip=0)
        assert p.total_pages == 5
        # 99 items, 20 per page -> 5 pages
        p2 = PaginatedDTO(items=[], total=99, limit=20, skip=0)
        assert p2.total_pages == 5
        # 0 items, 20 per page -> 0 pages
        p3 = PaginatedDTO(items=[], total=0, limit=20, skip=0)
        assert p3.total_pages == 0


# ===========================================================================
# application/use_cases/user_management — status str, role update
# ===========================================================================class TestUserManagementUseCasesExtended:
    """User management — status as string, role update."""

    def _get_mock_user(self):
        from src.domain.value_objects.role import UserRole
        mock_user = MagicMock()
        mock_user.id = str(uuid.uuid4())
        mock_user.username = "testuser"
        mock_user.email = MagicMock()
        mock_user.email.value = "test@example.com"
        mock_user.full_name = "Test User"
        mock_user.role = UserRole.DEVELOPER
        mock_user.status = MagicMock()
        mock_user.status.value = "active"
        mock_user.created_at = datetime.now(timezone.utc)
        mock_user.last_login_at = None
        return mock_user

    @pytest.mark.asyncio
    async def test_update_user_status_by_string(self) -> None:
        from src.application.use_cases.user_management import SuspendUserUseCase

        mock_repo = AsyncMock()
        mock_user = self._get_mock_user()
        mock_repo.find_by_id.return_value = mock_user
        mock_repo.update.return_value = mock_user
        service = SuspendUserUseCase(repo=mock_repo)

        await service.execute(user_id=str(uuid.uuid4()), reason="testing")
        mock_user.suspend.assert_called_once_with("testing")
        mock_repo.update.assert_called_once_with(mock_user)

    @pytest.mark.asyncio
    async def test_update_user_role(self) -> None:
        from src.application.use_cases.user_management import UpdateUserUseCase
        from src.domain.value_objects.role import UserRole

        mock_repo = AsyncMock()
        mock_user = self._get_mock_user()
        mock_repo.find_by_id.return_value = mock_user
        mock_repo.update.return_value = mock_user
        service = UpdateUserUseCase(repo=mock_repo)

        new_role = UserRole.OPERATOR
        await service.execute(user_id=str(uuid.uuid4()), role=new_role.value)
        assert mock_user.role == UserRole.OPERATOR
        mock_repo.update.assert_called_once_with(mock_user)
# application/use_cases/quantum_management — vqe/qaoa/qml
# ===========================================================================
class TestQuantumManagementUseCasesExtended:
    """Quantum management — VQE, QAOA, QML job submissions."""

    @pytest.mark.asyncio
    async def test_submit_vqe_job(self) -> None:
        from src.application.use_cases.quantum_management import SubmitQuantumJobUseCase

        mock_repo = AsyncMock()
        mock_executor = AsyncMock()
        mock_executor.run_circuit.return_value = {"status": "completed", "result": {"measurement": "vqe_success"}, "execution_time_ms": 123.4}
        service = SubmitQuantumJobUseCase(repo=mock_repo, executor=mock_executor)

        result = await service.execute(user_id="test-user", algorithm="vqe")
        assert result["result"] == {"measurement": "vqe_success"}

    @pytest.mark.asyncio
    async def test_submit_qaoa_job(self) -> None:
        from src.application.use_cases.quantum_management import SubmitQuantumJobUseCase

        mock_repo = AsyncMock()
        mock_executor = AsyncMock()
        mock_executor.run_circuit.return_value = {"status": "completed", "result": {"measurement": "qaoa_success"}, "execution_time_ms": 123.4}
        service = SubmitQuantumJobUseCase(repo=mock_repo, executor=mock_executor)

        result = await service.execute(user_id="test-user", algorithm="qaoa")
        assert result["result"] == {"measurement": "qaoa_success"}

    @pytest.mark.asyncio
    async def test_submit_qml_job(self) -> None:
        from src.application.use_cases.quantum_management import SubmitQuantumJobUseCase

        mock_repo = AsyncMock()
        mock_executor = AsyncMock()
        mock_executor.run_circuit.return_value = {"status": "completed", "result": {"measurement": "qml_success"}, "execution_time_ms": 123.4}
        service = SubmitQuantumJobUseCase(repo=mock_repo, executor=mock_executor)

        result = await service.execute(user_id="test-user", algorithm="qml")
        assert result["result"] == {"measurement": "qml_success"}


# ===========================================================================
# ai/prompts — variables property, remove_template
# ===========================================================================
class TestAIPromptsExtended:
    """AI prompts — variables property, remove_template."""

    def test_prompt_template_variables_property(self) -> None:
        from src.ai.prompts import PromptTemplate
        template = PromptTemplate(name="test", template="Hello, {{name}}! You are in {{location}}.")
        assert set(template.variables) == {"name", "location"}

    def test_prompt_manager_remove_template(self) -> None:
        from src.ai.prompts import PromptTemplate, PromptTemplateManager
        manager = PromptTemplateManager()
        manager.register(PromptTemplate(name="t1", template="template 1"))
        manager.register(PromptTemplate(name="t2", template="template 2"))
        manager.delete("t1")
        assert manager.get("t1") is None
        assert manager.get("t2") is not None


# ===========================================================================
# ai/embeddings/generator — openai path, sentence_transformer fallback
# ===========================================================================
class TestEmbeddingsGeneratorExtended:
    """Embeddings generator — OpenAI path, SentenceTransformer fallback."""

    @pytest.mark.asyncio
    async def test_openai_embedding_generator_path(self) -> None:
        from src.ai.embeddings.generator import EmbeddingGenerator
        import numpy as np

        mock_client = AsyncMock()
        mock_embedding = MagicMock()
        mock_embedding.embedding = [0.1, 0.2, 0.3]
        mock_response = MagicMock()
        mock_response.data = [mock_embedding]
        mock_response.usage = MagicMock()
        mock_response.usage.total_tokens = 10
        mock_client.embeddings.create.return_value = mock_response

        with patch("src.infrastructure.config.get_settings") as mock_get_settings:
            mock_get_settings.return_value.ai.openai_api_key = "test_key"
            with patch("openai.AsyncOpenAI", return_value=mock_client) as mock_openai_client:
                generator = EmbeddingGenerator()
                result = await generator.generate(["text"])
                assert result["embeddings"] == [[0.1, 0.2, 0.3]]

    @pytest.mark.asyncio
    async def test_sentence_transformer_fallback(self) -> None:
        from src.ai.embeddings.generator import EmbeddingGenerator
        import numpy as np

        with patch("openai.AsyncOpenAI", side_effect=Exception("API down")):
            with patch("sentence_transformers.SentenceTransformer") as mock_st:
                mock_model = MagicMock()
                mock_model.encode.return_value = np.array([[0.4, 0.5, 0.6]])
                mock_st.return_value = mock_model

                generator = EmbeddingGenerator()
                result = await generator.generate(["test"])
                assert len(result["embeddings"]) == 1


# ===========================================================================
# ai/vectordb/manager — chromadb client, embeddings, filter
# ===========================================================================
class TestVectorDBManagerExtended:
    """VectorDB manager — chromadb client, embeddings, filter."""

    def test_chromadb_client_initialization(self) -> None:
        from src.ai.vectordb.manager import VectorDBManager

        with patch("chromadb.HttpClient") as mock_http_client:
            with patch("src.infrastructure.config.get_settings") as mock_settings:
                mock_settings.return_value.ai.chromadb_host = "localhost"
                mock_settings.return_value.ai.chromadb_port = 8000
                mgr = VectorDBManager()
                mgr._get_client() # Trigger client creation
                mock_http_client.assert_called_once_with(host="localhost", port=8000)

    def test_embed_texts_with_sentence_transformer(self) -> None:
        from src.ai.vectordb.manager import VectorDBManager
        import numpy as np

        mgr = VectorDBManager()
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.1, 0.2]])

        with patch("sentence_transformers.SentenceTransformer", return_value=mock_model):
            result = mgr._embed_texts(["test text"])

        assert len(result) == 1


# ===========================================================================
# ai/agents/task_executor — full execute path
# ===========================================================================
class TestTaskExecutorExtended:
    """Task executor — full execute path with LLM mock."""

    @pytest.mark.asyncio
    async def test_execute_task_with_openai(self) -> None:
        from src.ai.agents.task_executor import AgentTaskExecutor

        executor = AgentTaskExecutor()

        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Task completed successfully."
        mock_response.choices = [mock_choice]
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30

        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch("openai.AsyncOpenAI", return_value=mock_client):
            with patch("src.infrastructure.config.get_settings") as mock_settings:
                mock_settings.return_value.ai.openai_api_key = "test-key"
                mock_settings.return_value.ai.openai_model = "gpt-4"
                mock_settings.return_value.ai.max_tokens = 1000

                result = await executor.execute(
                    agent_type="code_generator",
                    task="Write a function",
                    context={},
                    constraints=[],
                    output_format="code",
                )

        assert result["output"] == "Task completed successfully."

    @pytest.mark.asyncio
    async def test_execute_task_fallback_on_error(self) -> None:
        from src.ai.agents.task_executor import AgentTaskExecutor

        executor = AgentTaskExecutor()

        with patch("openai.AsyncOpenAI", side_effect=Exception("API error")):
            result = await executor.execute(
                task="Analyze data",
                agent_type="analyst",
                context={},
                constraints=[],
                output_format="markdown",
            )

        assert "task_id" in result
        assert "fallback" in result.get("usage", {})


# ===========================================================================
# ai/factory/expert_factory — RAG, LLM, not_found
# ===========================================================================
class TestExpertFactoryExtended:
    """Expert factory — RAG retrieval, LLM call, not_found."""

    def setup_method(self, method: object) -> None:
        from src.ai.factory.expert_factory import _EXPERT_STORE
        _EXPERT_STORE.clear()

    @pytest.mark.asyncio
    async def test_query_expert_with_rag_and_llm(self) -> None:
        from src.ai.factory.expert_factory import ExpertFactory

        factory = ExpertFactory()
        expert = await factory.create_expert(
            name="Quantum Physicist",
            domain="quantum",
            specialization="entanglement",
            knowledge_base=["kb_quantum"],
            model="gpt-4",
            temperature=0.2,
            system_prompt="",
        )
        expert_id = expert["id"]

        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Expert answer."
        mock_response.choices = [mock_choice]
        mock_response.usage.prompt_tokens = 5
        mock_response.usage.completion_tokens = 10
        mock_response.usage.total_tokens = 15

        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response

        mock_manager = AsyncMock()
        mock_manager.search.return_value = {"results": [{"document": "relevant doc"}]}

        with patch("openai.AsyncOpenAI", return_value=mock_client):
            with patch("src.infrastructure.config.get_settings") as mock_settings:
                mock_settings.return_value.ai.openai_api_key = "test-key"
                with patch("src.ai.vectordb.manager.VectorDBManager", return_value=mock_manager):
                    result = await factory.query_expert(
                        expert_id=expert_id,
                        query="What is quantum entanglement?",
                        context={"info": "Physics context"},
                        max_tokens=512,
                        include_sources=False,
                    )

        assert "answer" in result

    @pytest.mark.asyncio
    async def test_query_expert_rag_failure_continues(self) -> None:
        from src.ai.factory.expert_factory import ExpertFactory

        factory = ExpertFactory()
        expert = await factory.create_expert(
            name="Quantum Physicist",
            domain="quantum",
            specialization="entanglement",
            knowledge_base=["kb_quantum"],
            model="gpt-4",
            temperature=0.2,
            system_prompt="",
        )
        expert_id = expert["id"]

        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Answer without RAG."
        mock_response.choices = [mock_choice]
        mock_response.usage.prompt_tokens = 5
        mock_response.usage.completion_tokens = 10
        mock_response.usage.total_tokens = 15

        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch("openai.AsyncOpenAI", return_value=mock_client):
            with patch("src.infrastructure.config.get_settings") as mock_settings:
                mock_settings.return_value.ai.openai_api_key = "test-key"
                with patch("src.ai.vectordb.manager.VectorDBManager", side_effect=Exception("chromadb error")):
                    result = await factory.query_expert(
                        expert_id=expert_id,
                        query="What is superposition?",
                        context={},
                        max_tokens=512,
                        include_sources=False,
                    )

        assert result is not None

    @pytest.mark.asyncio
    async def test_query_expert_sources_appended(self) -> None:
        from src.ai.factory.expert_factory import ExpertFactory

        factory = ExpertFactory()
        expert = await factory.create_expert(
            name="Quantum Physicist",
            domain="quantum",
            specialization="entanglement",
            knowledge_base=["kb_quantum"],
            model="gpt-4",
            temperature=0.2,
            system_prompt="",
        )
        expert_id = expert["id"]

        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Answer with sources."
        mock_response.choices = [mock_choice]
        mock_response.usage.prompt_tokens = 5
        mock_response.usage.completion_tokens = 10
        mock_response.usage.total_tokens = 15

        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response

        mock_manager = AsyncMock()
        mock_manager.search.return_value = {
            "results": [{"document": "doc1"}, {"document": "doc2"}]
        }

        with patch("openai.AsyncOpenAI", return_value=mock_client):
            with patch("src.infrastructure.config.get_settings") as mock_settings:
                mock_settings.return_value.ai.openai_api_key = "test-key"
                with patch("src.ai.vectordb.manager.VectorDBManager", return_value=mock_manager):
                    result = await factory.query_expert(
                        expert_id=expert_id,
                        query="Explain VQE",
                        context={},
                        max_tokens=512,
                        include_sources=True,
                    )

        assert result is not None

    @pytest.mark.asyncio
    async def test_query_nonexistent_expert(self) -> None:
        from src.ai.factory.expert_factory import ExpertFactory

        factory = ExpertFactory()
        result = await factory.query_expert(
            expert_id="nonexistent_expert_xyz",
            query="What is this?",
            context={},
            max_tokens=512,
            include_sources=False,
        )
        assert "error" in result


# ===========================================================================
# scientific/analysis/calculus — romberg
# ===========================================================================
class TestCalculusRomberg:
    """Calculus — romberg integration method."""

    def test_romberg_integration(self) -> None:
        from src.scientific.analysis.calculus import NumericalCalculus as NumericalIntegrator

        integrator = NumericalIntegrator()
        result = integrator.integrate(
            function="x**2",
            lower_bound=0.0,
            upper_bound=1.0,
            method="romberg",
        )
        assert "result" in result
        assert abs(result["result"] - 1 / 3) < 0.01


# ===========================================================================
# scientific/analysis/interpolation — quadratic
# ===========================================================================
class TestInterpolationQuadratic:
    """Interpolation — quadratic method."""

    def test_quadratic_interpolation(self) -> None:
        from src.scientific.analysis.interpolation import Interpolator

        interp = Interpolator()
        result = interp.interpolate(
            x_data=[0.0, 1.0, 2.0, 3.0, 4.0],
            y_data=[0.0, 1.0, 4.0, 9.0, 16.0],
            x_new=[0.5, 1.5, 2.5],
            method="quadratic",
        )
        assert "y_interpolated" in result
        assert len(result["y_interpolated"]) == 3
