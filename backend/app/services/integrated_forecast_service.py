"""Bridge the M1/M2 runtime into the existing M3 HTTP/SQLite contract.

The agent runs offline against committed weather cache. Only LLM briefing can
make an external call, and only when INTEGRATED_LLM=on is explicitly configured.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from threading import Lock

from app.config import Settings
from app.db.repository import ForecastRepository
from app.integrations.errors import ProviderUnavailableError
from app.schemas.agent import AgentResult
from app.schemas.common import AgentEvent
from app.schemas.forecast import ForecastDetail, ForecastPoint, LineageEntry, ModelDescriptor, Provenance, RevisionDecision
from app.schemas.weather import KnowledgeBoundary, WeatherContext, WeatherPoint

ROOT = Path(__file__).resolve().parents[3]
# Supports both "uvicorn app.main:app" from backend/ and --app-dir backend.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_RUNTIME_LOCK = Lock()  # The upstream parquet Store is single-writer: use one API worker.


def web_id(source_id: str, llm_mode: str = "off") -> str:
    return "F-" + hashlib.sha256(f"{llm_mode}:{source_id}".encode()).hexdigest()[:16].upper()


class IntegratedForecastService:
    def __init__(self, repository: ForecastRepository, settings: Settings):
        self.repository = repository
        self.settings = settings

    def run(self, request) -> ForecastDetail:
        try:
            import pandas as pd
            from ai.agent.predictors import M1Predictor, failure_message
            from ai.agent.provenance import Store
            from ai.agent.run import run_issue
            from ai.weather.client import fetch_run
        except ImportError as exc:
            raise ProviderUnavailableError(
                "ML dependencies unavailable. Install requirements.txt from the repository root."
            ) from exc

        class CaptureStore(Store):
            def __init__(self, root):
                super().__init__(root)
                self.events = []

            def log(self, issue, step, status, details):
                super().log(issue, step, status, details)
                mapped = ("failed" if status in ("failed", "rejected", "REJECT") else
                          "warning" if status in ("unavailable", "SHADOW") else "info")
                self.events.append(AgentEvent(
                    timestamp=datetime.now(timezone.utc), type=step, status=mapped,
                    message=json.dumps(details, ensure_ascii=False, allow_nan=False),
                ))

        weather_frame = None

        def fetch(run):
            nonlocal weather_frame
            weather_frame = fetch_run(run, offline=True)
            return weather_frame

        with _RUNTIME_LOCK:
            try:
                # Separate LLM-off/on stores prevent reuse of an old template when LLM is enabled.
                store = CaptureStore(self.settings.integrated_output_dir / self.settings.integrated_llm)
                predictor = M1Predictor(directory=ROOT)
                receipt = run_issue(request.issue_time, predictor, store, offline=True,
                                    llm_mode=self.settings.integrated_llm, fetch=fetch)
                identifier = web_id(receipt["forecast_id"], self.settings.integrated_llm)
                try:
                    return self.repository.get(identifier)
                except KeyError:
                    pass

                points = []
                if receipt["decision"] != "REJECT" and store.path.exists():
                    table = pd.read_parquet(store.path)
                    table = table[table.forecast_id.eq(receipt["forecast_id"])]
                    for row in table.sort_values(["forecast_time", "turbine_id"]).itertuples():
                        points.append(ForecastPoint(
                            forecast_time=row.forecast_time.to_pydatetime(),
                            lead_hours=int((row.forecast_time - pd.Timestamp(request.issue_time)).total_seconds() / 3600),
                            turbine_id=str(row.turbine_id), p50=float(row.p50),
                            model_predictions={"lightgbm": float(row.p50)},
                        ))

                # On idempotent reuse by another DB, weather can be reconstructed from receipt metadata.
                if weather_frame is None and receipt.get("run_init_time") and receipt["decision"] != "REJECT":
                    from ai.weather.vintage import WeatherRun
                    weather_frame = fetch_run(WeatherRun.from_init(pd.Timestamp(receipt["run_init_time"])), offline=True)
                hourly = []
                if weather_frame is not None and receipt["decision"] != "REJECT":
                    for stamp, row in weather_frame.iterrows():
                        if request.issue_time < stamp <= pd.Timestamp(request.issue_time) + pd.Timedelta(hours=48):
                            def value(key):
                                item = row.get(key)
                                return float(item) if pd.notna(item) else None
                            hourly.append(WeatherPoint(
                                timestamp=stamp.to_pydatetime(), wind_10m=value("wind_speed_10m"),
                                wind_80m=value("wind_speed_80m"), wind_100m=value("wind_speed_100m"),
                                wind_120m=value("wind_speed_120m"), wind_direction=value("wind_direction_100m"),
                                temperature=value("temperature_2m"), pressure=value("surface_pressure"),
                            ))
                errors = receipt.get("errors", [])
                boundary = KnowledgeBoundary(
                    issue_time=request.issue_time, weather_available_time=receipt.get("available_at"),
                    status="failed" if errors else "pass",
                    future_information_used=bool({"future_weather", "model_cutoff_after_issue"} & set(errors)),
                    reason="; ".join(errors) or None,
                )
                weather = WeatherContext(
                    weather_source="Open-Meteo Single Runs · ECMWF IFS (cached)",
                    weather_run_id=receipt.get("weather_run_id"), forecast_run_time=receipt.get("run_init_time"),
                    forecast_available_time=receipt.get("available_at"), issue_time=request.issue_time,
                    hourly=hourly, knowledge_boundary=boundary,
                )
                briefing = receipt.get("briefing", {})
                agent = AgentResult(
                    status="completed", summary=receipt["decision"], decision=receipt["decision"],
                    warnings=receipt.get("validation", {}).get("weather", {}).get("warnings", []) +
                             receipt.get("validation", {}).get("forecast", {}).get("warnings", []),
                    operator_message=briefing.get("text"), llm_used=briefing.get("llm_used", False),
                    briefing_reason=briefing.get("reason"), fallback=None if briefing.get("llm_used") else "template",
                    activity=store.events,
                )
                now = datetime.now(timezone.utc)
                lineage, current, seen = [], receipt, set()
                while current and current["forecast_id"] not in seen:
                    seen.add(current["forecast_id"])
                    lineage.append(LineageEntry(
                        forecast_id=web_id(current["forecast_id"], self.settings.integrated_llm), version=current["version"],
                        issue_time=current["issue_time"], status=current["status"],
                        revision_reason=current["reason"], created_at=now,
                    ))
                    parent = current.get("parent_forecast_id")
                    parent_path = store.root / "receipts" / f"{parent}.json" if parent else None
                    current = json.loads(parent_path.read_text(encoding="utf-8")) if parent_path and parent_path.exists() else None
                lineage.reverse()
                provenance = Provenance(
                    forecast_id=identifier, source_forecast_id=receipt["forecast_id"],
                    issue_time=request.issue_time, weather_run_id=weather.weather_run_id,
                    weather_source=weather.weather_source, forecast_run_time=weather.forecast_run_time,
                    forecast_available_time=weather.forecast_available_time,
                    availability_basis=receipt.get("availability_basis"), model_cutoff=receipt.get("model_cutoff"),
                    model_name="lightgbm", model_version=receipt["model_version"],
                    feature_version=getattr(predictor, "feature_version", None), forecast_version=receipt["version"],
                    future_information_used=boundary.future_information_used, integrity_status=boundary.status,
                    uncertainty_available=False,
                )
                detail = ForecastDetail(
                    forecast_id=identifier, issue_time=request.issue_time, horizon_hours=48,
                    version=receipt["version"], status=receipt["status"], model_name="lightgbm",
                    integrity_status=boundary.status, created_at=now, is_mock=False,
                    points=points, models=[ModelDescriptor(name="lightgbm", type="ml")],
                    weather=weather, knowledge_boundary=boundary, provenance=provenance,
                    agent=agent, events=store.events, lineage=lineage,
                    revision=RevisionDecision(
                        previous_version=lineage[-2].version if len(lineage) > 1 else None,
                        candidate_version=receipt["version"], decision=receipt["decision"], reason=receipt["reason"],
                        metrics={"energy_change_pct": receipt.get("energy_change_pct")},
                    ),
                )
                return self.repository.save(detail)
            except (ImportError, OSError, ValueError, KeyError) as exc:
                raise ProviderUnavailableError("Integrated pipeline unavailable: " + failure_message(exc)) from exc
