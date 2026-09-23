from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.schemas.agent import AgentResult
from app.schemas.backtest import BacktestResult as BacktestSchema
from app.schemas.common import AgentEvent as AgentEventSchema
from app.schemas.forecast import (
    ForecastDetail,
    ForecastPoint as ForecastPointSchema,
    ForecastRunSummary,
    LineageEntry,
    ModelDescriptor,
    Provenance,
    RevisionDecision,
)
from app.schemas.weather import KnowledgeBoundary, WeatherContext

from .models import AgentEvent, BacktestResult, ForecastPoint, ForecastRun


class ForecastRepository:
    def __init__(self, db: Session):
        self.db = db

    def save(self, detail: ForecastDetail) -> ForecastDetail:
        run = ForecastRun(
            id=detail.forecast_id,
            issue_time=detail.issue_time,
            horizon_hours=detail.horizon_hours,
            version=detail.version,
            status=detail.status.value,
            confidence=detail.confidence,
            model_name=detail.model_name,
            integrity_status=detail.integrity_status.value,
            is_mock=detail.is_mock,
            created_at=detail.created_at,
            weather_json=detail.weather.model_dump(mode="json") if detail.weather else None,
            boundary_json=detail.knowledge_boundary.model_dump(mode="json"),
            provenance_json=detail.provenance.model_dump(mode="json"),
            agent_json=detail.agent.model_dump(mode="json"),
            models_json=[model.model_dump(mode="json") for model in detail.models],
            lineage_json=[entry.model_dump(mode="json") for entry in detail.lineage],
            revision_json=detail.revision.model_dump(mode="json") if detail.revision else None,
        )
        run.points = [
            ForecastPoint(
                turbine_id=point.turbine_id,
                forecast_time=point.forecast_time,
                lead_hours=point.lead_hours,
                p10=point.p10,
                p50=point.p50,
                p90=point.p90,
                model_predictions=point.model_predictions,
            )
            for point in detail.points
        ]
        run.events = [
            AgentEvent(
                timestamp=event.timestamp,
                type=event.type,
                status=event.status.value,
                message=event.message,
            )
            for event in detail.events
        ]
        self.db.add(run)
        self.db.commit()
        return self.get(detail.forecast_id)

    def get(self, forecast_id: str) -> ForecastDetail:
        statement = (
            select(ForecastRun)
            .where(ForecastRun.id == forecast_id)
            .options(selectinload(ForecastRun.points), selectinload(ForecastRun.events))
        )
        run = self.db.scalar(statement)
        if run is None:
            raise KeyError(forecast_id)
        return self._to_detail(run)

    def list(self) -> list[ForecastRunSummary]:
        runs = self.db.scalars(select(ForecastRun).order_by(ForecastRun.created_at.desc())).all()
        return [self._to_summary(run) for run in runs]

    def latest_backtest(self) -> BacktestSchema | None:
        result = self.db.scalar(select(BacktestResult).order_by(BacktestResult.created_at.desc()).limit(1))
        return BacktestSchema.model_validate(result.payload) if result else None

    def save_backtest(self, result: BacktestSchema) -> BacktestSchema:
        self.db.add(BacktestResult(payload=result.model_dump(mode="json")))
        self.db.commit()
        return result

    @staticmethod
    def _to_summary(run: ForecastRun) -> ForecastRunSummary:
        return ForecastRunSummary(
            forecast_id=run.id,
            issue_time=run.issue_time,
            horizon_hours=run.horizon_hours,
            version=run.version,
            status=run.status,
            confidence=run.confidence,
            model_name=run.model_name,
            integrity_status=run.integrity_status,
            created_at=run.created_at,
            is_mock=run.is_mock,
        )

    def _to_detail(self, run: ForecastRun) -> ForecastDetail:
        return ForecastDetail(
            **self._to_summary(run).model_dump(),
            points=[
                ForecastPointSchema(
                    forecast_time=point.forecast_time,
                    lead_hours=point.lead_hours,
                    turbine_id=point.turbine_id,
                    p10=point.p10,
                    p50=point.p50,
                    p90=point.p90,
                    model_predictions=point.model_predictions,
                )
                for point in run.points
            ],
            models=[ModelDescriptor.model_validate(item) for item in run.models_json],
            weather=WeatherContext.model_validate(run.weather_json) if run.weather_json else None,
            knowledge_boundary=KnowledgeBoundary.model_validate(run.boundary_json),
            provenance=Provenance.model_validate(run.provenance_json),
            agent=AgentResult.model_validate(run.agent_json),
            events=[
                AgentEventSchema(
                    timestamp=event.timestamp,
                    type=event.type,
                    status=event.status,
                    message=event.message,
                )
                for event in run.events
            ],
            lineage=[LineageEntry.model_validate(item) for item in run.lineage_json],
            revision=RevisionDecision.model_validate(run.revision_json) if run.revision_json else None,
        )
