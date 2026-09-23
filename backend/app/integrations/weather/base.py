from abc import ABC, abstractmethod
from datetime import datetime

from app.schemas.forecast import MockScenario
from app.schemas.weather import WeatherContext


class WeatherProvider(ABC):
    @abstractmethod
    def get_weather_context(
        self,
        issue_time: datetime,
        horizon_hours: int,
        scenario: MockScenario = MockScenario.normal,
    ) -> WeatherContext:
        """Return weather and a boundary verdict computed outside the web layer."""
