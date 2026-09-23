"""Train the separate M2 weather-only LightGBM artifact."""

import argparse
from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from m1.features import weather_only_examples
from m1.forecasting import M1Forecaster
from m1.scada import load_hourly_scada
from m1.weather import WEATHER_CONTRACT_VERSION, read_weather_vintages, weather_file_sha256

TRAIN_START = pd.Timestamp("2024-04-16 07:00:00", tz="UTC")
TRAIN_END = pd.Timestamp("2025-11-28 07:00:00", tz="UTC")
VALIDATION_START = pd.Timestamp("2025-12-01 07:00:00", tz="UTC")
VALIDATION_END = pd.Timestamp("2026-01-29 07:00:00", tz="UTC")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default=".")
    parser.add_argument("--weather", default="data/processed/weather_vintages.parquet")
    parser.add_argument("--artifact-dir", default="models/lightgbm_weather_only")
    parser.add_argument("--scada-timezone", default="Etc/GMT-5")
    args = parser.parse_args()

    weather = read_weather_vintages(args.weather)
    hourly = load_hourly_scada(args.data_dir, 1.0, args.scada_timezone)
    train_weather = weather.loc[weather["issue_time"].between(TRAIN_START, TRAIN_END)].copy()
    validation_weather = weather.loc[weather["issue_time"].between(VALIDATION_START, VALIDATION_END)].copy()
    examples = weather_only_examples(train_weather, hourly)
    model = M1Forecaster("m1-lgbm-weather-only-v1").train(
        examples, hourly.loc[hourly["hour_start"] < VALIDATION_START], feature_mode="weather_only"
    )
    training_target_end = pd.Timestamp(model.metadata["training_target_end"])
    model.metadata.update({
        "cutoff": (training_target_end + pd.Timedelta(hours=1)).isoformat(),
        "validation_start_reserved": VALIDATION_START.isoformat(),
        "validation_end_reserved": VALIDATION_END.isoformat(),
        "horizon_hours": 48,
        "issue_hour": 7,
        "minimum_hourly_coverage": 1.0,
        "scada_timezone": args.scada_timezone,
        "timestamp_convention": "timezone-aware UTC",
        "history_model_issue_cutoff": (hourly["hour_start"].max() + pd.Timedelta(hours=1)).isoformat(),
        "m2_weather_file": str(args.weather),
        "m2_weather_contract": WEATHER_CONTRACT_VERSION,
        "m2_weather_sha256": weather_file_sha256(args.weather),
        "training_mode": "M2 weather-only features",
        "training_issue_count": int(train_weather["issue_time"].nunique()),
        "validation_issue_count": int(validation_weather["issue_time"].nunique()),
    })
    model.save(args.artifact_dir)
    print(f"Saved {model.version} to {Path(args.artifact_dir).resolve()}")
    print(f"Training rows: {model.metadata['training_rows']:,}; issues: {model.metadata['training_issue_count']}")


if __name__ == "__main__":
    main()
