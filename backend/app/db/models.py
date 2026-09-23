from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ForecastRun(Base):
    __tablename__ = "forecast_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    issue_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    horizon_hours: Mapped[int] = mapped_column(Integer)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(32), index=True)
    confidence: Mapped[str | None] = mapped_column(String(32), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    integrity_status: Mapped[str] = mapped_column(String(32))
    is_mock: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    weather_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    boundary_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    provenance_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    agent_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    models_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    lineage_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    revision_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    points: Mapped[list["ForecastPoint"]] = relationship(
        cascade="all, delete-orphan", back_populates="run", order_by="ForecastPoint.id"
    )
    events: Mapped[list["AgentEvent"]] = relationship(
        cascade="all, delete-orphan", back_populates="run", order_by="AgentEvent.id"
    )


class ForecastPoint(Base):
    __tablename__ = "forecast_points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    forecast_id: Mapped[str] = mapped_column(ForeignKey("forecast_runs.id"), index=True)
    turbine_id: Mapped[str] = mapped_column(String(32), index=True)
    forecast_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    lead_hours: Mapped[int] = mapped_column(Integer)
    p10: Mapped[float] = mapped_column(Float)
    p50: Mapped[float] = mapped_column(Float)
    p90: Mapped[float] = mapped_column(Float)
    model_predictions: Mapped[dict[str, float]] = mapped_column(JSON)

    run: Mapped[ForecastRun] = relationship(back_populates="points")


class AgentEvent(Base):
    __tablename__ = "agent_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    forecast_id: Mapped[str] = mapped_column(ForeignKey("forecast_runs.id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    type: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32))
    message: Mapped[str] = mapped_column(Text)

    run: Mapped[ForecastRun] = relationship(back_populates="events")


class BacktestResult(Base):
    __tablename__ = "backtest_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
