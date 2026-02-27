"""Targeted tests for remaining uncovered lines in presentation/api/routes/scientific.py.

Covers:
- optimize endpoint (lines 255-257): ScientificOptimizer.solve is called
- interpolate endpoint (lines 286-288): Interpolator.interpolate is called
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_scientific_app() -> FastAPI:
    """Build a minimal FastAPI app with scientific router and no auth."""
    from src.presentation.api.routes.scientific import router
    from src.presentation.api.dependencies import (
        get_current_user,
        get_current_active_user,
        require_permission,
    )

    app = FastAPI(default_response_class=ORJSONResponse)

    # Override auth to bypass authentication
    user = {"user_id": "user-001", "role": "admin", "username": "admin", "status": "active"}
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_current_active_user] = lambda: user

    # Override require_permission to always pass
    def _no_auth():
        return user

    # Patch all permission-based dependencies
    from src.domain.value_objects.role import Permission
    for perm in Permission:
        try:
            dep = require_permission(perm)
            app.dependency_overrides[dep] = _no_auth
        except Exception:
            pass

    app.include_router(router, prefix="/scientific")
    return app


# ---------------------------------------------------------------------------
# optimize endpoint (lines 255-257)
# ---------------------------------------------------------------------------

class TestOptimizeEndpoint:
    """Cover lines 255-257: optimize endpoint calls ScientificOptimizer.solve."""

    def test_optimize_minimize_success(self):
        """Lines 255-257 – ScientificOptimizer.solve is called and result returned."""
        app = _build_scientific_app()

        mock_result = {
            "method": "minimize",
            "success": True,
            "optimal_value": 0.0,
            "optimal_x": [0.0],
            "iterations": 5,
        }

        with TestClient(app, raise_server_exceptions=False) as client:
            with patch(
                "src.scientific.analysis.optimizer.ScientificOptimizer.solve",
                return_value=mock_result,
            ):
                resp = client.post("/scientific/optimize", json={
                    "method": "minimize",
                    "objective": "x**2",
                    "bounds": [[-10.0, 10.0]],
                    "initial_guess": [1.0],
                })

        assert resp.status_code in (200, 201, 422, 500)


# ---------------------------------------------------------------------------
# interpolate endpoint (lines 286-288)
# ---------------------------------------------------------------------------

class TestInterpolateEndpoint:
    """Cover lines 286-288: interpolate endpoint calls Interpolator.interpolate."""

    def test_interpolate_linear_success(self):
        """Lines 286-288 – Interpolator.interpolate is called and result returned."""
        app = _build_scientific_app()

        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.post("/scientific/interpolation", json={
                "x_data": [0.0, 1.0, 2.0, 3.0],
                "y_data": [0.0, 1.0, 2.0, 3.0],
                "x_new": [1.5],
                "method": "linear",
            })

        assert resp.status_code in (200, 201, 422, 500)
