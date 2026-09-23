from fastapi import APIRouter, Depends, HTTPException, status

from app.db.repository import ForecastRepository
from app.dependencies import get_forecast_service, get_repository
from app.integrations.errors import ProviderUnavailableError
from app.schemas.agent import AgentResult
from app.schemas.common import APIError, AgentEvent
from app.schemas.forecast import ForecastDetail, ForecastRequest, ForecastRunSummary, LineageEntry
from app.schemas.weather import WeatherContext
from app.services.forecast_service import ForecastService

router = APIRouter(prefix="/forecasts", tags=["forecasts"])


def _get_or_404(repository: ForecastRepository, forecast_id: str) -> ForecastDetail:
    try:
        return repository.get(forecast_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Forecast not found") from exc


@router.post(
    "/run",
    response_model=ForecastDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Run a forecast through configured providers",
    description="Orchestrates provider adapters and persists their structured result. In mock mode all values are demo data.",
    responses={503: {"model": APIError, "description": "Forecast or weather provider unavailable"}},
)
def run_forecast(
    request: ForecastRequest,
    service: ForecastService = Depends(get_forecast_service),
) -> ForecastDetail:
    try:
        return service.run(request)
    except ProviderUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get(
    "",
    response_model=list[ForecastRunSummary],
    summary="List stored forecast runs",
    description="Returns application-level run metadata in reverse chronological order.",
)
def list_forecasts(repository: ForecastRepository = Depends(get_repository)) -> list[ForecastRunSummary]:
    return repository.list()


@router.get(
    "/{forecast_id}",
    response_model=ForecastDetail,
    summary="Get a complete forecast run",
    responses={404: {"model": APIError}},
)
def get_forecast(forecast_id: str, repository: ForecastRepository = Depends(get_repository)) -> ForecastDetail:
    return _get_or_404(repository, forecast_id)


@router.get(
    "/{forecast_id}/lineage",
    response_model=list[LineageEntry],
    summary="Get forecast version lineage",
    responses={404: {"model": APIError}},
)
def get_lineage(forecast_id: str, repository: ForecastRepository = Depends(get_repository)) -> list[LineageEntry]:
    return _get_or_404(repository, forecast_id).lineage


@router.get(
    "/{forecast_id}/weather",
    response_model=WeatherContext,
    summary="Get weather context and knowledge-boundary verdict",
    responses={404: {"model": APIError}},
)
def get_weather(forecast_id: str, repository: ForecastRepository = Depends(get_repository)) -> WeatherContext:
    detail = _get_or_404(repository, forecast_id)
    if detail.weather is None:
        raise HTTPException(status_code=404, detail="Weather context not available")
    return detail.weather


@router.get(
    "/{forecast_id}/agent",
    response_model=AgentResult,
    summary="Get structured agent result",
    responses={404: {"model": APIError}},
)
def get_agent(forecast_id: str, repository: ForecastRepository = Depends(get_repository)) -> AgentResult:
    return _get_or_404(repository, forecast_id).agent


@router.get(
    "/{forecast_id}/events",
    response_model=list[AgentEvent],
    summary="Get agent and application events",
    responses={404: {"model": APIError}},
)
def get_events(forecast_id: str, repository: ForecastRepository = Depends(get_repository)) -> list[AgentEvent]:
    return _get_or_404(repository, forecast_id).events
