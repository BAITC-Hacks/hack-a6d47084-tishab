from abc import ABC, abstractmethod
from datetime import datetime

from app.schemas.forecast import ForecastProviderResult, MockScenario


class ForecastProvider(ABC):
    @abstractmethod
    def run_forecast(
        self,
        issue_time: datetime,
        horizon_hours: int,
        scenario: MockScenario = MockScenario.normal,
    ) -> ForecastProviderResult:
        """Return already-computed forecasts; web code must not implement ML."""
