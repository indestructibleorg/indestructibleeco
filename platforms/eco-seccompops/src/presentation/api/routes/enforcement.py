"""Enforcement API — Zero-tolerance governance enforcement endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from engines.zero_tolerance.engine import (
    ArchitectureLayer,
    ExecutionPhase,
    GovernanceEvent,
    ZeroToleranceEnforcementEngine,
)

router = APIRouter()

# Singleton engine instance
_engine = ZeroToleranceEnforcementEngine()
_engine.initialize_genesis()


class EnforceEventRequest(BaseModel):
    """Request to enforce a governance event."""

    event_type: str
    actor: str
    action: str
    target: str
    execution_phase: int = 1
    architecture_layer: int = 1
    evidence: dict[str, Any] = {}


class EnforceEventResponse(BaseModel):
    """Response from enforcement evaluation."""

    accepted: bool
    event_id: str
    violation: dict[str, Any] | None = None


@router.post("/evaluate", response_model=EnforceEventResponse)
async def evaluate_event(request: EnforceEventRequest):
    """Evaluate a governance event through zero-tolerance rules."""
    event = GovernanceEvent(
        event_type=request.event_type,
        actor=request.actor,
        action=request.action,
        target=request.target,
        execution_phase=ExecutionPhase(request.execution_phase),
        architecture_layer=ArchitectureLayer(request.architecture_layer),
        evidence=request.evidence,
    )
    event.hash_value = event.compute_hash()

    passed, violation = _engine.process_event(event)

    return EnforceEventResponse(
        accepted=passed,
        event_id=event.event_id,
        violation={
            "violation_id": violation.violation_id,
            "type": violation.violation_type.value,
            "level": violation.enforcement_level.name,
            "description": violation.description,
            "blocking": violation.blocking,
        }
        if violation
        else None,
    )


@router.get("/report")
async def get_violation_report():
    """Get current violation report."""
    return _engine.get_violation_report()


@router.get("/chain/integrity")
async def verify_chain_integrity():
    """Verify evidence chain integrity."""
    is_valid, errors = _engine.verify_chain_integrity()
    return {"valid": is_valid, "errors": errors, "chain_length": len(_engine.evidence_chain)}
