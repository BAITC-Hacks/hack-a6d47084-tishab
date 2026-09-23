import json
from pathlib import Path
import subprocess
import sys

import pandas as pd
import pytest

from app.config import Settings, get_settings
from app.main import app

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def integrated_settings(tmp_path):
    settings = Settings(integrated_output_dir=tmp_path / "runs", integrated_llm="off")
    app.dependency_overrides[get_settings] = lambda: settings
    yield settings
    app.dependency_overrides.pop(get_settings, None)


def test_handoff_matches_api_and_survives_storage(client, integrated_settings, tmp_path):
    output = tmp_path / "handoff.csv"
    subprocess.run([
        sys.executable, "scripts/predict.py", "--weather", "data/processed/weather_vintages.parquet",
        "--issue-time", "2026-02-10T07:00:00Z", "--output", str(output),
    ], cwd=ROOT, check=True, capture_output=True)
    expected = pd.read_csv(output)
    payload = {"mode": "integrated", "issue_time": "2026-02-10T07:00:00Z", "horizon_hours": 48}
    response = client.post("/api/forecasts/run", json=payload)
    assert response.status_code == 201, response.text
    result = response.json()
    assert result["status"] == "published"
    assert result["is_mock"] is False
    assert result["provenance"]["uncertainty_available"] is False
    assert result["provenance"]["model_version"] == "m1-lgbm-weather-only-v1"
    assert result["provenance"]["availability_basis"] == "assumed:init+7h"
    assert result["knowledge_boundary"]["future_information_used"] is False
    assert result["agent"]["llm_used"] is False
    assert result["agent"]["briefing_reason"] == "llm_off"
    assert len(result["points"]) == len(expected) == 96
    assert {point["turbine_id"] for point in result["points"]} == {"T1", "T2"}
    actual = pd.DataFrame(result["points"]).sort_values(["turbine_id", "lead_hours"])
    expected = expected.sort_values(["turbine_id", "lead_time"])
    assert actual.p50.to_list() == pytest.approx(expected.prediction.to_list(), abs=1e-12)
    assert all(point["p10"] is None and point["p90"] is None for point in result["points"])
    assert pd.Timestamp(result["issue_time"]) == pd.Timestamp("2026-02-10T07:00Z")
    assert pd.Timestamp(result["points"][0]["forecast_time"]) == pd.Timestamp("2026-02-10T08:00Z")
    assert len(result["weather"]["hourly"]) == 48
    assert client.get(f"/api/forecasts/{result['forecast_id']}").json() == result
    assert client.post("/api/forecasts/run", json=payload).json()["forecast_id"] == result["forecast_id"]


@pytest.mark.parametrize("extra", [
    {"horizon_hours": 24}, {"scenario": "leakage"}, {"issue_time": "2026-02-10T07:15:00Z"},
])
def test_integrated_rejects_unsupported_inputs(client, integrated_settings, extra):
    payload = {"mode": "integrated", "issue_time": "2026-02-10T07:00:00Z", "horizon_hours": 48, **extra}
    assert client.post("/api/forecasts/run", json=payload).status_code == 422


@pytest.mark.parametrize("issue,reason", [
    ("2025-11-01T07:00:00Z", "model_cutoff_after_issue"),
    ("2030-01-01T07:00:00Z", "no_legal_weather"),
])
def test_integrated_rejection_has_no_invented_points(client, integrated_settings, issue, reason):
    response = client.post("/api/forecasts/run", json={"mode": "integrated", "issue_time": issue})
    assert response.status_code == 201, response.text
    result = response.json()
    assert result["status"] == "rejected"
    assert result["points"] == []
    assert reason in result["knowledge_boundary"]["reason"]


def test_real_leakage_guard_runs_before_prediction(tmp_path):
    from ai.agent.provenance import Store
    from ai.agent.run import run_issue

    class NeverPredict:
        model_version = "test"
        cutoff = pd.Timestamp("2025-01-01T00:00Z")

        def predict(self, weather):
            pytest.fail("Future weather must be rejected before model inference")

    receipt = run_issue("2026-02-10T07:00Z", NeverPredict(), Store(tmp_path),
                        offline=True, llm_mode="off", force_run="2026-02-10T06:00Z")
    assert receipt["decision"] == "REJECT"
    assert receipt["errors"] == ["future_weather"]


def test_llm_fallback_and_grounding_without_network(monkeypatch):
    from ai.agent import llm
    import dotenv
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    facts = {"issue_time": "2026-02-10T07:00:00Z", "decision": "PUBLISH", "reason": "first_publication"}
    assert llm.brief(facts, "off")["reason"] == "llm_off"
    assert llm.brief(facts, "on")["reason"] == "missing_api_key"
    monkeypatch.setenv("OPENAI_API_KEY", "test-placeholder")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    monkeypatch.setattr(llm, "_request", lambda *args: "Прогноз принят к публикации.")
    assert llm.brief(facts, "on")["llm_used"] is True
    monkeypatch.setattr(llm, "_request", lambda *args: "Мощность составит 99999.")
    rejected = llm.brief(facts, "on")
    assert rejected["llm_used"] is False
    assert rejected["reason"] == "grounding_guard_failed"


def test_backtest_uses_saved_metrics_without_inventing_scores(client):
    report = json.loads((ROOT / "data/processed/power_curve_eval.json").read_text(encoding="utf-8"))
    result = client.get("/api/backtests/latest").json()
    assert result["is_mock"] is False
    assert len(result["models"]) == len(report["metrics"])
    assert result["models"][0]["mae"] == report["metrics"][0]["mae"]
    assert all(row["nmae"] is None for row in result["models"])
    assert result["series"] == []
