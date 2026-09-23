from abc import ABC, abstractmethod

from app.schemas.agent import AgentResult
from app.schemas.forecast import ForecastProviderResult, MockScenario
from app.schemas.weather import WeatherContext


class AgentProvider(ABC):
    @abstractmethod
    def process(
        self,
        forecast: ForecastProviderResult,
        weather: WeatherContext,
        scenario: MockScenario = MockScenario.normal,
    ) -> AgentResult:
        """Interpret structured context without producing numerical forecasts."""
