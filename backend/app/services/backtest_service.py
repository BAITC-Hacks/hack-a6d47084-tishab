import json
from pathlib import Path

from app.db.repository import ForecastRepository
from app.schemas.backtest import BacktestModelResult, BacktestPeriod, BacktestResult


class BacktestService:
    def __init__(self, repository: ForecastRepository):
        self.repository = repository

    def latest(self) -> BacktestResult:
        existing = self.repository.latest_backtest()
        if existing:
            return existing
        # Preserve per-turbine/per-horizon results; do not invent an aggregate
        # score or present the power-curve holdout as a LightGBM evaluation.
        report = Path(__file__).resolve().parents[3] / "data/processed/power_curve_eval.json"
        if report.exists():
            payload = json.loads(report.read_text(encoding="utf-8"))
            return BacktestResult(
                period=BacktestPeriod(start=payload.get("cutoff")),
                models=[BacktestModelResult(
                    name=f"{row['method']} · {row['turbine_id']} · {row['lead_bucket_h']}h (n={row['n']})",
                    mae=row["mae"], rmse=row["rmse"],
                ) for row in payload["metrics"]],
                status="available",
                message="Saved January 2026 holdout: power curve and persistence, not LightGBM or the organizer metric. nMAE and chart series are not supplied.",
            )
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
