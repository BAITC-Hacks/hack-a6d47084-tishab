from datetime import datetime

from app.integrations.errors import ProviderUnavailableError
from app.schemas.forecast import MockScenario
from app.schemas.weather import WeatherContext

from .base import WeatherProvider


class RealWeatherProvider(WeatherProvider):
    def get_weather_context(
        self,
        issue_time: datetime,
        horizon_hours: int,
        scenario: MockScenario = MockScenario.normal,
    ) -> WeatherContext:
        raise ProviderUnavailableError(
            "Real weather provider is not connected. Implement this adapter around the team weather module."
        )
