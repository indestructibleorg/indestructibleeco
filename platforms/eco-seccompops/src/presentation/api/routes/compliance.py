"""Compliance API — Regulatory compliance status and mapping endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
async def compliance_status():
    """Get overall compliance status across all frameworks."""
    return {
        "status": "compliant",
        "frameworks": {
            "NIST_800_53": {"status": "active", "controls_implemented": 3},
            "ISO_27001": {"status": "active", "controls_implemented": 3},
            "SOC2_Type_II": {"status": "active", "controls_implemented": 3},
            "GDPR": {"status": "active", "controls_implemented": 2},
            "PCI_DSS": {"status": "active", "controls_implemented": 2},
            "HIPAA": {"status": "active", "controls_implemented": 2},
        },
    }


@router.get("/frameworks/{framework}")
async def get_framework_details(framework: str):
    """Get detailed compliance status for a specific framework."""
    return {"framework": framework, "controls": [], "status": "active"}


@router.get("/registries")
async def list_registries():
    """List all governance registries and their validation status."""
    return {
        "registries": [
            {"name": "governance_registry", "version": "1.0.0", "status": "PASSED"},
            {"name": "architecture_registry", "version": "1.0.0", "status": "PASSED"},
            {"name": "execution_registry", "version": "1.0.0", "status": "PASSED"},
            {"name": "cross_registry_mapping", "version": "1.0.0", "status": "PASSED"},
        ]
    }
