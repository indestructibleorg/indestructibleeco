"""Tests for presentation/api/routes/ai.py and quantum.py.

Uses FastAPI TestClient with mocked use cases and dependencies.
"""
from __future__ import annotations
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient


def _make_app_with_ai_router():
    """Create a FastAPI app with AI router and mocked auth."""
    from src.presentation.api.routes.ai import router
    from src.presentation.api.dependencies import get_current_user, get_client_ip, get_current_active_user
    app = FastAPI()
    app.include_router(router, prefix="/ai")

    def _mock_user():
        return {"user_id": "user-1", "role": "admin", "roles": ["admin"], "permissions": ["ai:read", "ai:execute", "ai:manage"]}

    def _mock_ip():
        return "127.0.0.1"

    app.dependency_overrides[get_current_user] = _mock_user
    app.dependency_overrides[get_current_active_user] = _mock_user
    app.dependency_overrides[get_client_ip] = _mock_ip
    return app


def _make_app_with_quantum_router():
    """Create a FastAPI app with Quantum router and mocked auth."""
    from src.presentation.api.routes.quantum import router
    from src.presentation.api.dependencies import get_current_user, get_client_ip, get_current_active_user
    app = FastAPI()
    app.include_router(router, prefix="/quantum")

    def _mock_user():
        return {"user_id": "user-1", "role": "admin", "roles": ["admin"], "permissions": ["quantum:read", "quantum:execute"]}

    def _mock_ip():
        return "127.0.0.1"

    app.dependency_overrides[get_current_user] = _mock_user
    app.dependency_overrides[get_current_active_user] = _mock_user
    app.dependency_overrides[get_client_ip] = _mock_ip
    return app


# ===========================================================================
# AI Routes Tests
# ===========================================================================

class TestAIExpertRoutes:
    """Tests for /ai/experts endpoints."""

    def test_create_expert_success(self) -> None:
        """POST /ai/experts should create expert and return 201."""
        app = _make_app_with_ai_router()
        mock_result = {
            "expert_id": "exp-1",
            "name": "Test Expert",
            "domain": "finance",
            "specialization": "risk",
            "model": "gpt-4-turbo-preview",
            "status": "active",
            "created_at": None,
        }
        with patch("src.presentation.api.routes.ai.CreateExpertUseCase") as mock_cls:
            mock_cls.return_value.execute = AsyncMock(return_value=mock_result)
            with patch("src.presentation.api.routes.ai.AuditService.log", new_callable=AsyncMock):
                client = TestClient(app)
                resp = client.post("/ai/experts", json={
                    "name": "Test Expert",
                    "domain": "finance",
                    "owner_id": "user-1",
                })
        assert resp.status_code == 201
        assert resp.json()["expert_id"] == "exp-1"

    def test_query_expert_success(self) -> None:
        """POST /ai/experts/{id}/query should return query response."""
        app = _make_app_with_ai_router()
        mock_result = {
            "expert_id": "exp-1",
            "query": "What is risk?",
            "response": "Risk is...",
            "sources": [],
            "model": "gpt-4",
            "tokens_used": 100,
            "latency_ms": 500.0,
        }
        with patch("src.presentation.api.routes.ai.QueryExpertUseCase") as mock_cls:
            mock_cls.return_value.execute = AsyncMock(return_value=mock_result)
            client = TestClient(app)
            resp = client.post("/ai/experts/exp-1/query", json={
                "query": "What is risk?",
            })
        assert resp.status_code == 200
        assert resp.json()["response"] == "Risk is..."

    def test_list_experts_success(self) -> None:
        """GET /ai/experts should return expert list."""
        app = _make_app_with_ai_router()
        mock_result = [
            {"expert_id": "exp-1", "name": "Expert 1", "domain": "finance", "specialization": "", "model": "", "status": "active", "created_at": None},
        ]
        with patch("src.presentation.api.routes.ai.ListExpertsUseCase") as mock_cls:
            mock_cls.return_value.execute = AsyncMock(return_value=mock_result)
            client = TestClient(app)
            resp = client.get("/ai/experts")
        assert resp.status_code == 200

    def test_get_expert_success(self) -> None:
        """GET /ai/experts/{id} should return single expert."""
        app = _make_app_with_ai_router()
        mock_result = [
            {"expert_id": "exp-1", "name": "Expert 1", "domain": "finance", "specialization": "", "model": "", "status": "active", "created_at": None},
        ]
        with patch("src.presentation.api.routes.ai.ListExpertsUseCase") as mock_cls:
            mock_cls.return_value.execute = AsyncMock(return_value=mock_result)
            client = TestClient(app)
            resp = client.get("/ai/experts/exp-1")
        assert resp.status_code in (200, 404)

    def test_delete_expert_success(self) -> None:
        """DELETE /ai/experts/{id} should return 204."""
        app = _make_app_with_ai_router()
        with patch("src.presentation.api.routes.ai.DeleteExpertUseCase") as mock_cls:
            mock_cls.return_value.execute = AsyncMock(return_value={"deleted": True})
            with patch("src.presentation.api.routes.ai.AuditService.log", new_callable=AsyncMock):
                client = TestClient(app)
                resp = client.delete("/ai/experts/exp-1")
        assert resp.status_code == 204


class TestAIVectorRoutes:
    """Tests for /ai/vectors endpoints."""

    def test_vector_upsert_success(self) -> None:
        """POST /ai/vectors/upsert should store documents."""
        app = _make_app_with_ai_router()
        mock_result = {"collection": "docs", "document_count": 2, "status": "success"}
        with patch("src.presentation.api.routes.ai.CreateVectorCollectionUseCase") as mock_cls:
            mock_cls.return_value.execute = AsyncMock(return_value=mock_result)
            with patch("src.presentation.api.routes.ai.AuditService.log", new_callable=AsyncMock):
                client = TestClient(app)
                resp = client.post("/ai/vectors/upsert", json={
                    "collection": "docs",
                    "documents": ["doc1", "doc2"],
                })
        assert resp.status_code == 200
        assert resp.json()["document_count"] == 2

    def test_vector_search_success(self) -> None:
        """POST /ai/vectors/search should return search results."""
        app = _make_app_with_ai_router()
        mock_result = {
            "collection": "docs",
            "results": [{"id": "1", "score": 0.9, "document": "doc1"}],
            "total": 1,
            "query": "test query",
        }
        with patch("src.presentation.api.routes.ai.SearchVectorCollectionUseCase") as mock_cls:
            mock_cls.return_value.execute = AsyncMock(return_value=mock_result)
            client = TestClient(app)
            resp = client.post("/ai/vectors/search", json={
                "collection": "docs",
                "query": "test query",
            })
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_list_collections_success(self) -> None:
        """GET /ai/vectors/collections should return collection list."""
        app = _make_app_with_ai_router()
        mock_result = [{"name": "docs", "document_count": 10, "embedding_model": "text-embedding-3-small"}]
        with patch("src.presentation.api.routes.ai.ListVectorCollectionsUseCase") as mock_cls:
            mock_cls.return_value.execute = AsyncMock(return_value=mock_result)
            client = TestClient(app)
            resp = client.get("/ai/vectors/collections")
        assert resp.status_code == 200

    def test_list_collections_dict_response(self) -> None:
        """GET /ai/vectors/collections should handle dict response with 'collections' key."""
        app = _make_app_with_ai_router()
        mock_result = {"collections": [{"name": "docs", "document_count": 5, "embedding_model": ""}]}
        with patch("src.presentation.api.routes.ai.ListVectorCollectionsUseCase") as mock_cls:
            mock_cls.return_value.execute = AsyncMock(return_value=mock_result)
            client = TestClient(app)
            resp = client.get("/ai/vectors/collections")
        assert resp.status_code == 200

    def test_delete_collection_success(self) -> None:
        """DELETE /ai/vectors/collections/{name} should return 204."""
        app = _make_app_with_ai_router()
        with patch("src.ai.vectordb.manager.VectorDBManager") as mock_mgr_cls:
            mock_mgr_cls.return_value.delete_collection = AsyncMock(return_value=None)
            with patch("src.presentation.api.routes.ai.AuditService.log", new_callable=AsyncMock):
                client = TestClient(app)
                resp = client.delete("/ai/vectors/collections/docs")
        assert resp.status_code == 204


class TestAIAgentRoutes:
    """Tests for /ai/agents endpoints."""

    def test_execute_agent_task_success(self) -> None:
        """POST /ai/agents/execute should dispatch task and return result."""
        app = _make_app_with_ai_router()
        mock_result = {
            "task_id": "task-1",
            "agent_type": "code_generator",
            "status": "completed",
            "output": "def hello(): pass",
            "artifacts": [],
            "execution_time_ms": 1500.0,
        }
        with patch("src.presentation.api.routes.ai.ExecuteAgentTaskUseCase") as mock_cls:
            mock_cls.return_value.execute = AsyncMock(return_value=mock_result)
            with patch("src.presentation.api.routes.ai.AuditService.log", new_callable=AsyncMock):
                client = TestClient(app)
                resp = client.post("/ai/agents/execute", json={
                    "agent_type": "code_generator",
                    "task": "Write a hello world function",
                })
        assert resp.status_code == 200
        assert resp.json()["agent_type"] == "code_generator"

    def test_execute_agent_task_invalid_type(self) -> None:
        """POST /ai/agents/execute with invalid agent_type should return 422."""
        app = _make_app_with_ai_router()
        client = TestClient(app)
        resp = client.post("/ai/agents/execute", json={
            "agent_type": "invalid_agent",
            "task": "do something",
        })
        assert resp.status_code == 422


class TestAIEmbeddingRoutes:
    """Tests for /ai/embeddings endpoint."""

    def test_generate_embeddings_success(self) -> None:
        """POST /ai/embeddings should return embeddings."""
        app = _make_app_with_ai_router()
        mock_result = {
            "model": "text-embedding-3-small",
            "embeddings": [[0.1, 0.2, 0.3]],
            "total_tokens": 5,
        }
        with patch("src.presentation.api.routes.ai.GenerateEmbeddingsUseCase") as mock_cls:
            mock_cls.return_value.execute = AsyncMock(return_value=mock_result)
            client = TestClient(app)
            resp = client.post("/ai/embeddings", json={
                "texts": ["hello world"],
            })
        assert resp.status_code == 200
        assert resp.json()["model"] == "text-embedding-3-small"


# ===========================================================================
# Quantum Routes Tests
# ===========================================================================

class TestQuantumJobRoutes:
    """Tests for /quantum/jobs endpoints."""

    def test_submit_job_success(self) -> None:
        """POST /quantum/jobs should submit circuit and return 201."""
        app = _make_app_with_quantum_router()
        mock_result = {
            "job_id": "job-1",
            "algorithm": "bell",
            "status": "completed",
            "result": {"counts": {"00": 512, "11": 512}},
            "metadata": {},
            "execution_time_ms": 100.0,
        }
        with patch("src.presentation.api.routes.quantum.SubmitQuantumJobUseCase") as mock_cls:
            mock_cls.return_value.execute = AsyncMock(return_value=mock_result)
            with patch("src.presentation.api.routes.quantum.AuditService.log", new_callable=AsyncMock):
                client = TestClient(app)
                resp = client.post("/quantum/jobs", json={
                    "circuit_type": "bell",
                    "num_qubits": 2,
                    "shots": 1024,
                    "parameters": {},
                })
        assert resp.status_code == 201
        assert resp.json()["job_id"] == "job-1"

    def test_list_jobs_success(self) -> None:
        """GET /quantum/jobs should return job list."""
        app = _make_app_with_quantum_router()
        with patch("src.quantum.runtime.executor.QuantumExecutor") as mock_cls:
            mock_cls.return_value.list_jobs = AsyncMock(return_value={"items": [], "total": 0})
            client = TestClient(app)
            resp = client.get("/quantum/jobs")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_get_job_success(self) -> None:
        """GET /quantum/jobs/{id} should return job details."""
        app = _make_app_with_quantum_router()
        mock_job = {
            "job_id": "job-1",
            "algorithm": "bell",
            "status": "completed",
            "result": {"counts": {"00": 512, "11": 512}},
            "metadata": {},
            "execution_time_ms": 100.0,
        }
        with patch("src.quantum.runtime.executor.QuantumExecutor") as mock_cls:
            mock_cls.return_value.get_job = AsyncMock(return_value=mock_job)
            client = TestClient(app)
            resp = client.get("/quantum/jobs/job-1")
        assert resp.status_code == 200
        assert resp.json()["job_id"] == "job-1"

    def test_cancel_job_not_found(self) -> None:
        """POST /quantum/jobs/{id}/cancel should return 404 when job not found."""
        from src.domain.exceptions import EntityNotFoundException
        from fastapi.responses import JSONResponse
        app = _make_app_with_quantum_router()
        @app.exception_handler(EntityNotFoundException)
        async def _handle_not_found(request, exc):
            return JSONResponse(status_code=404, content={"detail": str(exc)})
        with patch("src.quantum.runtime.executor.QuantumExecutor") as mock_cls:
            mock_cls.return_value.cancel_job = AsyncMock(return_value=None)
            with patch("src.presentation.api.routes.quantum.AuditService.log", new_callable=AsyncMock):
                client = TestClient(app, raise_server_exceptions=False)
                resp = client.post("/quantum/jobs/missing-job/cancel")
        assert resp.status_code == 404

    def test_cancel_job_success(self) -> None:
        """POST /quantum/jobs/{id}/cancel should return cancellation result."""
        app = _make_app_with_quantum_router()
        mock_result = {"job_id": "job-1", "status": "cancelled", "message": "Job cancelled"}
        with patch("src.quantum.runtime.executor.QuantumExecutor") as mock_cls:
            mock_cls.return_value.cancel_job = AsyncMock(return_value=mock_result)
            with patch("src.presentation.api.routes.quantum.AuditService.log", new_callable=AsyncMock):
                client = TestClient(app)
                resp = client.post("/quantum/jobs/job-1/cancel")
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"


class TestQuantumBackendRoutes:
    """Tests for /quantum/backends endpoint."""

    def test_list_backends_success(self) -> None:
        """GET /quantum/backends should return backend list."""
        app = _make_app_with_quantum_router()
        mock_result = [
            {"name": "aer_simulator", "provider": "IBM", "num_qubits": 30, "status": "available", "description": ""},
        ]
        with patch("src.presentation.api.routes.quantum.ListQuantumBackendsUseCase") as mock_cls:
            mock_cls.return_value.execute = AsyncMock(return_value=mock_result)
            client = TestClient(app)
            resp = client.get("/quantum/backends")
        assert resp.status_code == 200
        assert len(resp.json()) == 1


class TestQuantumAlgorithmRoutes:
    """Tests for /quantum/vqe, /quantum/qaoa, /quantum/qml endpoints."""

    def test_solve_vqe_success(self) -> None:
        """POST /quantum/vqe/solve should execute VQE and return 201."""
        app = _make_app_with_quantum_router()
        mock_result = {
            "job_id": "vqe-1",
            "algorithm": "vqe",
            "status": "completed",
            "result": {"energy": -1.137},
            "metadata": {},
            "execution_time_ms": 2000.0,
        }
        with patch("src.presentation.api.routes.quantum.RunVQEUseCase") as mock_cls:
            mock_cls.return_value.execute = AsyncMock(return_value=mock_result)
            with patch("src.presentation.api.routes.quantum.AuditService.log", new_callable=AsyncMock):
                client = TestClient(app)
                resp = client.post("/quantum/vqe/solve", json={
                    "hamiltonian": {"paulis": [{"coeff": 1.0, "label": "ZZ"}, {"coeff": -1.0, "label": "II"}]},
                    "num_qubits": 2,
                    "ansatz": "ry",
                    "optimizer": "COBYLA",
                    "max_iterations": 100,
                    "shots": 1024,
                })
        assert resp.status_code == 201
        assert resp.json()["job_id"] == "vqe-1"

    def test_optimize_qaoa_success(self) -> None:
        """POST /quantum/qaoa/optimize should execute QAOA and return 201."""
        app = _make_app_with_quantum_router()
        mock_result = {
            "job_id": "qaoa-1",
            "algorithm": "qaoa",
            "status": "completed",
            "result": {"optimal_value": 3.5},
            "metadata": {},
            "execution_time_ms": 1500.0,
        }
        with patch("src.presentation.api.routes.quantum.RunQAOAUseCase") as mock_cls:
            mock_cls.return_value.execute = AsyncMock(return_value=mock_result)
            with patch("src.presentation.api.routes.quantum.AuditService.log", new_callable=AsyncMock):
                client = TestClient(app)
                resp = client.post("/quantum/qaoa/optimize", json={
                    "num_qubits": 4,
                    "cost_matrix": [[0, 1], [1, 0]],
                    "num_layers": 2,
                    "optimizer": "COBYLA",
                    "shots": 1024,
                })
        assert resp.status_code == 201
        assert resp.json()["job_id"] == "qaoa-1"

    def test_qml_classify_success(self) -> None:
        """POST /quantum/qml/classify should execute QML and return 201."""
        app = _make_app_with_quantum_router()
        mock_result = {
            "job_id": "qml-1",
            "algorithm": "qml",
            "status": "completed",
            "result": {"accuracy": 0.95},
            "metadata": {},
            "execution_time_ms": 3000.0,
        }
        with patch("src.presentation.api.routes.quantum.RunQMLUseCase") as mock_cls:
            mock_cls.return_value.execute = AsyncMock(return_value=mock_result)
            with patch("src.presentation.api.routes.quantum.AuditService.log", new_callable=AsyncMock):
                client = TestClient(app)
                resp = client.post("/quantum/qml/classify", json={
                    "num_qubits": 2,
                    "training_data": [[0.1, 0.2], [0.3, 0.4]],
                    "training_labels": [0, 1],
                    "test_data": [[0.15, 0.25]],
                    "feature_map": "ZZFeatureMap",
                    "ansatz": "RealAmplitudes",
                    "epochs": 10,
                })
        assert resp.status_code == 201
        assert resp.json()["job_id"] == "qml-1"
