from datetime import datetime

from app.integrations.errors import ProviderUnavailableError
from app.schemas.forecast import ForecastProviderResult, MockScenario

from .base import ForecastProvider


class RealForecastProvider(ForecastProvider):
    def run_forecast(
        self,
        issue_time: datetime,
        horizon_hours: int,
        scenario: MockScenario = MockScenario.normal,
    ) -> ForecastProviderResult:
        raise ProviderUnavailableError(
            "Real forecast provider is not connected. Implement this adapter around the team forecasting module."
        )
