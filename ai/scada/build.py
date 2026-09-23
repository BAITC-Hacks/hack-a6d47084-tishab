"""Build hourly SCADA with UTC hour-start labels (docs/CONTRACTS.md, section 3).

    python3 -m ai.scada.build

Naive source times are localized to a fixed UTC offset at ingestion. UTC records
10:00..10:50 belong to hour 10:00 via ts.floor("h"). Missing hours stay NaN.
For an issue T, downstream users may use only hours with timestamp + 1h <= T.
"""

from __future__ import annotations

from datetime import timedelta, timezone

import numpy as np
import pandas as pd

from ai import config

COLUMNS = [
    "timestamp", "turbine_id", "power", "wind_speed", "temperature",
    "n_samples", "is_valid", "flag",
]
SOURCE_COLUMNS = {
    "Статистическое время": "ts",
    "Средняя скорость ветра(m/s)": "wind_speed",
    "Нормализованная активная мощность": "power",
    "Средняя температура окружающей среды(°C)": "temperature",
}


def build_hourly(
    records: pd.DataFrame, turbine_id: str, offset_h: int = config.SCADA_UTC_OFFSET_H,
) -> pd.DataFrame:
    """Aggregate one turbine's naive 10-minute records onto a full UTC hourly grid."""
    if records.empty:
        raise ValueError("cannot build an hourly grid from empty SCADA")
    df = records[["ts", "wind_speed", "power", "temperature"]].copy()
    source_time = pd.to_datetime(df.ts, errors="raise")
    if source_time.dt.tz is not None:
        raise ValueError("SCADA ingestion expects naive source timestamps")
    if source_time.isna().any() or source_time.duplicated().any():
        raise ValueError("SCADA timestamps must be present and unique per turbine")
    df["ts"] = source_time.dt.tz_localize(timezone(timedelta(hours=offset_h))).dt.tz_convert("UTC")
    df = df.sort_values("ts").reset_index(drop=True)
    df["timestamp"] = df.ts.dt.floor("h")

    # Missing slots break runs even when wind values on either side are identical.
    new_run = df.wind_speed.ne(df.wind_speed.shift()) | df.ts.diff().ne(pd.Timedelta(minutes=10))
    run_lengths = df.groupby(new_run.cumsum()).wind_speed.transform("size")
    stuck_hours = df.loc[(run_lengths >= 6) & df.wind_speed.notna(), "timestamp"].unique()

    grouped = df.groupby("timestamp")
    grid = pd.date_range(df.timestamp.min(), df.timestamp.max(), freq="h", name="timestamp")
    hourly = grouped[["power", "wind_speed", "temperature"]].mean().reindex(grid)
    hourly["n_samples"] = grouped.size().reindex(grid, fill_value=0).astype("int64")
    if hourly.n_samples.gt(6).any():
        raise ValueError("SCADA has more than six samples in an hour")
    hourly["flag"] = np.select(
        [hourly.n_samples.eq(0), hourly.n_samples.lt(4), hourly.index.isin(stuck_hours),
         hourly.wind_speed.gt(6) & hourly.power.le(0.01)],
        ["no_data", "low_coverage", "stuck_sensor", "possible_curtailment"],
        default="ok",
    )
    hourly["is_valid"] = hourly.flag.eq("ok")
    hourly["turbine_id"] = turbine_id
    return hourly.reset_index()[COLUMNS]


def main() -> None:
    frames = []
    for turbine_id, n in (("T1", 1), ("T2", 2)):
        path = next(config.DATA_DIR.glob(f"*turbine {n}.csv"))
        records = pd.read_csv(path).rename(columns=SOURCE_COLUMNS)
        hourly = build_hourly(records, turbine_id)
        frames.append(hourly)
        print(f"{turbine_id}: hours={len(hourly)}, valid={hourly.is_valid.mean():.6%}, "
              f"range={hourly.timestamp.min().isoformat()} .. {hourly.timestamp.max().isoformat()}")
        print(hourly.flag.value_counts().to_string())
    table = pd.concat(frames, ignore_index=True)
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    path = config.PROCESSED_DIR / "scada_hourly.parquet"
    table.to_parquet(path, index=False)
    print(f"rows: {len(table)} -> {path}")


if __name__ == "__main__":
    main()
