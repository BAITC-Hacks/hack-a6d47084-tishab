"""Evaluate a saved artifact on the reserved final issue dates."""

import argparse
from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from m1.evaluation import evaluate
from m1.features import attach_weather, build_examples, daily_issues
from m1.forecasting import M1Forecaster
from m1.scada import load_hourly_scada
from m1.weather import read_weather_vintages


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default=".")
    parser.add_argument("--weather", help="M2-prepared weather_vintages.parquet matching the artifact")
    parser.add_argument("--artifact-dir", help="Defaults to models/lightgbm[_weather] based on --weather")
    parser.add_argument("--output", help="Defaults to reports/evaluation[_weather].csv")
    args = parser.parse_args()
    artifact_dir = args.artifact_dir or ("models/lightgbm_weather" if args.weather else "models/lightgbm")
    output_path = args.output or ("reports/evaluation_weather.csv" if args.weather else "reports/evaluation.csv")

    model = M1Forecaster.load(artifact_dir)
    horizon = int(model.metadata["horizon_hours"])
    hourly = load_hourly_scada(
        args.data_dir, float(model.metadata["minimum_hourly_coverage"]), model.metadata.get("scada_timezone"),
    )
    all_issues = daily_issues(hourly, horizon, int(model.metadata["issue_hour"]))
    validation_start = pd.Timestamp(model.metadata["validation_start_reserved"])
    validation_issues = all_issues[all_issues >= validation_start]
    examples = build_examples(hourly, validation_issues, horizon)
    if model.metadata["weather_features"]:
        if not args.weather:
            raise ValueError("This artifact requires --weather")
        examples = attach_weather(examples, read_weather_vintages(args.weather))
    predictions = model.predict(examples)
    metrics = evaluate(examples, predictions)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(output, index=False)
    summary = metrics[(metrics["turbine_id"] == "all") & (metrics["lead_time"] == "all")]
    print(summary.to_string(index=False))
    print(f"Detailed metrics: {output.resolve()}")


if __name__ == "__main__":
    main()
