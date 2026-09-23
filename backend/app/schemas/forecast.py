from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import Field, field_validator

from .agent import AgentResult
from .common import AgentEvent, IntegrityStatus, RunStatus, StrictModel
from .weather import KnowledgeBoundary, WeatherContext


class MockScenario(str, Enum):
    normal = "normal"
    baselines = "baselines"
    revision = "revision"
    leakage = "leakage"
    agent_off = "agent_off"
    optional_models = "optional_models"


class ForecastRequest(StrictModel):
    issue_time: datetime
    horizon_hours: Literal[24, 48] = 48
    scenario: MockScenario = MockScenario.normal

    @field_validator("issue_time")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("issue_time must include a timezone")
        return value


class ForecastPoint(StrictModel):
    forecast_time: datetime
    lead_hours: int = Field(ge=1)
    turbine_id: str
    p10: float = Field(ge=0, le=2)
    p50: float = Field(ge=0, le=2)
    p90: float = Field(ge=0, le=2)
    model_predictions: dict[str, float] = Field(default_factory=dict)


class ModelDescriptor(StrictModel):
    name: str
    type: str


class Provenance(StrictModel):
    forecast_id: str
    issue_time: datetime
    weather_run_id: str | None = None
    weather_source: str | None = None
    forecast_run_time: datetime | None = None
    forecast_available_time: datetime | None = None
    model_name: str | None = None
    model_version: str | None = None
    feature_version: str | None = None
    forecast_version: int = 1
    future_information_used: bool = False
    integrity_status: IntegrityStatus = IntegrityStatus.unknown
    is_mock: bool = False


class LineageEntry(StrictModel):
    forecast_id: str
    version: int
    parent_version: int | None = None
    issue_time: datetime
    status: RunStatus
    revision_reason: str | None = None
    created_at: datetime


class RevisionDecision(StrictModel):
    previous_version: int | None = None
    candidate_version: int
    decision: str
    reason: str | None = None
    metrics: dict[str, float | None] = Field(default_factory=dict)


class ForecastProviderResult(StrictModel):
    status: RunStatus
    version: int = 1
    points: list[ForecastPoint]
    models: list[ModelDescriptor]
    model_name: str | None = None
    model_version: str | None = None
    feature_version: str | None = None
    lineage: list[LineageEntry] = Field(default_factory=list)
    revision: RevisionDecision | None = None
    is_mock: bool = False


class ForecastRunSummary(StrictModel):
    forecast_id: str
    issue_time: datetime
    horizon_hours: int
    version: int
    status: RunStatus
    confidence: str | None = None
    model_name: str | None = None
    integrity_status: IntegrityStatus
    created_at: datetime
    is_mock: bool


class ForecastDetail(ForecastRunSummary):
    points: list[ForecastPoint]
    models: list[ModelDescriptor]
    weather: WeatherContext | None = None
    knowledge_boundary: KnowledgeBoundary
    provenance: Provenance
    agent: AgentResult
    events: list[AgentEvent]
    lineage: list[LineageEntry]
    revision: RevisionDecision | None = None
