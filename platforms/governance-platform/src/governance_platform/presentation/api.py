"""Governance Platform API — FastAPI router for policy evaluation, quality gates, and reasoning.

Routes:
    POST /policies/evaluate  — evaluate policies against an operation
    POST /gates/run          — run a quality gate against data
    POST /reasoning/query    — dual-path reasoning query
    GET  /health             — health check
"""

from __future__ import annotations

from typing import Any

try:
    from fastapi import APIRouter, HTTPException
    from pydantic import BaseModel, Field

    _HAS_FASTAPI = True
except ImportError:
    _HAS_FASTAPI = False

from governance_platform.engines.policy_engine import PolicyEngine
from governance_platform.engines.quality_gate_engine import QualityGateEngine
from governance_platform.engines.reasoning_engine import ReasoningEngine


def create_router(
    policy_engine: PolicyEngine | None = None,
    gate_engine: QualityGateEngine | None = None,
    reasoning_engine: ReasoningEngine | None = None,
) -> Any:
    """Create and return the governance API router.

    Falls back to a stub dict if FastAPI is not installed (for testing without deps).
    """
    pe = policy_engine or PolicyEngine()
    ge = gate_engine or QualityGateEngine()
    re_ = reasoning_engine or ReasoningEngine()

    if not _HAS_FASTAPI:
        # Return a lightweight dict-based stub for environments without FastAPI
        return _create_stub_router(pe, ge, re_)

    router = APIRouter(tags=["governance"])

    # -- Request / Response models ---------------------------------------------

    class PolicyRuleModel(BaseModel):
        field: str
        operator: str
        value: Any

    class PolicyModel(BaseModel):
        id: str = ""
        name: str = ""
        rules: list[PolicyRuleModel] = Field(default_factory=list)
        severity: str = "medium"
        enabled: bool = True

    class EvaluatePoliciesRequest(BaseModel):
        operation: dict[str, Any]
        policies: list[PolicyModel]

    class GateCheckModel(BaseModel):
        name: str
        field: str
        operator: str = "eq"
        expected: Any = None

    class QualityGateModel(BaseModel):
        id: str = ""
        name: str = ""
        checks: list[GateCheckModel] = Field(default_factory=list)
        threshold: float = 1.0

    class RunGateRequest(BaseModel):
        gate: QualityGateModel
        data: dict[str, Any]

    class ReasoningQueryRequest(BaseModel):
        question: str
        sources: list[str] = Field(default_factory=list)
        context: dict[str, Any] = Field(default_factory=dict)

    # -- Routes ----------------------------------------------------------------

    @router.post("/policies/evaluate")
    async def evaluate_policies(request: EvaluatePoliciesRequest) -> dict[str, Any]:
        """Evaluate a set of policies against an operation."""
        payload = {
            "operation": request.operation,
            "policies": [p.model_dump() for p in request.policies],
        }
        return await pe.execute(payload)

    @router.post("/gates/run")
    async def run_gate(request: RunGateRequest) -> dict[str, Any]:
        """Run a quality gate against provided data."""
        payload = {
            "gate": request.gate.model_dump(),
            "data": request.data,
        }
        return await ge.execute(payload)

    @router.post("/reasoning/query")
    async def reasoning_query(request: ReasoningQueryRequest) -> dict[str, Any]:
        """Execute a dual-path reasoning query."""
        payload = {
            "question": request.question,
            "sources": request.sources,
            "context": request.context,
        }
        return await re_.execute(payload)

    @router.get("/health")
    async def health() -> dict[str, Any]:
        return {
            "status": "healthy",
            "platform": "governance-platform",
            "engines": {
                "policy_engine": pe.status.value,
                "quality_gate_engine": ge.status.value,
                "reasoning_engine": re_.status.value,
            },
        }

    return router


def _create_stub_router(
    pe: PolicyEngine,
    ge: QualityGateEngine,
    re_: ReasoningEngine,
) -> dict[str, Any]:
    """Stub router for environments without FastAPI — used only for import testing."""
    return {
        "type": "stub",
        "routes": ["/policies/evaluate", "/gates/run", "/reasoning/query", "/health"],
        "engines": {"policy": pe, "gate": ge, "reasoning": re_},
    }
