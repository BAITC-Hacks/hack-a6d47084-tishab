from fastapi import APIRouter, Depends

from app.dependencies import get_backtest_service
from app.schemas.backtest import BacktestResult
from app.services.backtest_service import BacktestService

router = APIRouter(prefix="/backtests", tags=["backtests"])


@router.get(
    "/latest",
    response_model=BacktestResult,
    summary="Get the latest integrated backtest",
    description="Returns team-provided evaluation data or an explicit N/A mock placeholder.",
)
def latest_backtest(service: BacktestService = Depends(get_backtest_service)) -> BacktestResult:
    return service.latest()
