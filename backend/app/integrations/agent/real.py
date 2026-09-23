from app.integrations.errors import ProviderUnavailableError
from app.schemas.agent import AgentResult
from app.schemas.forecast import ForecastProviderResult, MockScenario
from app.schemas.weather import WeatherContext

from .base import AgentProvider


class RealAgentProvider(AgentProvider):
    def process(
        self,
        forecast: ForecastProviderResult,
        weather: WeatherContext,
        scenario: MockScenario = MockScenario.normal,
    ) -> AgentResult:
        raise ProviderUnavailableError(
            "Real agent provider is not connected. Implement this adapter around the team supervisor module."
        )
