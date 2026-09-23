"""Generate 1–48 hour M1 forecasts for one issue time."""

import argparse
from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from m1.features import attach_weather, build_examples, weather_only_examples
from m1.forecasting import M1Forecaster
from m1.scada import load_hourly_scada
from m1.weather import read_weather_vintages


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--issue-time", required=True, help="Naive time matching SCADA, e.g. 2026-01-29T23:00:00")
    parser.add_argument("--data-dir", default=".")
    parser.add_argument("--weather", help="M2-prepared weather_vintages.parquet matching this issue")
    parser.add_argument("--artifact-dir", help="Defaults to models/lightgbm[_weather] based on --weather")
    parser.add_argument("--output", default="predictions/m1_forecast.csv")
    parser.add_argument("--horizon", type=int, choices=range(1, 49))
    args = parser.parse_args()
    issue = pd.Timestamp(args.issue_time)
    if args.weather and issue.tz is None:
        raise ValueError("Weather-model issue time must be timezone-aware UTC")
    if args.weather:
        issue = issue.tz_convert("UTC")
    artifact_dir = args.artifact_dir or ("models/lightgbm_weather" if args.weather else "models/lightgbm")
    if args.weather and args.artifact_dir is None:
        fallback = Path("models/lightgbm_weather_only")
        if fallback.is_dir():
            fallback_model = M1Forecaster.load(fallback)
            cutoff = pd.Timestamp(fallback_model.metadata["history_model_issue_cutoff"])
            if issue > cutoff:
                artifact_dir = fallback

    model = M1Forecaster.load(artifact_dir)
    horizon = args.horizon or int(model.metadata["horizon_hours"])
    if model.metadata.get("feature_mode") == "weather_only":
        table = read_weather_vintages(args.weather)
        table = table.loc[table["issue_time"].eq(issue)].copy()
        if table.empty:
            raise ValueError(f"Weather input has no rows for issue time {issue.isoformat()}")
        examples = weather_only_examples(table)
    else:
        hourly = load_hourly_scada(
            args.data_dir, float(model.metadata["minimum_hourly_coverage"]), model.metadata.get("scada_timezone"),
        )
        if model.metadata.get("scada_timezone"):
            if issue.tz is None:
                raise ValueError("Weather-model issue time must be timezone-aware UTC")
            issue = issue.tz_convert("UTC")
        elif issue.tz is not None:
            raise ValueError("History-only artifact expects a naive issue time matching raw SCADA")
        if issue > hourly["hour_start"].max() + pd.Timedelta(hours=1):
            raise ValueError("Issue time is after available SCADA; recent-history features would be undefined")
        examples = build_examples(hourly, [issue], horizon, with_targets=False)
        if model.metadata["weather_features"]:
            if not args.weather:
                raise ValueError("This artifact requires --weather")
            examples = attach_weather(examples, read_weather_vintages(args.weather))
    predictions = model.predict(examples, models=("lightgbm",))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(output, index=False)
    print(f"Wrote {len(predictions):,} rows to {output.resolve()}")


if __name__ == "__main__":
    main()
