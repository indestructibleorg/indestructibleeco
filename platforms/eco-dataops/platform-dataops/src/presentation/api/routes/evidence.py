"""Evidence API — Evidence pipeline lifecycle management endpoints."""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from engines.evidence_pipeline.engine import EvidencePipelineEngine

router = APIRouter()

_pipeline = EvidencePipelineEngine()


class IngestRequest(BaseModel):
    """Request to ingest new evidence."""

    source: str
    payload: dict[str, Any]


class IngestResponse(BaseModel):
    """Response from evidence ingestion."""

    record_id: str
    state: str
    hash_value: str
    chain_parent_hash: str | None = None


@router.post("/ingest", response_model=IngestResponse)
async def ingest_evidence(request: IngestRequest):
    """Ingest new evidence into the pipeline."""
    record = _pipeline.ingest(source=request.source, payload=request.payload)
    return IngestResponse(
        record_id=record.record_id,
        state=record.state.value,
        hash_value=record.hash_value,
        chain_parent_hash=record.chain_parent_hash,
    )


@router.get("/chain/integrity")
async def verify_chain():
    """Verify evidence chain integrity."""
    is_valid, errors = _pipeline.verify_chain_integrity()
    return {
        "valid": is_valid,
        "errors": errors,
        "chain_length": len(_pipeline.processed_records),
    }


@router.get("/stats")
async def pipeline_stats():
    """Get evidence pipeline statistics."""
    return _pipeline.get_pipeline_stats()
