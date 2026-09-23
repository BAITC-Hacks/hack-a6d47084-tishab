from pathlib import Path

import numpy as np
import pandas as pd

from m1.features import KEYS, attach_weather, build_examples, feature_columns, split_issues, weather_only_examples
from m1.forecasting import M1Forecaster
from m1.scada import aggregate_scada
from m1.weather import WEATHER_CONTRACT_VERSION, read_weather_vintages


def raw_scada(hours: int = 240) -> pd.DataFrame:
    timestamps = pd.date_range("2025-01-01", periods=hours * 6, freq="10min")
    x = np.arange(len(timestamps))
    return pd.DataFrame({
        "ID": x + 1,
        "Статистическое время": timestamps.strftime("%Y-%m-%d %H:%M:%S"),
        "Средняя скорость ветра(m/s)": 5 + np.sin(x / 30),
        "Нормализованная активная мощность": np.clip(0.4 + 0.2 * np.sin(x / 40), 0, 1),
        "Средняя температура окружающей среды(°C)": 10 + np.cos(x / 50),
    })


def hourly_frame(hours: int = 240, timezone: str | None = None) -> pd.DataFrame:
    time = pd.date_range("2025-01-01", periods=hours, freq="h", tz=timezone)
    parts = []
    for turbine, offset in (("T1", 0.0), ("T2", 0.05)):
        power = np.clip(0.45 + offset + 0.2 * np.sin(np.arange(hours) / 8), 0, 1)
        parts.append(pd.DataFrame({
            "hour_start": time, "power": power, "wind_speed": 6 + power * 4,
            "temperature": 10 + np.sin(np.arange(hours) / 24),
            "observed_count": 6, "coverage": 1.0, "turbine_id": turbine,
        }))
    return pd.concat(parts, ignore_index=True)


def synthetic_m2_weather(examples: pd.DataFrame) -> pd.DataFrame:
    weather = examples[["issue_time", "forecast_time", "turbine_id", "lead_time"]].copy()
    weather = weather.rename(columns={"lead_time": "lead_time_h"})
    weather["weather_run_id"] = weather["issue_time"].dt.strftime("synthetic-%Y%m%d%H")
    weather["run_init_time"] = weather["issue_time"] - pd.Timedelta(hours=6)
    weather["available_at"] = weather["issue_time"] - pd.Timedelta(hours=5)
    weather["availability_basis"] = "synthetic-contract-fixture"
    weather["nwp_lead_h"] = weather["lead_time_h"] + 6
    lead = weather["lead_time_h"].astype(float)
    turbine_offset = weather["turbine_id"].map({"T1": 0.0, "T2": 0.2})
    weather["wind_speed_10m"] = 5.0 + lead / 100 + turbine_offset
    weather["wind_speed_80m"] = 7.0 + lead / 100 + turbine_offset
    weather["wind_speed_100m"] = 8.0 + lead / 100 + turbine_offset
    weather["wind_speed_120m"] = 8.5 + lead / 100 + turbine_offset
    weather["wind_direction_100m"] = (180 + lead * 2) % 360
    weather["wind_gusts_10m"] = weather["wind_speed_10m"] + 2.5
    weather["temperature_2m"] = 12 + np.sin(lead / 8)
    weather["surface_pressure"] = 101325 - lead * 3
    weather["relative_humidity_2m"] = 60 + np.cos(lead / 7) * 5
    return weather


def test_hourly_aggregation_and_missing_period(tmp_path: Path) -> None:
    raw = raw_scada(3).drop(index=[6])  # hour 01:00 has only five samples
    path = tmp_path / "scada.csv"
    raw.to_csv(path, index=False)
    hourly = aggregate_scada(path, "T1")
    assert len(hourly) == 3
    assert hourly.loc[0, "coverage"] == 1.0
    assert hourly.loc[1, "coverage"] == 5 / 6
    assert pd.isna(hourly.loc[1, "power"])
    assert hourly.loc[1, "observed_count"] == 5


def test_future_targets_are_not_features() -> None:
    hourly = hourly_frame()
    issue = pd.Timestamp("2025-01-09 00:00:00")
    before = build_examples(hourly, [issue], horizon=6)
    changed = hourly.copy()
    future = (changed["hour_start"] >= issue) & (changed["hour_start"] <= issue + pd.Timedelta(hours=6))
    changed.loc[future, "power"] = 1 - changed.loc[future, "power"]
    changed.loc[future, "wind_speed"] += 100
    changed.loc[future, "temperature"] += 100
    after = build_examples(changed, [issue], horizon=6)
    assert not before["target"].equals(after["target"])
    assert before[feature_columns(before)].equals(after[feature_columns(after)])
    expected_recent = hourly.loc[hourly["hour_start"].eq(issue - pd.Timedelta(hours=1)), "power"].iloc[0]
    assert before.loc[before["turbine_id"].eq("T1"), "recent_power"].iloc[0] == expected_recent


def test_weather_schema_and_direction_encoding(tmp_path: Path) -> None:
    examples = build_examples(hourly_frame(timezone="UTC"), [pd.Timestamp("2025-01-09", tz="UTC")], horizon=2)
    weather = synthetic_m2_weather(examples)
    weather["wind_direction_100m"] = 90.0
    path = tmp_path / "weather_vintages.parquet"
    weather.to_parquet(path, index=False)
    joined = attach_weather(examples, read_weather_vintages(path))
    assert np.allclose(joined["wx_direction_sin"], 1.0)
    assert np.allclose(joined["wx_direction_cos"], 0.0, atol=1e-12)
    assert feature_columns(joined) == feature_columns(joined.copy())


def test_weather_vintages_parquet_contract(tmp_path: Path) -> None:
    examples = build_examples(hourly_frame(timezone="UTC"), [pd.Timestamp("2025-01-09", tz="UTC")], horizon=2)
    weather = synthetic_m2_weather(examples)
    weather.loc[weather.index[0], "available_at"] = weather.loc[weather.index[0], "issue_time"] + pd.Timedelta(hours=1)
    original_available = weather["available_at"].copy()
    path = tmp_path / "weather_vintages.parquet"
    weather.to_parquet(path, index=False)
    loaded = read_weather_vintages(path)
    assert loaded.attrs["weather_contract_version"] == WEATHER_CONTRACT_VERSION
    assert "wx_wind_100m" in loaded and "wind_speed_100m" in loaded
    assert loaded["available_at"].equals(original_available)
    assert str(loaded["issue_time"].dt.tz) == "UTC"
    joined = attach_weather(examples, loaded)
    assert set(["lead_time_h", "run_init_time", "available_at", "availability_basis", "nwp_lead_h"]).issubset(joined)


def test_weather_parquet_rejects_columns_outside_contract(tmp_path: Path) -> None:
    examples = build_examples(hourly_frame(timezone="UTC"), [pd.Timestamp("2025-01-09", tz="UTC")], horizon=1)
    weather = synthetic_m2_weather(examples)
    weather["humidity"] = 50.0
    path = tmp_path / "weather_vintages.parquet"
    weather.to_parquet(path, index=False)
    try:
        read_weather_vintages(path)
    except ValueError as exc:
        assert "humidity" in str(exc)
    else:
        raise AssertionError("Unexpected weather fields must be rejected")


def test_weather_features_train_and_predict_end_to_end(tmp_path: Path) -> None:
    hourly = hourly_frame(480, timezone="UTC")
    issues = pd.date_range("2025-01-09", periods=4, freq="D", tz="UTC")
    examples = build_examples(hourly, issues, horizon=48)
    weather = synthetic_m2_weather(examples)
    path = tmp_path / "weather_vintages.parquet"
    weather.to_parquet(path, index=False)
    prepared = attach_weather(examples, read_weather_vintages(path))
    training = prepared[prepared["issue_time"] < issues[-1]]
    inference = prepared[prepared["issue_time"] == issues[-1]].drop(columns="target")
    model = M1Forecaster("weather-test-v1").train(training, hourly)
    predictions = model.predict(inference, models=("lightgbm",))
    assert "wx_wind_100m" in model.columns
    assert "wx_relative_humidity" in model.metadata["weather_features"]
    assert len(predictions) == 48 * 2
    assert set(predictions["turbine_id"]) == {"T1", "T2"}
    assert set(predictions["lead_time"]) == set(range(1, 49))
    assert (predictions["forecast_time"] == predictions["issue_time"] + pd.to_timedelta(predictions["lead_time"], unit="h")).all()
    assert predictions["prediction"].between(0, 1).all()
    assert set(KEYS + ["prediction", "model_name", "model_version", "weather_run_id", "available_at"]).issubset(predictions)


def test_weather_only_model_needs_no_scada_history_at_inference(tmp_path: Path) -> None:
    hourly = hourly_frame(480, timezone="UTC")
    issues = pd.date_range("2025-01-09", periods=4, freq="D", tz="UTC")
    history_examples = build_examples(hourly, issues, horizon=48)
    path = tmp_path / "weather_vintages.parquet"
    synthetic_m2_weather(history_examples).to_parquet(path, index=False)
    weather = read_weather_vintages(path)
    prepared = weather_only_examples(weather, hourly)
    model = M1Forecaster("weather-only-test-v1").train(prepared, hourly, feature_mode="weather_only")
    future = weather_only_examples(weather.loc[weather["issue_time"].eq(issues[-1])])
    predictions = model.predict(future)
    assert len(predictions) == 96
    assert not any(name in model.columns for name in ("recent_power", "recent_wind", "power_mean_24h"))


def test_time_split_has_no_target_overlap() -> None:
    issues = pd.date_range("2025-03-18 23:00", "2026-01-29 23:00", freq="D")
    training, validation, validation_start = split_issues(issues, horizon=48, validation_days=60)
    training_targets = {
        issue + pd.Timedelta(hours=lead) for issue in training for lead in range(1, 49)
    }
    validation_targets = {
        issue + pd.Timedelta(hours=lead) for issue in validation for lead in range(1, 49)
    }
    assert validation_start == pd.Timestamp("2025-12-01 00:00")
    assert max(training_targets) < min(validation_targets)
    assert training_targets.isdisjoint(validation_targets)
    assert max(validation_targets) < pd.Timestamp("2026-02-01 00:00")


def test_train_save_load_and_prediction_contract(tmp_path: Path) -> None:
    hourly = hourly_frame(360)
    issues = pd.date_range("2025-01-09", periods=5, freq="D")
    examples = build_examples(hourly, issues, horizon=4)
    model = M1Forecaster("test-v1").train(examples, hourly[hourly["hour_start"] < issues.max()])
    expected = model.predict(examples.drop(columns="target"))
    artifact = tmp_path / "model"
    model.save(artifact)
    actual = M1Forecaster.load(artifact).predict(examples.drop(columns="target"))
    assert set(KEYS + ["prediction", "model_name", "model_version"]).issubset(actual.columns)
    assert actual["prediction"].between(0, 1).all()
    assert np.allclose(expected["prediction"], actual["prediction"])
