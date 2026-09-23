from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Vintage-Aware Wind Forecast API"
    app_env: str = "development"
    database_url: str = "sqlite:///./wind_forecasts.db"
    cors_origins: list[str] = ["http://localhost:5173"]
    forecast_provider: Literal["mock", "real"] = "mock"
    weather_provider: Literal["mock", "real"] = "mock"
    agent_provider: Literal["mock", "real"] = "mock"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: object) -> object:
        if isinstance(value, str) and not value.lstrip().startswith("["):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
