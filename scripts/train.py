"""Train M1 LightGBM and baselines; optionally consume an M2-prepared weather CSV."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from m1.features import attach_weather, build_examples, daily_issues, split_issues
from m1.forecasting import M1Forecaster
from m1.scada import load_hourly_scada
from m1.weather import WEATHER_CONTRACT_VERSION, read_weather_vintages, weather_file_sha256


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default=".")
    parser.add_argument("--weather", help="M2-prepared weather_vintages.parquet; omit for history-only model")
    parser.add_argument("--artifact-dir", help="Defaults to models/lightgbm[_weather] based on --weather")
    parser.add_argument("--horizon", type=int, default=48, choices=range(1, 49))
    parser.add_argument("--validation-days", type=int, default=60)
    parser.add_argument("--issue-hour", type=int, default=23, choices=range(24))
    parser.add_argument("--min-coverage", type=float, default=1.0)
    parser.add_argument("--scada-timezone", help="Explicit timezone of naive raw SCADA; required with --weather")
    args = parser.parse_args()
    if args.validation_days < 1:
        parser.error("--validation-days must be positive")
    if args.weather and not args.scada_timezone:
        parser.error("--scada-timezone is required with --weather; M1 will not infer the SCADA timezone")
    artifact_dir = args.artifact_dir or ("models/lightgbm_weather" if args.weather else "models/lightgbm")

    hourly = load_hourly_scada(args.data_dir, args.min_coverage, args.scada_timezone)
    issues = daily_issues(hourly, args.horizon, args.issue_hour)
    train_issues, _, validation_start = split_issues(issues, args.horizon, args.validation_days)
    examples = build_examples(hourly, train_issues, args.horizon)
    weather_table = None
    if args.weather:
        weather_table = read_weather_vintages(args.weather)
        examples = attach_weather(examples, weather_table)
    training_history = hourly[hourly["hour_start"] < validation_start].copy()
    version = "m1-lgbm-weather-v1" if args.weather else "m1-lgbm-v1"
    model = M1Forecaster(version).train(examples, training_history)
    model.metadata.update({
        "validation_start_reserved": str(validation_start),
        "horizon_hours": args.horizon,
        "issue_hour": args.issue_hour,
        "minimum_hourly_coverage": args.min_coverage,
        "scada_timezone": args.scada_timezone,
        "m2_weather_file": str(args.weather) if args.weather else None,
        "m2_weather_contract": WEATHER_CONTRACT_VERSION if args.weather else None,
        "m2_weather_sha256": weather_file_sha256(args.weather) if args.weather else None,
        "m2_weather_columns": list(weather_table.columns) if weather_table is not None else [],
        "training_mode": "M2 weather features" if args.weather else "SCADA history-only fallback",
    })
    model.save(artifact_dir)
    print(f"Saved {model.version} to {Path(artifact_dir).resolve()}")
    print(f"Training examples: {model.metadata['training_rows']:,}; features: {len(model.columns)}")


if __name__ == "__main__":
    main()
