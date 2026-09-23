from datetime import timedelta

from app.schemas.agent import AgentResult
from app.schemas.common import AgentEvent, EventStatus
from app.schemas.forecast import ForecastProviderResult, MockScenario
from app.schemas.weather import WeatherContext

from .base import AgentProvider


class MockAgentProvider(AgentProvider):
    def process(
        self,
        forecast: ForecastProviderResult,
        weather: WeatherContext,
        scenario: MockScenario = MockScenario.normal,
    ) -> AgentResult:
        if scenario == MockScenario.agent_off:
            return AgentResult(
                status="unavailable",
                fallback="deterministic",
                operator_message="Agent is unavailable; numerical mock forecast remains accessible.",
                is_mock=True,
            )

        issue_time = weather.issue_time
        rejected = weather.knowledge_boundary.future_information_used
        events = [
            AgentEvent(
                timestamp=issue_time + timedelta(seconds=1),
                type="weather_validation",
                status=EventStatus.failed if rejected else EventStatus.success,
                message="Future weather detected in demo scenario." if rejected else "Mock weather vintage verdict received.",
            ),
            AgentEvent(
                timestamp=issue_time + timedelta(seconds=3),
                type="forecast_validation",
                status=EventStatus.warning if rejected else EventStatus.success,
                message="Forecast rejected by upstream boundary result." if rejected else "Structured forecast received from provider.",
            ),
            AgentEvent(
                timestamp=issue_time + timedelta(seconds=4),
                type="publication",
                status=EventStatus.failed if rejected else EventStatus.success,
                message="Publication blocked." if rejected else "Mock forecast published.",
            ),
        ]
        return AgentResult(
            status="completed",
            summary="Demo forecast rejected." if rejected else "Demo forecast accepted.",
            decision="reject" if rejected else "publish",
            warnings=["Future information was reported by the mock weather provider."] if rejected else [],
            operator_message=(
                "Do not use this run: mock future weather was detected."
                if rejected
                else "Mock run passed the provided validation verdict."
            ),
            activity=events,
            is_mock=True,
        )
