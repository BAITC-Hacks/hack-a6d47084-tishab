from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.schemas.health import HealthResponse

router = APIRouter(tags=["system"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Check API health",
    description="Reports API availability and configured provider modes without calling team modules.",
)
def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        environment=settings.app_env,
        providers={
            "forecast": settings.forecast_provider,
            "weather": settings.weather_provider,
            "agent": settings.agent_provider,
        },
    )
