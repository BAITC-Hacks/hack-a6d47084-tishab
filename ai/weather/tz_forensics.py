"""Infer the naive SCADA clock from short-lead wind and temperature forecasts.

    python -m ai.weather.tz_forensics

Naive timestamps are handled only at SCADA ingestion: interpreting them as UTC+k
subtracts k hours and localizes to UTC. Missing hours remain missing. Temperature
is checked using the UTC-hour diurnal cycles of paired observations and forecasts.
Weather overlap begins in April 2024; no pre-March-2024 offset can be inferred.
"""

from __future__ import annotations

import json

import pandas as pd

from ai import config

OFFSETS = range(-2, 10)
MIN_MARGIN = 0.005
PERIODS = {
    "2024-04..2024-12": ("2024-04-01", "2025-01-01"),
    "2025-01..2026-01": ("2025-01-01", "2026-02-01"),
}


def load_scada_naive() -> dict[str, pd.DataFrame]:
    """Read hourly wind and temperature per turbine in the unassigned source clock."""
    frames = {"wind": [], "temp": []}
    for tid, n in (("T1", 1), ("T2", 2)):
        path = next(config.DATA_DIR.glob(f"*turbine {n}.csv"))
        df = pd.read_csv(path)
        df.columns = ["id", "ts", "wind", "power", "temp"]
        df["ts"] = pd.to_datetime(df["ts"])
        if df.ts.dt.tz is not None:
            raise ValueError("SCADA source timestamps must be naive")
        hourly = df.set_index("ts")[["wind", "temp"]].resample("h").mean()
        for variable in frames:
            frames[variable].append(hourly[variable].rename(tid))
    return {variable: pd.concat(parts, axis=1) for variable, parts in frames.items()}


def load_scada_wind_naive() -> pd.DataFrame:
    return load_scada_naive()["wind"]


def _paired_hours(nwp: pd.Series, measured: pd.Series, offset: int) -> pd.DataFrame:
    """Assign a candidate UTC offset at the SCADA ingestion boundary."""
    if measured.index.tz is not None:
        raise ValueError("SCADA source timestamps must be naive")
    if nwp.index.tz is None:
        raise ValueError("weather timestamps must be timezone-aware")
    nwp = nwp.copy()
    nwp.index = nwp.index.tz_convert("UTC")
    utc_index = (measured.index - pd.Timedelta(hours=offset)).tz_localize("UTC")
    shifted = pd.Series(measured.values, index=utc_index, name="measured")
    return pd.concat([nwp.rename("forecast"), shifted], axis=1, join="inner").dropna()


def _scores(
    weather: pd.DataFrame, scada: pd.DataFrame, variable: str,
    offsets=OFFSETS, diurnal: bool = False,
) -> tuple[pd.Series, dict[int, int]]:
    # Leads 1..24 of daily issues do not overlap; T1/T2 share the weather grid cell.
    short = weather[weather.lead_time_h.between(1, 24)]
    nwp = short.drop_duplicates("forecast_time").set_index("forecast_time")[variable].sort_index()
    measured = scada.mean(axis=1)
    scores, counts = {}, {}
    for k in offsets:
        joined = _paired_hours(nwp, measured, k)
        counts[k] = len(joined)
        signal = joined.groupby(joined.index.hour).mean() if diurnal else joined
        scores[k] = signal.forecast.corr(signal.measured)
    return pd.Series(scores, name="corr").rename_axis("utc_offset_h"), counts


def offset_scores(weather: pd.DataFrame, scada: pd.DataFrame, offsets=OFFSETS) -> pd.Series:
    return _scores(weather, scada, "wind_speed_100m", offsets)[0]


def _summary(scores: pd.Series, counts: dict[int, int]) -> dict:
    ranked = scores.dropna().sort_values(ascending=False)
    if len(ranked) < 2:
        raise ValueError("insufficient paired data to compare timezone offsets")
    best, runner = int(ranked.index[0]), int(ranked.index[1])
    margin = float(ranked.iloc[0] - ranked.iloc[1])
    return {
        "scores": {int(k): float(v) if pd.notna(v) else None for k, v in scores.items()},
        "best_offset_h": best,
        "runner_up": {"offset_h": runner, "corr": float(ranked.iloc[1])},
        "margin": margin,
        "status": "inconclusive" if margin < MIN_MARGIN else "conclusive",
        "n_hours": counts[best],
        "n_hours_by_offset": counts,
    }


def analyze(weather: pd.DataFrame, scada: dict[str, pd.DataFrame]) -> dict:
    wind = _summary(*_scores(weather, scada["wind"], "wind_speed_100m"))
    temperature = _summary(*_scores(weather, scada["temp"], "temperature_2m", diurnal=True))
    wind["temperature_cross_check"] = temperature
    return wind


def main() -> None:
    weather = pd.read_parquet(config.PROCESSED_DIR / "weather_vintages.parquet")
    weather = weather[weather.turbine_id == "T1"]
    scada = load_scada_naive()
    report = analyze(weather, scada)
    report["per_period"] = {}
    for label, (start, end) in PERIODS.items():
        mask = (weather.forecast_time >= pd.Timestamp(start, tz="UTC")) & (
            weather.forecast_time < pd.Timestamp(end, tz="UTC"))
        report["per_period"][label] = analyze(weather.loc[mask], scada)
    temperature = report["temperature_cross_check"]
    report["signals_agree"] = report["best_offset_h"] == temperature["best_offset_h"]
    report["chosen_offset_h"] = report["best_offset_h"] if (
        report["signals_agree"] and report["status"] == "conclusive"
        and temperature["status"] == "conclusive"
    ) else None
    report["overall_status"] = "conclusive" if report["chosen_offset_h"] is not None else "inconclusive"
    report["conclusion"] = (
        f"SCADA_UTC_OFFSET_H = {report['chosen_offset_h']} (supported for weather overlap only)"
        if report["chosen_offset_h"] is not None else "inconclusive; do not set SCADA_UTC_OFFSET_H"
    )
    report["method"] = {
        "wind": "Pearson correlation of paired hourly turbine-mean wind and ECMWF wind_speed_100m, leads 1..24",
        "temperature": "Pearson correlation of 24 UTC-hour diurnal means from paired hourly turbine-mean temperature and ECMWF temperature_2m, leads 1..24",
        "missing": "Exclude missing pairs; turbine mean uses available turbines; no filling",
        "minimum_margin": MIN_MARGIN,
    }
    report["limitation"] = (
        "Weather exists only from April 2024, after the 2024-03-01 change to UTC+5. "
        "Pre-March-2024 SCADA timestamps cannot be tested; no earlier offset is inferred."
    )
    path = config.PROCESSED_DIR / "tz_report.json"
    path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(pd.DataFrame({"wind_corr": report["scores"], "temperature_diurnal_corr": temperature["scores"]}).to_string(float_format=lambda x: f"{x:.6f}"))
    for label, result in {"all": report, **report["per_period"]}.items():
        for signal, summary in (("wind", result), ("temperature", result["temperature_cross_check"])):
            print(f"{label} {signal}: best UTC{summary['best_offset_h']:+d}, "
                  f"runner-up UTC{summary['runner_up']['offset_h']:+d} "
                  f"({summary['runner_up']['corr']:.6f}), margin {summary['margin']:.6f}, "
                  f"{summary['status']}, n_hours={summary['n_hours']}")
    print(report["conclusion"])
    print(report["limitation"])
    print(f"report: {path}")


if __name__ == "__main__":
    main()
