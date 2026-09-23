from app.config import Settings
from app.integrations.agent.base import AgentProvider
from app.integrations.agent.mock import MockAgentProvider
from app.integrations.agent.real import RealAgentProvider
from app.integrations.forecast.base import ForecastProvider
from app.integrations.forecast.mock import MockForecastProvider
from app.integrations.forecast.real import RealForecastProvider
from app.integrations.weather.base import WeatherProvider
from app.integrations.weather.mock import MockWeatherProvider
from app.integrations.weather.real import RealWeatherProvider


def build_forecast_provider(settings: Settings) -> ForecastProvider:
    return MockForecastProvider() if settings.forecast_provider == "mock" else RealForecastProvider()


def build_weather_provider(settings: Settings) -> WeatherProvider:
    return MockWeatherProvider() if settings.weather_provider == "mock" else RealWeatherProvider()


def build_agent_provider(settings: Settings) -> AgentProvider:
    return MockAgentProvider() if settings.agent_provider == "mock" else RealAgentProvider()
