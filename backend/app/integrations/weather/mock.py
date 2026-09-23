import math
from datetime import datetime, timedelta

from app.schemas.common import IntegrityStatus
from app.schemas.forecast import MockScenario
from app.schemas.weather import KnowledgeBoundary, WeatherContext, WeatherPoint

from .base import WeatherProvider


class MockWeatherProvider(WeatherProvider):
    def get_weather_context(
        self,
        issue_time: datetime,
        horizon_hours: int,
        scenario: MockScenario = MockScenario.normal,
    ) -> WeatherContext:
        leaked = scenario == MockScenario.leakage
        available_at = issue_time + timedelta(hours=6) if leaked else issue_time - timedelta(minutes=40)
        boundary = KnowledgeBoundary(
            issue_time=issue_time,
            weather_available_time=available_at,
            status=IntegrityStatus.failed if leaked else IntegrityStatus.passed,
            future_information_used=leaked,
            reason="Demo scenario: weather was not available at issue time." if leaked else None,
        )
        hourly = [
            WeatherPoint(
                timestamp=issue_time + timedelta(hours=lead),
                wind_100m=round(7.0 + 1.8 * math.sin(lead / 5), 2),
                wind_direction=round((235 + lead * 3) % 360, 1),
                temperature=round(-1.5 + 4 * math.sin((lead - 5) / 10), 1),
                pressure=1012.0,
            )
            for lead in range(1, horizon_hours + 1)
        ]
        return WeatherContext(
            weather_source="DEMO weather fixture",
            weather_run_id=f"mock-run-{issue_time:%Y%m%d%H}",
            forecast_run_time=issue_time - timedelta(hours=6),
            forecast_available_time=available_at,
            issue_time=issue_time,
            hourly=hourly,
            knowledge_boundary=boundary,
            is_mock=True,
        )
