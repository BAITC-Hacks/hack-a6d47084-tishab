"""Leakage-safe model-side features from completed SCADA hours and M2's table."""

import numpy as np
import pandas as pd

KEYS = ["issue_time", "forecast_time", "turbine_id", "lead_time"]
PROVENANCE = [
    "lead_time_h", "weather_run_id", "run_init_time", "available_at",
    "availability_basis", "nwp_lead_h",
]
OPTIONAL_PROVENANCE: list[str] = []
ALLOWED_WEATHER = [
    "wx_wind_10m", "wx_wind_80m", "wx_wind_100m", "wx_wind_120m",
    "wx_wind_direction", "wx_temperature", "wx_pressure", "wx_gust",
    "wx_relative_humidity", "wx_nwp_lead_h",
]
BASE_FEATURES = [
    "turbine_code", "lead_time", "target_hour", "target_month", "target_dayofweek",
    "recent_power", "power_mean_24h", "power_mean_168h", "power_age_hours",
    "recent_wind", "wind_mean_24h", "recent_temperature", "temperature_mean_24h",
    "observed_hours_24h",
]
WEATHER_ONLY_BASE_FEATURES = [
    "turbine_code", "lead_time", "target_hour", "target_month", "target_dayofweek",
]


def daily_issues(hourly: pd.DataFrame, horizon: int = 48, issue_hour: int = 23) -> pd.DatetimeIndex:
    if not 1 <= horizon <= 48 or not 0 <= issue_hour <= 23:
        raise ValueError("horizon must be 1..48 and issue_hour 0..23")
    first = pd.Timestamp(hourly["hour_start"].min()) + pd.Timedelta(days=7)
    last = pd.Timestamp(hourly["hour_start"].max()) - pd.Timedelta(hours=horizon)
    return pd.date_range(first.normalize(), last.normalize(), freq="D") + pd.Timedelta(hours=issue_hour)


def split_issues(
    issues: pd.DatetimeIndex, horizon: int = 48, validation_days: int = 60,
) -> tuple[pd.DatetimeIndex, pd.DatetimeIndex, pd.Timestamp]:
    """Keep every training target strictly before the validation boundary."""
    if validation_days < 1:
        raise ValueError("validation_days must be positive")
    validation_start = issues.max().normalize() - pd.Timedelta(days=validation_days - 1)
    training = issues[issues < validation_start - pd.Timedelta(hours=horizon)]
    validation = issues[issues >= validation_start]
    if len(training) == 0 or len(validation) == 0:
        raise ValueError("Time split produced an empty training or validation set")
    return training, validation, validation_start


def _history_at_issues(turbine: pd.DataFrame, issues: pd.DatetimeIndex) -> pd.DataFrame:
    h = turbine.set_index("hour_start").sort_index()
    if str(h.index.tz) != str(issues.tz):
        raise ValueError("SCADA hours and issue times must use the same timezone")
    observed = h["power"].notna()
    last_valid_time = pd.Series(h.index.where(observed), index=h.index).ffill()
    hist = pd.DataFrame(index=h.index)
    hist["recent_power"] = h["power"].ffill()
    hist["power_mean_24h"] = h["power"].rolling(24, min_periods=6).mean()
    hist["power_mean_168h"] = h["power"].rolling(168, min_periods=24).mean()
    hist["recent_wind"] = h["wind_speed"].ffill()
    hist["wind_mean_24h"] = h["wind_speed"].rolling(24, min_periods=6).mean()
    hist["recent_temperature"] = h["temperature"].ffill()
    hist["temperature_mean_24h"] = h["temperature"].rolling(24, min_periods=6).mean()
    hist["observed_hours_24h"] = observed.rolling(24, min_periods=1).sum()
    hist["last_valid_time"] = last_valid_time
    lookup = issues - pd.Timedelta(hours=1)  # the latest *completed* hour
    result = hist.reindex(lookup).reset_index(drop=True)
    age = (issues.to_series().reset_index(drop=True) - result["last_valid_time"] - pd.Timedelta(hours=1)) / pd.Timedelta(hours=1)
    result["power_age_hours"] = age.to_numpy(dtype=float)
    stale = result["power_age_hours"].isna() | result["power_age_hours"].gt(6)
    result.loc[stale, ["recent_power", "recent_wind", "recent_temperature"]] = np.nan
    return result.drop(columns="last_valid_time")


def build_examples(
    hourly: pd.DataFrame, issues: pd.DatetimeIndex | list, horizon: int = 48,
    with_targets: bool = True,
) -> pd.DataFrame:
    """One row per issue/lead/turbine. Targets are separate from all features."""
    if not 1 <= horizon <= 48:
        raise ValueError("horizon must be 1..48")
    issues = pd.DatetimeIndex(pd.to_datetime(issues)).sort_values().unique()
    if len(issues) == 0:
        raise ValueError("No issue times")
    if any((t.minute, t.second, t.microsecond) != (0, 0, 0) for t in issues):
        raise ValueError("Issue times must be aligned to full hours")
    parts = []
    for turbine_id, turbine in hourly.groupby("turbine_id", sort=True):
        history = _history_at_issues(turbine, issues)
        lead_values = np.tile(np.arange(1, horizon + 1), len(issues))
        issue_values = issues.repeat(horizon)
        frame = pd.DataFrame({
            "issue_time": issue_values,
            "forecast_time": issue_values + pd.to_timedelta(lead_values, unit="h"),
            "turbine_id": turbine_id,
            "lead_time": lead_values,
        })
        for column in history.columns:
            frame[column] = np.repeat(history[column].to_numpy(), horizon)
        if with_targets:
            targets = turbine.set_index("hour_start")["power"]
            frame["target"] = targets.reindex(frame["forecast_time"]).to_numpy()
        parts.append(frame)
    result = pd.concat(parts, ignore_index=True)
    target_time = pd.to_datetime(result["forecast_time"])
    result["target_hour"] = target_time.dt.hour
    result["target_month"] = target_time.dt.month
    result["target_dayofweek"] = target_time.dt.dayofweek
    result["turbine_code"] = result["turbine_id"].map({"T1": 1, "T2": 2}).astype("int8")
    return result.sort_values(KEYS).reset_index(drop=True)


def attach_weather(examples: pd.DataFrame, weather: pd.DataFrame, require_all: bool = True) -> pd.DataFrame:
    """Join M2-prepared rows; M2 alone certifies weather-vintage legality."""
    required = set(KEYS + PROVENANCE)
    missing = required - set(weather.columns)
    if missing:
        raise ValueError(f"M2 weather table missing columns: {sorted(missing)}")
    weather_features = [c for c in ALLOWED_WEATHER if c in weather.columns]
    if not weather_features:
        raise ValueError("M2 weather table has no supported wx_ feature columns")
    unexpected = [c for c in weather.columns if c.startswith("wx_") and c not in ALLOWED_WEATHER]
    if unexpected:
        raise ValueError(f"Unsupported weather features: {unexpected}")
    optional_provenance = [c for c in OPTIONAL_PROVENANCE if c in weather.columns]
    selected = weather[KEYS + PROVENANCE + optional_provenance + weather_features].copy()
    if selected[KEYS].isna().any().any() or selected.duplicated(KEYS).any():
        raise ValueError("M2 weather keys must be non-null and unique")
    for column in weather_features:
        selected[column] = pd.to_numeric(selected[column], errors="raise")
    for frame_name, frame in (("examples", examples), ("weather", selected)):
        for column in ("issue_time", "forecast_time"):
            if not isinstance(frame[column].dtype, pd.DatetimeTZDtype) or str(frame[column].dt.tz) != "UTC":
                raise ValueError(f"{frame_name}.{column} must be timezone-aware UTC")
    merged = examples.merge(selected, on=KEYS, how="left", validate="one_to_one", indicator=True)
    if require_all and merged["_merge"].ne("both").any():
        raise ValueError(f"M2 weather table lacks {int(merged['_merge'].ne('both').sum())} requested rows")
    merged = merged.drop(columns="_merge")
    if "wx_wind_direction" in weather_features:
        radians = np.deg2rad(merged["wx_wind_direction"])
        merged["wx_direction_sin"] = np.sin(radians)
        merged["wx_direction_cos"] = np.cos(radians)
    return merged


def weather_only_examples(
    weather: pd.DataFrame, hourly_targets: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Build ML rows solely from M2 weather; SCADA is used only as an optional target."""
    weather_features = [c for c in ALLOWED_WEATHER if c in weather.columns]
    selected = weather[KEYS + PROVENANCE + weather_features].copy()
    if selected[KEYS].isna().any().any() or selected.duplicated(KEYS).any():
        raise ValueError("M2 weather keys must be non-null and unique")
    target_time = pd.to_datetime(selected["forecast_time"])
    selected["target_hour"] = target_time.dt.hour
    selected["target_month"] = target_time.dt.month
    selected["target_dayofweek"] = target_time.dt.dayofweek
    selected["turbine_code"] = selected["turbine_id"].map({"T1": 1, "T2": 2}).astype("int8")
    if "wx_wind_direction" in selected:
        radians = np.deg2rad(selected["wx_wind_direction"])
        selected["wx_direction_sin"] = np.sin(radians)
        selected["wx_direction_cos"] = np.cos(radians)
    if hourly_targets is not None:
        targets = hourly_targets[["hour_start", "turbine_id", "power"]].rename(
            columns={"hour_start": "forecast_time", "power": "target"}
        )
        selected = selected.merge(targets, on=["forecast_time", "turbine_id"], how="left", validate="many_to_one")
    return selected.sort_values(KEYS).reset_index(drop=True)


def feature_columns(examples: pd.DataFrame, mode: str = "history") -> list[str]:
    base = WEATHER_ONLY_BASE_FEATURES if mode == "weather_only" else BASE_FEATURES
    columns = base + [c for c in ALLOWED_WEATHER if c in examples.columns and c != "wx_wind_direction"]
    if "wx_wind_direction" in examples.columns:
        columns += ["wx_direction_sin", "wx_direction_cos"]
    return columns
