from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.database import get_db
from app.db.repository import ForecastRepository
from app.integrations.factory import build_agent_provider, build_forecast_provider, build_weather_provider
from app.services.backtest_service import BacktestService
from app.services.forecast_service import ForecastService


def get_repository(db: Session = Depends(get_db)) -> ForecastRepository:
    return ForecastRepository(db)


def get_forecast_service(
    repository: ForecastRepository = Depends(get_repository),
    settings: Settings = Depends(get_settings),
) -> ForecastService:
    return ForecastService(
        repository,
        build_forecast_provider(settings),
        build_weather_provider(settings),
        build_agent_provider(settings),
    )


def get_backtest_service(repository: ForecastRepository = Depends(get_repository)) -> BacktestService:
    return BacktestService(repository)
