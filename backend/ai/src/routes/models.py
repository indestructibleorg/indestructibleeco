from fastapi import APIRouter

router = APIRouter()

MODELS = [
    {
        "id": "quantum-bert-xxl-v1",
        "dim_range": [1024, 4096],
        "tolerance_range": [0.0001, 0.005],
        "status": "available",
    }
]

@router.get("/models")
async def list_models():
    return {"models": MODELS}