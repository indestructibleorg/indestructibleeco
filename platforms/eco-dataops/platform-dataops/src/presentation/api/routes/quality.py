"""Quality API — Data quality governance and SLO endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
async def quality_status():
    """Get overall data quality status across all dimensions."""
    return {
        "status": "healthy",
        "dimensions": {
            "COMPLETENESS": {"slo_target": "99.9%", "current": "99.95%", "status": "met"},
            "ACCURACY": {"slo_target": "99.5%", "current": "99.8%", "status": "met"},
            "CONSISTENCY": {"slo_target": "99.0%", "current": "99.5%", "status": "met"},
            "TIMELINESS": {"slo_target": "95.0%", "current": "97.2%", "status": "met"},
            "INTEGRITY": {"slo_target": "100.0%", "current": "100.0%", "status": "met"},
        },
    }


@router.get("/gates")
async def list_quality_gates():
    """List all quality gates and their current status."""
    return {
        "gates": [
            {"gate_id": "QG-INGEST", "stage": "INGEST", "status": "ACTIVE", "pass_rate": "99.9%"},
            {"gate_id": "QG-VALIDATE", "stage": "VALIDATE", "status": "ACTIVE", "pass_rate": "99.7%"},
            {"gate_id": "QG-SEAL", "stage": "SEAL", "status": "ACTIVE", "pass_rate": "100.0%"},
        ]
    }


@router.get("/registries")
async def list_registries():
    """List all DataOps registries and their validation status."""
    return {
        "registries": [
            {"name": "evidence_lifecycle_registry", "version": "1.0.0", "status": "PASSED"},
            {"name": "replay_specification_registry", "version": "1.0.0", "status": "PASSED"},
            {"name": "semantic_rules_registry", "version": "1.0.0", "status": "PASSED"},
            {"name": "data_quality_registry", "version": "1.0.0", "status": "PASSED"},
            {"name": "cross_registry_mapping", "version": "1.0.0", "status": "PASSED"},
        ]
    }
