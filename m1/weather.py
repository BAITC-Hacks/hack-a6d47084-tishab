"""Adapter for M2's prepared weather_vintages.parquet handoff.

This module validates and normalizes a table that M2 has already made legal.
It deliberately does not retrieve weather, choose vintages, or interpret when a
run became available.
"""

import hashlib
from pathlib import Path

import pandas as pd

WEATHER_CONTRACT_VERSION = "m2-weather-vintages-v1"

M2_COLUMNS = [
    "issue_time", "forecast_time", "turbine_id", "lead_time_h",
    "weather_run_id", "run_init_time", "available_at", "availability_basis",
    "nwp_lead_h", "wind_speed_10m", "wind_speed_80m", "wind_speed_100m",
    "wind_speed_120m", "wind_direction_100m", "wind_gusts_10m",
    "temperature_2m", "surface_pressure", "relative_humidity_2m",
]
M2_TIMESTAMP_COLUMNS = ["issue_time", "forecast_time", "run_init_time", "available_at"]
M2_WEATHER_ALIASES = {
    "nwp_lead_h": "wx_nwp_lead_h",
    "wind_speed_10m": "wx_wind_10m",
    "wind_speed_80m": "wx_wind_80m",
    "wind_speed_100m": "wx_wind_100m",
    "wind_speed_120m": "wx_wind_120m",
    "wind_direction_100m": "wx_wind_direction",
    "wind_gusts_10m": "wx_gust",
    "temperature_2m": "wx_temperature",
    "surface_pressure": "wx_pressure",
    "relative_humidity_2m": "wx_relative_humidity",
}


def weather_file_sha256(path: str | Path) -> str:
    with Path(path).open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def read_weather_vintages(path: str | Path) -> pd.DataFrame:
    """Read M2's Parquet contract and normalize weather feature names.

    The returned rows are not certified by M1. M2 remains responsible for
    selecting one legal vintage per key and establishing availability metadata.
    """
    source = Path(path)
    if source.suffix.lower() not in {".parquet", ".pq"}:
        raise ValueError("M2 weather input must be weather_vintages.parquet (or .pq)")
    if not source.is_file():
        raise FileNotFoundError(source)
    table = pd.read_parquet(source)
    missing = sorted(set(M2_COLUMNS) - set(table.columns))
    if missing:
        raise ValueError(f"Missing M2 v1 columns in {source.name}: {missing}")
    unexpected = sorted(set(table.columns) - set(M2_COLUMNS))
    if unexpected:
        raise ValueError(f"Unexpected columns in {source.name}: {unexpected}")

    for column in M2_TIMESTAMP_COLUMNS:
        parsed = pd.to_datetime(table[column], errors="raise")
        if not isinstance(parsed.dtype, pd.DatetimeTZDtype):
            raise ValueError(f"{column} must be timezone-aware; M2 v1 timestamps are UTC")
        table[column] = parsed.dt.tz_convert("UTC")

    for column in ("turbine_id", "weather_run_id", "availability_basis"):
        table[column] = table[column].astype("string")
    required_non_null = [
        "issue_time", "forecast_time", "turbine_id", "lead_time_h",
        "weather_run_id", "run_init_time", "available_at", "availability_basis", "nwp_lead_h",
    ]
    if table[required_non_null].isna().any().any():
        raise ValueError("M2 v1 key and provenance fields must not be null")
    if not table["turbine_id"].isin(["T1", "T2"]).all():
        raise ValueError("turbine_id must be T1 or T2")

    numeric = ["lead_time_h", "nwp_lead_h", *[c for c in M2_WEATHER_ALIASES if c != "nwp_lead_h"]]
    for column in numeric:
        table[column] = pd.to_numeric(table[column], errors="raise")
    if not table["lead_time_h"].between(1, 48).all() or not (table["lead_time_h"] % 1 == 0).all():
        raise ValueError("lead_time_h must be an integer in 1..48")
    table["lead_time_h"] = table["lead_time_h"].astype("int8")
    if (table["nwp_lead_h"] < 0).any():
        raise ValueError("nwp_lead_h must be non-negative")
    expected_time = table["issue_time"] + pd.to_timedelta(table["lead_time_h"], unit="h")
    if table["forecast_time"].ne(expected_time).any():
        raise ValueError("forecast_time must equal issue_time + lead_time_h hours")
    if table.duplicated(["issue_time", "forecast_time", "turbine_id"]).any():
        raise ValueError("M2 v1 keys (issue_time, forecast_time, turbine_id) must be unique")

    # Add internal copies; retain every public M2 field unchanged for provenance.
    table["lead_time"] = table["lead_time_h"]
    for public_name, internal_name in M2_WEATHER_ALIASES.items():
        table[internal_name] = table[public_name]
    table.attrs["weather_contract_version"] = WEATHER_CONTRACT_VERSION
    table.attrs["weather_file"] = str(source.resolve())
    return table
