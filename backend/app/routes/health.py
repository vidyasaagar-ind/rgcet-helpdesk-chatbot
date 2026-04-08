from fastapi import APIRouter
from app.models.schemas import HealthResponse

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Returns a simple success payload to verify the backend is running."""
    return HealthResponse(
        status="success",
        message="RGCET Help Desk Backend API is operational.",
        version="0.1.0-stub"
    )
