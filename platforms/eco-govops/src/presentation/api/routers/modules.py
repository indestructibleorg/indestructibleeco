"""Module management endpoints for the GovOps Platform API.

Provides CRUD-style access to governance modules, including listing with
pagination and filtering, detail retrieval, evidence chain inspection,
full-text search, and compliance statistics.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, Path, Query, status
from pydantic import BaseModel, ConfigDict, Field

logger = structlog.get_logger("govops.modules")

router = APIRouter(prefix="/api/v1/modules", tags=["modules"])


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class ModuleSummary(BaseModel):
    """Compact module representation for list views."""

    model_config = ConfigDict(from_attributes=True)

    module_id: str
    name: str
    path: str
    gl_layer: str
    ng_era: str
    compliance_status: str
    last_scan_at: datetime | None = None
    binding_count: int = 0


class ModuleDetail(ModuleSummary):
    """Full module representation including metadata and bindings."""

    hash_signature: str = ""
    bindings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidenceEntry(BaseModel):
    """Single evidence record in a module's evidence chain."""

    evidence_id: str
    cycle_id: str
    evidence_type: str
    content_hash: str
    created_at: datetime
    chain_previous_hash: str | None = None


class EvidenceChainResponse(BaseModel):
    """Evidence chain for a specific module."""

    module_id: str
    chain_length: int = 0
    is_valid: bool = True
    entries: list[EvidenceEntry] = Field(default_factory=list)


class ModuleSearchRequest(BaseModel):
    """Search request body for module full-text search."""

    query: str = Field(..., min_length=1, max_length=500, description="Search query string.")
    gl_layers: list[str] = Field(default_factory=list, description="Filter by GL layers.")
    compliance_statuses: list[str] = Field(
        default_factory=list, description="Filter by compliance statuses."
    )
    limit: int = Field(default=20, ge=1, le=100, description="Maximum results to return.")
    offset: int = Field(default=0, ge=0, description="Result offset for pagination.")


class ModuleSearchResult(BaseModel):
    """A single search result with relevance score."""

    module: ModuleSummary
    score: float = Field(description="Relevance score (0.0 - 1.0).")
    highlights: dict[str, list[str]] = Field(
        default_factory=dict, description="Field-level match highlights."
    )


class ModuleSearchResponse(BaseModel):
    """Paginated search results."""

    query: str
    total: int = 0
    items: list[ModuleSearchResult] = Field(default_factory=list)
    limit: int = 20
    offset: int = 0


class PaginatedModulesResponse(BaseModel):
    """Paginated list of governance modules."""

    items: list[ModuleSummary] = Field(default_factory=list)
    total: int = Field(ge=0)
    skip: int = Field(ge=0)
    limit: int = Field(ge=1)
    has_next: bool = False


class ComplianceStats(BaseModel):
    """Aggregate compliance statistics across all modules."""

    total_modules: int = 0
    compliant: int = 0
    non_compliant: int = 0
    partially_compliant: int = 0
    unknown: int = 0
    exempt: int = 0
    compliance_rate: float = Field(
        default=0.0, description="Percentage of modules that are compliant or exempt."
    )
    by_gl_layer: dict[str, dict[str, int]] = Field(
        default_factory=dict, description="Compliance breakdown by GL layer."
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/stats",
    response_model=ComplianceStats,
    status_code=status.HTTP_200_OK,
    summary="Compliance statistics",
    description="Returns aggregate compliance statistics across all governed modules.",
)
async def get_compliance_stats() -> ComplianceStats:
    """Compute and return compliance statistics.

    This endpoint must be defined before ``/{module_id}`` to avoid path
    parameter conflicts in FastAPI routing.
    """
    logger.info("compliance_stats_requested")

    # Placeholder — in production this would query the module repository
    return ComplianceStats(
        total_modules=0,
        compliant=0,
        non_compliant=0,
        partially_compliant=0,
        unknown=0,
        exempt=0,
        compliance_rate=0.0,
        by_gl_layer={},
    )


@router.get(
    "",
    response_model=PaginatedModulesResponse,
    status_code=status.HTTP_200_OK,
    summary="List modules",
    description="Returns a paginated list of governance modules with optional filtering.",
)
async def list_modules(
    skip: int = Query(default=0, ge=0, description="Number of items to skip."),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum items to return."),
    gl_layer: str | None = Query(
        default=None, description="Filter by governance layer (e.g. GL30-49)."
    ),
    compliance_status: str | None = Query(
        default=None,
        description="Filter by compliance status (compliant, non_compliant, etc.).",
    ),
    name: str | None = Query(default=None, description="Filter by partial name match."),
) -> PaginatedModulesResponse:
    """List governance modules with pagination and optional filters."""
    logger.info(
        "modules_list_requested",
        skip=skip,
        limit=limit,
        gl_layer=gl_layer,
        compliance_status=compliance_status,
    )

    # Placeholder — in production this would query the module repository
    return PaginatedModulesResponse(
        items=[],
        total=0,
        skip=skip,
        limit=limit,
        has_next=False,
    )


@router.get(
    "/{module_id}",
    response_model=ModuleDetail,
    status_code=status.HTTP_200_OK,
    summary="Get module detail",
    description="Returns the full detail of a specific governance module.",
    responses={404: {"description": "Module not found."}},
)
async def get_module(
    module_id: str = Path(..., description="UUID of the governance module."),
) -> ModuleDetail:
    """Retrieve a single governance module by its identifier."""
    logger.info("module_detail_requested", module_id=module_id)

    # Validate UUID format
    try:
        uuid.UUID(module_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid module ID format: {module_id}",
        )

    # Placeholder — in production this would fetch from the module repository
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Module {module_id} not found.",
    )


@router.get(
    "/{module_id}/evidence",
    response_model=EvidenceChainResponse,
    status_code=status.HTTP_200_OK,
    summary="Get module evidence chain",
    description="Returns the tamper-evident evidence chain for a governance module.",
    responses={404: {"description": "Module not found."}},
)
async def get_module_evidence(
    module_id: str = Path(..., description="UUID of the governance module."),
) -> EvidenceChainResponse:
    """Retrieve the evidence chain for a specific module."""
    logger.info("module_evidence_requested", module_id=module_id)

    try:
        uuid.UUID(module_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid module ID format: {module_id}",
        )

    # Placeholder — in production this queries the evidence store
    return EvidenceChainResponse(
        module_id=module_id,
        chain_length=0,
        is_valid=True,
        entries=[],
    )


@router.post(
    "/search",
    response_model=ModuleSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search modules",
    description="Full-text search across governance modules with optional filters.",
)
async def search_modules(body: ModuleSearchRequest) -> ModuleSearchResponse:
    """Execute a full-text search against the module index."""
    logger.info(
        "module_search_requested",
        query=body.query,
        gl_layers=body.gl_layers,
        limit=body.limit,
    )

    # Placeholder — in production this queries the search index
    return ModuleSearchResponse(
        query=body.query,
        total=0,
        items=[],
        limit=body.limit,
        offset=body.offset,
    )
