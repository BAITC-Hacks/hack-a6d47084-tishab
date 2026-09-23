import math
from datetime import datetime, timedelta

from app.schemas.common import RunStatus
from app.schemas.forecast import (
    ForecastPoint,
    ForecastProviderResult,
    LineageEntry,
    MockScenario,
    ModelDescriptor,
    RevisionDecision,
)

from .base import ForecastProvider


class MockForecastProvider(ForecastProvider):
    """Deterministic demo fixture. Values are synthetic and never model output."""

    def run_forecast(
        self,
        issue_time: datetime,
        horizon_hours: int,
        scenario: MockScenario = MockScenario.normal,
    ) -> ForecastProviderResult:
        model_names = ["lightgbm"]
        if scenario in {MockScenario.baselines, MockScenario.revision}:
            model_names = ["persistence", "power_curve", "lightgbm"]
        elif scenario == MockScenario.optional_models:
            model_names = ["persistence", "power_curve", "lightgbm", "tft", "ensemble"]

        model_types = {
            "persistence": "baseline",
            "climatology": "baseline",
            "power_curve": "baseline",
            "lightgbm": "primary",
            "tft": "optional",
            "ensemble": "optional",
        }
        points: list[ForecastPoint] = []
        for turbine_id, offset in (("PLANT", 0.17), ("T1", 0.0), ("T2", 0.03)):
            scale = 1.75 if turbine_id == "PLANT" else 0.9
            for lead in range(1, horizon_hours + 1):
                base = 0.48 + 0.18 * math.sin((lead + 3) / 5) + offset
                p50 = max(0.03, min(scale, base * scale))
                spread = 0.09 + 0.025 * abs(math.sin(lead / 4))
                predictions = {
                    name: round(max(0.0, min(scale, p50 + (index - len(model_names) / 2) * 0.018)), 3)
                    for index, name in enumerate(model_names)
                }
                points.append(
                    ForecastPoint(
                        forecast_time=issue_time + timedelta(hours=lead),
                        lead_hours=lead,
                        turbine_id=turbine_id,
                        p10=round(max(0.0, p50 - spread), 3),
                        p50=round(p50, 3),
                        p90=round(min(2.0, p50 + spread), 3),
                        model_predictions=predictions,
                    )
                )

        version = 2 if scenario == MockScenario.revision else 1
        status = RunStatus.rejected if scenario == MockScenario.leakage else RunStatus.published
        now = issue_time + timedelta(seconds=4)
        lineage = [
            LineageEntry(
                forecast_id="pending",
                version=1,
                issue_time=issue_time,
                status=RunStatus.superseded if version == 2 else status,
                revision_reason="Initial mock forecast",
                created_at=now,
            )
        ]
        revision = None
        if version == 2:
            lineage.append(
                LineageEntry(
                    forecast_id="pending",
                    version=2,
                    parent_version=1,
                    issue_time=issue_time,
                    status=RunStatus.published,
                    revision_reason="Mock weather update for lineage demonstration",
                    created_at=now + timedelta(minutes=30),
                )
            )
            revision = RevisionDecision(
                previous_version=1,
                candidate_version=2,
                decision="publish_revision",
                reason="Demo scenario: a team module requested publication",
            )

        return ForecastProviderResult(
            status=status,
            version=version,
            points=points,
            models=[ModelDescriptor(name=name, type=model_types[name]) for name in model_names],
            model_name="mock-forecast-provider",
            model_version="demo-1",
            feature_version="demo-features-1",
            lineage=lineage,
            revision=revision,
            is_mock=True,
        )
