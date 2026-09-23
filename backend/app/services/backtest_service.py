from app.db.repository import ForecastRepository
from app.schemas.backtest import BacktestModelResult, BacktestPeriod, BacktestResult


class BacktestService:
    def __init__(self, repository: ForecastRepository):
        self.repository = repository

    def latest(self) -> BacktestResult:
        existing = self.repository.latest_backtest()
        if existing:
            return existing
        return BacktestResult(
            period=BacktestPeriod(),
            models=[
                BacktestModelResult(name="Persistence"),
                BacktestModelResult(name="Power Curve"),
                BacktestModelResult(name="LightGBM"),
            ],
            status="unavailable",
            message="No team backtest result has been integrated. Metrics are intentionally N/A.",
            is_mock=True,
        )
