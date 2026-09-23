from app.config import Settings
from app.integrations.factory import build_agent_provider, build_forecast_provider, build_weather_provider
from app.integrations.agent.mock import MockAgentProvider
from app.integrations.forecast.mock import MockForecastProvider
from app.integrations.weather.mock import MockWeatherProvider

from conftest import run_scenario


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["providers"] == {"forecast": "mock", "weather": "mock", "agent": "mock"}
    assert client.get("/docs").status_code == 200


def test_forecast_schema_and_dynamic_predictions(client, issue_time):
    forecast = run_scenario(client, issue_time, "baselines")
    assert forecast["is_mock"] is True
    assert forecast["horizon_hours"] == 24
    assert len(forecast["points"]) == 72
    assert set(forecast["points"][0]["model_predictions"]) == {"persistence", "power_curve", "lightgbm"}
    assert forecast["points"][0]["p10"] <= forecast["points"][0]["p50"] <= forecast["points"][0]["p90"]


def test_knowledge_boundary_response(client, issue_time):
    forecast = run_scenario(client, issue_time, "normal")
    boundary = forecast["knowledge_boundary"]
    assert boundary["status"] == "pass"
    assert boundary["future_information_used"] is False
    response = client.get(f"/api/forecasts/{forecast['forecast_id']}/weather")
    assert response.status_code == 200
    assert response.json()["knowledge_boundary"] == boundary


def test_forecast_lineage_response(client, issue_time):
    forecast = run_scenario(client, issue_time, "revision")
    response = client.get(f"/api/forecasts/{forecast['forecast_id']}/lineage")
    assert response.status_code == 200
    assert [item["version"] for item in response.json()] == [1, 2]
    assert forecast["revision"]["decision"] == "publish_revision"


def test_mock_provider_selection():
    settings = Settings(forecast_provider="mock", weather_provider="mock", agent_provider="mock")
    assert isinstance(build_forecast_provider(settings), MockForecastProvider)
    assert isinstance(build_weather_provider(settings), MockWeatherProvider)
    assert isinstance(build_agent_provider(settings), MockAgentProvider)


def test_agent_unavailable_does_not_remove_forecast(client, issue_time):
    forecast = run_scenario(client, issue_time, "agent_off")
    assert forecast["agent"]["status"] == "unavailable"
    assert forecast["agent"]["fallback"] == "deterministic"
    assert forecast["points"]


def test_optional_model_fields_are_serialized(client, issue_time):
    forecast = run_scenario(client, issue_time, "optional_models")
    model_names = {model["name"] for model in forecast["models"]}
    assert {"tft", "ensemble"}.issubset(model_names)
    assert {"tft", "ensemble"}.issubset(forecast["points"][0]["model_predictions"])


def test_leakage_forecast_rejection_serialization(client, issue_time):
    forecast = run_scenario(client, issue_time, "leakage")
    assert forecast["status"] == "rejected"
    assert forecast["integrity_status"] == "failed"
    assert forecast["knowledge_boundary"]["future_information_used"] is True
    assert forecast["agent"]["decision"] == "reject"
