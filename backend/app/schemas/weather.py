from datetime import datetime

from pydantic import Field

from .common import IntegrityStatus, StrictModel


class WeatherPoint(StrictModel):
    timestamp: datetime
    wind_10m: float | None = None
    wind_80m: float | None = None
    wind_100m: float | None = None
    wind_120m: float | None = None
    wind_direction: float | None = None
    temperature: float | None = None
    pressure: float | None = None


class KnowledgeBoundary(StrictModel):
    issue_time: datetime
    weather_available_time: datetime | None
    status: IntegrityStatus
    future_information_used: bool
    reason: str | None = None


class WeatherContext(StrictModel):
    weather_source: str | None
    weather_run_id: str | None
    forecast_run_time: datetime | None
    forecast_available_time: datetime | None
    issue_time: datetime
    hourly: list[WeatherPoint] = Field(default_factory=list)
    knowledge_boundary: KnowledgeBoundary
    is_mock: bool = False
