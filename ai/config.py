"""Shared constants. Contract reference: docs/CONTRACTS.md."""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"
PROCESSED_DIR = DATA_DIR / "processed"

# Both turbines fall into the same ECMWF grid cell (43.620, 78.479),
# so weather is fetched once for the site and duplicated per turbine.
TURBINES = {
    "T1": (43.645150, 78.535604),
    "T2": (43.643198, 78.538828),
}
SITE_LAT, SITE_LON = TURBINES["T1"]

# Weather source: Open-Meteo Single Runs API, ECMWF IFS.
WEATHER_API_URL = "https://single-runs-api.open-meteo.com/v1/forecast"
WEATHER_MODEL = "ecmwf_ifs"
RUN_CYCLE_HOURS = (0, 6, 12, 18)
# Earliest run verified to exist in the archive for this site.
FIRST_AVAILABLE_RUN = pd.Timestamp("2024-04-15 00:00", tz="UTC")
RUN_FORECAST_HOURS = 72

# ASSUMPTION, not a verified publication time: a run becomes usable 7 hours
# after its initialization. Recorded in provenance as AVAILABILITY_BASIS.
AVAILABILITY_DELAY = pd.Timedelta(hours=7)
AVAILABILITY_BASIS = "assumed:init+7h"

WEATHER_VARIABLES = [
    "wind_speed_10m",
    "wind_speed_80m",
    "wind_speed_100m",
    "wind_speed_120m",
    "wind_direction_100m",
    "wind_gusts_10m",
    "temperature_2m",
    "surface_pressure",
    "relative_humidity_2m",
]
# Variables allowed to contain NaN (gusts are missing at the first hour of a run).
NULLABLE_WEATHER_VARIABLES = {"wind_gusts_10m"}

# Daily issue time: 00Z run becomes legal exactly at 07:00 UTC under the +7h assumption.
ISSUE_HOUR_UTC = 7
HORIZON_HOURS = 48

# Owner decision: hourly wind correlation favors UTC+5 independently in both periods; nacelle temperature-sensor lag biases the diurnal phase, which is too flat to resolve ±1h; identical SCADA temperature peak phase in 2023/2024/2025 indicates no clock change on 2024-03-01, so one fixed offset applies throughout; see data/processed/tz_report.json.
SCADA_UTC_OFFSET_H = 5
