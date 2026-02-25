"""Integration tests for the workflow API endpoints wired to the ClosedLoopEngine.

Verifies that the FastAPI routes correctly delegate to the orchestrator engine
and return proper HTTP responses.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from presentation.api.routers.workflows import (
    CycleCancelResponse,
    CycleDetail,
    CycleTriggerResponse,
    PaginatedCyclesResponse,
    WorkflowEngineStatus,
    get_engine,
    router,
)
from engine.orchestrator.analysis_workflow import WorkflowConfig
from engine.orchestrator.closed_loop import ClosedLoopEngine


# ---------------------------------------------------------------------------
# Test app
# ---------------------------------------------------------------------------

from fastapi import FastAPI

app = FastAPI()
app.include_router(router)


@pytest.fixture
def fresh_engine() -> ClosedLoopEngine:
    """Return a fresh engine instance in running state."""
    engine = ClosedLoopEngine()
    engine.start()
    return engine


@pytest.fixture
def client(fresh_engine: ClosedLoopEngine) -> TestClient:
    """Test client with a monkeypatched engine."""
    import presentation.api.routers.workflows as wf_module
    original = wf_module._engine
    wf_module._engine = fresh_engine
    yield TestClient(app)
    wf_module._engine = original


# ===================================================================
# POST /api/v1/workflows/cycles — Trigger cycle
# ===================================================================


class TestTriggerCycle:
    """Test triggering governance analysis cycles via the API."""

    def test_trigger_returns_202(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/workflows/cycles",
            json={"name": "api-test-cycle"},
        )
        assert resp.status_code == 202
        body = resp.json()
        assert body["status"] == "pending"
        assert body["cycle_id"].startswith("CYCLE-")
        assert "api-test-cycle" in body["message"]

    def test_trigger_with_full_config(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/workflows/cycles",
            json={
                "name": "full-config",
                "description": "Full test cycle",
                "modules": ["mod-a", "mod-b"],
                "auto_enforce": True,
                "severity_threshold": "error",
                "max_duration_seconds": 1800,
                "tags": {"env": "test"},
            },
        )
        assert resp.status_code == 202

    def test_trigger_queues_cycle(
        self, client: TestClient, fresh_engine: ClosedLoopEngine
    ) -> None:
        client.post(
            "/api/v1/workflows/cycles",
            json={"name": "queued"},
        )
        assert fresh_engine.queue_depth == 1

    def test_trigger_invalid_severity_returns_422(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/workflows/cycles",
            json={"name": "bad", "severity_threshold": "banana"},
        )
        assert resp.status_code == 422

    def test_trigger_empty_name_returns_422(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/workflows/cycles",
            json={"name": ""},
        )
        assert resp.status_code == 422

    def test_trigger_on_stopped_engine_returns_503(
        self, client: TestClient, fresh_engine: ClosedLoopEngine
    ) -> None:
        fresh_engine.stop()
        resp = client.post(
            "/api/v1/workflows/cycles",
            json={"name": "stopped-test"},
        )
        assert resp.status_code == 503


# ===================================================================
# GET /api/v1/workflows/status — Engine status
# ===================================================================


class TestWorkflowStatus:
    """Test retrieving engine status via the API."""

    def test_status_returns_running(self, client: TestClient) -> None:
        resp = client.get("/api/v1/workflows/status")
        assert resp.status_code == 200
        body = resp.json()
        assert body["engine_status"] == "running"
        assert body["queued_cycles"] == 0
        assert body["active_cycles"] == 0

    def test_status_reflects_queued_cycles(
        self, client: TestClient, fresh_engine: ClosedLoopEngine
    ) -> None:
        # Submit a cycle first
        client.post(
            "/api/v1/workflows/cycles",
            json={"name": "queued-for-status"},
        )
        resp = client.get("/api/v1/workflows/status")
        body = resp.json()
        assert body["queued_cycles"] == 1


# ===================================================================
# GET /api/v1/workflows/cycles — List cycles
# ===================================================================


class TestListCycles:
    """Test listing governance cycles via the API."""

    def test_empty_list(self, client: TestClient) -> None:
        resp = client.get("/api/v1/workflows/cycles")
        assert resp.status_code == 200
        body = resp.json()
        assert body["items"] == []
        assert body["total"] == 0

    def test_list_after_execution(
        self, client: TestClient, fresh_engine: ClosedLoopEngine
    ) -> None:
        # Submit and run a cycle
        asyncio.get_event_loop().run_until_complete(
            fresh_engine.submit_cycle(WorkflowConfig(name="executed"))
        )
        asyncio.get_event_loop().run_until_complete(fresh_engine.run_pending())

        resp = client.get("/api/v1/workflows/cycles")
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["name"] == "executed"
        assert body["items"][0]["status"] == "completed"

    def test_pagination(
        self, client: TestClient, fresh_engine: ClosedLoopEngine
    ) -> None:
        # Run 3 cycles
        for i in range(3):
            asyncio.get_event_loop().run_until_complete(
                fresh_engine.submit_cycle(WorkflowConfig(name=f"cycle-{i}"))
            )
        asyncio.get_event_loop().run_until_complete(fresh_engine.run_pending())

        resp = client.get("/api/v1/workflows/cycles?skip=1&limit=1")
        body = resp.json()
        assert body["total"] == 3
        assert len(body["items"]) == 1
        assert body["has_next"] is True


# ===================================================================
# GET /api/v1/workflows/cycles/{cycle_id} — Get cycle detail
# ===================================================================


class TestGetCycle:
    """Test retrieving a specific cycle via the API."""

    def test_not_found(self, client: TestClient) -> None:
        resp = client.get("/api/v1/workflows/cycles/CYCLE-nonexistent")
        assert resp.status_code == 404

    def test_found_after_execution(
        self, client: TestClient, fresh_engine: ClosedLoopEngine
    ) -> None:
        cycle_id = asyncio.get_event_loop().run_until_complete(
            fresh_engine.submit_cycle(WorkflowConfig(name="detail-test"))
        )
        asyncio.get_event_loop().run_until_complete(fresh_engine.run_pending())

        resp = client.get(f"/api/v1/workflows/cycles/{cycle_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["cycle_id"] == cycle_id
        assert body["name"] == "detail-test"
        assert body["status"] == "completed"


# ===================================================================
# POST /api/v1/workflows/cycles/{cycle_id}/cancel — Cancel cycle
# ===================================================================


class TestCancelCycle:
    """Test cancelling cycles via the API."""

    def test_cancel_queued_cycle(
        self, client: TestClient, fresh_engine: ClosedLoopEngine
    ) -> None:
        # Submit but don't run
        cycle_id = asyncio.get_event_loop().run_until_complete(
            fresh_engine.submit_cycle(WorkflowConfig(name="to-cancel"))
        )

        resp = client.post(f"/api/v1/workflows/cycles/{cycle_id}/cancel")
        assert resp.status_code == 200
        body = resp.json()
        assert body["cycle_id"] == cycle_id
        assert body["status"] == "cancelled"
        assert fresh_engine.queue_depth == 0

    def test_cancel_nonexistent(self, client: TestClient) -> None:
        resp = client.post("/api/v1/workflows/cycles/CYCLE-fake/cancel")
        assert resp.status_code == 404
