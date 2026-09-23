"""Open-Meteo Single Runs client with an offline-first raw-response cache."""

from __future__ import annotations

import hashlib
import json
import random
import time
from email.utils import parsedate_to_datetime
from pathlib import Path

import pandas as pd
import requests

from ai import config
from ai.weather.vintage import WeatherRun


class RunUnavailable(LookupError):
    """The archive has no data for this run."""


class DownloadError(RuntimeError):
    """The API failed to return a run; archive availability is unknown."""


def _params(run: WeatherRun) -> dict:
    return {
        "latitude": config.SITE_LAT,
        "longitude": config.SITE_LON,
        "models": run.model,
        "run": f"{run.init_time:%Y-%m-%dT%H:%M}",
        "hourly": ",".join(config.WEATHER_VARIABLES),
        "forecast_hours": config.RUN_FORECAST_HOURS,
        "wind_speed_unit": "ms",
        "timezone": "GMT",
    }


def cache_path(run: WeatherRun, cache_dir: Path = config.CACHE_DIR) -> Path:
    # The key covers everything that changes the response: API, model, run, point, variables.
    key = json.dumps(_params(run), sort_keys=True)
    digest = hashlib.sha256(f"{config.WEATHER_API_URL}|{key}".encode()).hexdigest()[:12]
    return cache_dir / "raw" / run.model / f"{run.init_time:%Y%m%dT%H}Z_{digest}.json"


def fetch_run(run: WeatherRun, cache_dir: Path = config.CACHE_DIR, offline: bool = False) -> pd.DataFrame:
    """Hourly forecast indexed by UTC time; raises RunUnavailable or DownloadError."""
    path = cache_path(run, cache_dir)
    if path.exists():
        record = json.loads(path.read_text())
    elif offline:
        raise RunUnavailable(f"{run.run_id} not in cache and offline mode is on")
    else:
        record = _download(run)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record))

    if record["status"] != "ok":
        raise RunUnavailable(f"{run.run_id}: {record['reason']}")
    return _to_frame(record["response"])


def _retry_delay(attempt: int, retry_after: str | None = None) -> float:
    if retry_after is not None:
        try:
            return max(0.0, float(retry_after))
        except ValueError:
            try:
                deadline = pd.Timestamp(parsedate_to_datetime(retry_after))
                return max(0.0, (deadline - pd.Timestamp.now(tz="UTC")).total_seconds())
            except (TypeError, ValueError, OverflowError):
                pass
    return min(60, 2 ** attempt * 2) + random.uniform(0, 0.5)


def _download(run: WeatherRun, retries: int = 6) -> dict:
    params = _params(run)
    failure = "no attempts made"
    for attempt in range(retries):
        retry_after = None
        try:
            resp = requests.get(config.WEATHER_API_URL, params=params, timeout=30)
        except requests.RequestException as exc:
            failure = type(exc).__name__
        else:
            if resp.status_code != 429 and resp.status_code < 500:
                break
            failure = f"HTTP {resp.status_code}"
            retry_after = resp.headers.get("Retry-After")
        if attempt < retries - 1:
            time.sleep(_retry_delay(attempt, retry_after))
    else:
        raise DownloadError(f"{run.run_id}: API failed after {retries} attempts ({failure})")

    try:
        body = resp.json()
        if resp.status_code >= 400 and not body.get("error"):
            raise DownloadError(f"{run.run_id}: HTTP {resp.status_code}")
        meta = {
            "url": config.WEATHER_API_URL,
            "params": params,
            "retrieved_at": pd.Timestamp.now(tz="UTC").isoformat(),
            "sha256": hashlib.sha256(resp.content).hexdigest(),
        }
        if body.get("error"):
            # Cache "not available" answers too, so the replay is reproducible offline.
            return {"status": "unavailable", "reason": body.get("reason", ""), "meta": meta}
        return {"status": "ok", "response": body, "meta": meta}
    except ValueError as exc:
        raise DownloadError(f"{run.run_id}: invalid JSON response") from exc


def _to_frame(response: dict) -> pd.DataFrame:
    hourly = response["hourly"]
    df = pd.DataFrame({v: hourly[v] for v in config.WEATHER_VARIABLES}, dtype="float64")
    df.index = pd.to_datetime(hourly["time"]).tz_localize("UTC")
    df.index.name = "forecast_time"
    return df
