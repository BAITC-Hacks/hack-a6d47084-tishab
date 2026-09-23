from datetime import datetime, timezone
from uuid import uuid4

from app.db.repository import ForecastRepository
from app.integrations.agent.base import AgentProvider
from app.integrations.errors import ProviderUnavailableError
from app.integrations.forecast.base import ForecastProvider
from app.integrations.weather.base import WeatherProvider
from app.schemas.agent import AgentResult
from app.schemas.forecast import ForecastDetail, ForecastRequest, Provenance


class ForecastService:
    def __init__(
        self,
        repository: ForecastRepository,
        forecast_provider: ForecastProvider,
        weather_provider: WeatherProvider,
        agent_provider: AgentProvider,
    ):
        self.repository = repository
        self.forecast_provider = forecast_provider
        self.weather_provider = weather_provider
        self.agent_provider = agent_provider

    def run(self, request: ForecastRequest) -> ForecastDetail:
        weather = self.weather_provider.get_weather_context(
            request.issue_time, request.horizon_hours, request.scenario
        )
        forecast = self.forecast_provider.run_forecast(
            request.issue_time, request.horizon_hours, request.scenario
        )
        try:
            agent = self.agent_provider.process(forecast, weather, request.scenario)
        except ProviderUnavailableError:
            agent = AgentResult(
                status="unavailable",
                fallback="deterministic",
                operator_message="Agent provider is unavailable; numerical forecast is preserved.",
            )

        forecast_id = f"F-{uuid4().hex[:10].upper()}"
        for entry in forecast.lineage:
            entry.forecast_id = forecast_id
        boundary = weather.knowledge_boundary
        provenance = Provenance(
            forecast_id=forecast_id,
            issue_time=request.issue_time,
            weather_run_id=weather.weather_run_id,
            weather_source=weather.weather_source,
            forecast_run_time=weather.forecast_run_time,
            forecast_available_time=weather.forecast_available_time,
            model_name=forecast.model_name,
            model_version=forecast.model_version,
            feature_version=forecast.feature_version,
            forecast_version=forecast.version,
            future_information_used=boundary.future_information_used,
            integrity_status=boundary.status,
            is_mock=forecast.is_mock or weather.is_mock,
        )
        detail = ForecastDetail(
            forecast_id=forecast_id,
            issue_time=request.issue_time,
            horizon_hours=request.horizon_hours,
            version=forecast.version,
            status=forecast.status,
            confidence="demo" if forecast.is_mock else None,
            model_name=forecast.model_name,
            integrity_status=boundary.status,
            created_at=datetime.now(timezone.utc),
            is_mock=forecast.is_mock or weather.is_mock or agent.is_mock,
            points=forecast.points,
            models=forecast.models,
            weather=weather,
            knowledge_boundary=boundary,
            provenance=provenance,
            agent=agent,
            events=agent.activity,
            lineage=forecast.lineage,
            revision=forecast.revision,
        )
        return self.repository.save(detail)
