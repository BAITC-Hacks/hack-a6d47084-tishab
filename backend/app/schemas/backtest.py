from datetime import datetime

from pydantic import Field

from .common import StrictModel


class BacktestPeriod(StrictModel):
    start: datetime | None = None
    end: datetime | None = None


class BacktestModelResult(StrictModel):
    name: str
    mae: float | None = None
    rmse: float | None = None
    nmae: float | None = None


class BacktestPoint(StrictModel):
    timestamp: datetime
    actual: float | None = None
    forecast: float | None = None


class BacktestResult(StrictModel):
    period: BacktestPeriod
    models: list[BacktestModelResult] = Field(default_factory=list)
    series: list[BacktestPoint] = Field(default_factory=list)
    status: str
    message: str | None = None
    is_mock: bool = False
