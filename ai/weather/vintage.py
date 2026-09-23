"""Publication-aware selection of weather runs (knowledge boundary)."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ai import config


class LeakageError(RuntimeError):
    """A weather run that was not yet available at the issue time was about to be used."""


@dataclass(frozen=True)
class WeatherRun:
    model: str
    init_time: pd.Timestamp
    available_at: pd.Timestamp
    availability_basis: str

    @classmethod
    def from_init(cls, init_time: pd.Timestamp, model: str = config.WEATHER_MODEL) -> "WeatherRun":
        init_time = to_utc(init_time)
        return cls(
            model=model,
            init_time=init_time,
            available_at=init_time + config.AVAILABILITY_DELAY,
            availability_basis=config.AVAILABILITY_BASIS,
        )

    @property
    def run_id(self) -> str:
        return f"{self.model}:{self.init_time:%Y-%m-%dT%H}Z"


def to_utc(ts) -> pd.Timestamp:
    ts = pd.Timestamp(ts)
    if ts.tzinfo is None:
        raise ValueError(f"naive timestamp {ts}: all times must be timezone-aware UTC")
    return ts.tz_convert("UTC")


def assert_legal(run: WeatherRun, issue_time) -> None:
    issue_time = to_utc(issue_time)
    if run.available_at > issue_time:
        raise LeakageError(
            f"weather run {run.run_id} available_at={run.available_at.isoformat()} "
            f"> issue_time={issue_time.isoformat()}: future information rejected"
        )


def legal_runs(issue_time, max_age: pd.Timedelta = pd.Timedelta(hours=24)) -> list[WeatherRun]:
    """Runs usable at issue_time, newest first, not older than max_age before issue_time."""
    issue_time = to_utc(issue_time)
    latest_init = (issue_time - config.AVAILABILITY_DELAY).floor("6h")
    runs = []
    init = latest_init
    while init >= issue_time - max_age and init >= config.FIRST_AVAILABLE_RUN:
        run = WeatherRun.from_init(init)
        assert_legal(run, issue_time)
        runs.append(run)
        init -= pd.Timedelta(hours=6)
    return runs


def select_legal_run(issue_time) -> WeatherRun:
    runs = legal_runs(issue_time)
    if not runs:
        raise LookupError(f"no archived weather run is legal at {to_utc(issue_time).isoformat()}")
    return runs[0]
