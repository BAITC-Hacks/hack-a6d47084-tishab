import os
import tempfile
from pathlib import Path

TEST_DIRECTORY = Path(tempfile.mkdtemp(prefix="windline-tests-"))
os.environ["DATABASE_URL"] = f"sqlite:///{(TEST_DIRECTORY / 'test.db').as_posix()}"
os.environ["FORECAST_PROVIDER"] = "mock"
os.environ["WEATHER_PROVIDER"] = "mock"
os.environ["AGENT_PROVIDER"] = "mock"

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def issue_time():
    return "2026-02-10T06:00:00Z"


def run_scenario(client: TestClient, issue_time: str, scenario: str):
    response = client.post(
        "/api/forecasts/run",
        json={"issue_time": issue_time, "horizon_hours": 24, "scenario": scenario},
    )
    assert response.status_code == 201, response.text
    return response.json()
