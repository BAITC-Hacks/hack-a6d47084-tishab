"""Load the supplied ten-minute SCADA and retain incomplete hourly bins."""

from pathlib import Path

import numpy as np
import pandas as pd

RAW_COLUMNS = {
    "Статистическое время": "timestamp",
    "Средняя скорость ветра(m/s)": "wind_speed",
    "Нормализованная активная мощность": "power",
    "Средняя температура окружающей среды(°C)": "temperature",
}


def find_scada_files(data_dir: str | Path) -> dict[str, Path]:
    root = Path(data_dir)
    found = {}
    for turbine_id, suffix in (("T1", "turbine 1.csv"), ("T2", "turbine 2.csv")):
        matches = list(root.glob(f"*{suffix}"))
        if len(matches) != 1:
            raise FileNotFoundError(f"Expected one {suffix} in {root}; found {len(matches)}")
        found[turbine_id] = matches[0]
    return found


def aggregate_scada(path: str | Path, turbine_id: str, min_coverage: float = 1.0) -> pd.DataFrame:
    """Return all hourly bins, with target NaN when fewer than six readings exist.

    The raw timestamps are naive; caller must use the same convention for issue
    and weather times until the source timezone is established.
    """
    if not 0 < min_coverage <= 1:
        raise ValueError("min_coverage must be in (0, 1]")
    raw = pd.read_csv(path, encoding="utf-8-sig")
    required = {"ID", *RAW_COLUMNS}
    if not required.issubset(raw.columns):
        raise ValueError(f"Missing SCADA columns: {sorted(required - set(raw.columns))}")
    raw = raw.rename(columns=RAW_COLUMNS)
    raw["timestamp"] = pd.to_datetime(raw["timestamp"], format="%Y-%m-%d %H:%M:%S", errors="raise")
    if raw["timestamp"].duplicated().any():
        raise ValueError(f"Duplicate timestamps in {path}")
    if ((raw["timestamp"].dt.minute % 10) != 0).any() or raw["timestamp"].dt.second.ne(0).any():
        raise ValueError(f"Unexpected SCADA sampling timestamps in {path}")
    for name in ("wind_speed", "power", "temperature"):
        raw[name] = pd.to_numeric(raw[name], errors="raise")
        if not np.isfinite(raw[name]).all():
            raise ValueError(f"Non-finite {name} in {path}")
    if raw["power"].lt(0).any() or raw["power"].gt(1).any():
        raise ValueError(f"Power outside [0, 1] in {path}")
    hourly = raw.set_index("timestamp").sort_index().resample("h").agg(
        power=("power", "mean"), wind_speed=("wind_speed", "mean"),
        temperature=("temperature", "mean"), observed_count=("power", "count"),
    )
    hourly["coverage"] = hourly["observed_count"] / 6.0
    incomplete = hourly["coverage"] < min_coverage
    hourly.loc[incomplete, ["power", "wind_speed", "temperature"]] = np.nan
    hourly["turbine_id"] = turbine_id
    hourly.index.name = "hour_start"
    return hourly.reset_index()


def load_hourly_scada(
    data_dir: str | Path, min_coverage: float = 1.0, timezone: str | None = None,
) -> pd.DataFrame:
    files = find_scada_files(data_dir)
    hourly = pd.concat(
        [aggregate_scada(path, turbine_id, min_coverage) for turbine_id, path in files.items()],
        ignore_index=True,
    ).sort_values(["turbine_id", "hour_start"]).reset_index(drop=True)
    if timezone:
        hourly["hour_start"] = (
            hourly["hour_start"].dt.tz_localize(timezone, ambiguous="raise", nonexistent="raise").dt.tz_convert("UTC")
        )
    return hourly
