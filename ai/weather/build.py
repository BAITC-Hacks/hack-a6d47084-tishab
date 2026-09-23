"""Build the weather-vintage table (docs/CONTRACTS.md, section 2).

    python -m ai.weather.build --start 2024-04-16 --end 2026-02-27
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

import pandas as pd

from ai import config
from ai.weather.client import DownloadError, RunUnavailable, fetch_run
from ai.weather.vintage import WeatherRun, assert_legal, legal_runs, to_utc

Fetcher = Callable[[WeatherRun], pd.DataFrame]

COLUMNS = [
    "issue_time", "forecast_time", "turbine_id", "lead_time_h",
    "weather_run_id", "run_init_time", "available_at", "availability_basis", "nwp_lead_h",
    *config.WEATHER_VARIABLES,
]


def daily_issue_times(start, end) -> pd.DatetimeIndex:
    days = pd.date_range(pd.Timestamp(start).normalize(), pd.Timestamp(end).normalize(), freq="D", tz="UTC")
    return days + pd.Timedelta(hours=config.ISSUE_HOUR_UTC)


def build_vintage(issue_time, fetch: Fetcher = fetch_run) -> tuple[pd.DataFrame, dict]:
    """Weather rows for one issue time plus a provenance record.

    Uses the newest legal run that covers the full horizon; falls back to older legal
    runs when a newer one is missing or fails to download. Never uses an illegal run.
    """
    issue_time = to_utc(issue_time)
    horizon = pd.date_range(issue_time + pd.Timedelta(hours=1), periods=config.HORIZON_HOURS, freq="h")
    skipped = []
    for run in legal_runs(issue_time):
        assert_legal(run, issue_time)
        try:
            weather = fetch(run)
        except DownloadError as exc:
            skipped.append({"run": run.run_id, "reason": f"download_error: {exc}"})
            continue
        except RunUnavailable as exc:
            skipped.append({"run": run.run_id, "reason": str(exc)})
            continue
        window = weather.reindex(horizon)
        required = [v for v in config.WEATHER_VARIABLES if v not in config.NULLABLE_WEATHER_VARIABLES]
        if window[required].isna().any().any():
            skipped.append({"run": run.run_id, "reason": "horizon not fully covered"})
            continue
        return _rows(issue_time, run, window), {
            "issue_time": issue_time.isoformat(),
            "status": "ok",
            "weather_run_id": run.run_id,
            "run_init_time": run.init_time.isoformat(),
            "available_at": run.available_at.isoformat(),
            "availability_basis": run.availability_basis,
            "leakage_check": "pass",
            "skipped_runs": skipped,
        }
    return pd.DataFrame(columns=COLUMNS), {
        "issue_time": issue_time.isoformat(),
        "status": "no_legal_weather",
        "skipped_runs": skipped,
    }


def _rows(issue_time: pd.Timestamp, run: WeatherRun, window: pd.DataFrame) -> pd.DataFrame:
    base = window.reset_index().rename(columns={"index": "forecast_time"})
    base.insert(0, "issue_time", issue_time)
    base["lead_time_h"] = ((base.forecast_time - issue_time) / pd.Timedelta(hours=1)).astype(int)
    base["weather_run_id"] = run.run_id
    base["run_init_time"] = run.init_time
    base["available_at"] = run.available_at
    base["availability_basis"] = run.availability_basis
    base["nwp_lead_h"] = ((base.forecast_time - run.init_time) / pd.Timedelta(hours=1)).astype(int)
    frames = [base.assign(turbine_id=t) for t in config.TURBINES]
    return pd.concat(frames, ignore_index=True)[COLUMNS]


def validate_table(df: pd.DataFrame) -> None:
    """Contract invariants; raises AssertionError on violation."""
    assert (df.available_at <= df.issue_time).all(), "leakage: available_at > issue_time"
    assert df.lead_time_h.between(1, config.HORIZON_HOURS).all()
    assert df.groupby(["issue_time", "turbine_id"]).size().eq(config.HORIZON_HOURS).all()
    required = [c for c in COLUMNS if c not in config.NULLABLE_WEATHER_VARIABLES]
    assert not df[required].isna().any().any(), "unexpected NaN in weather table"
    assert not df.duplicated(["issue_time", "forecast_time", "turbine_id"]).any()


def build_table(issue_times, fetch: Fetcher = fetch_run, workers: int = 3) -> tuple[pd.DataFrame, list[dict]]:
    # Warm the cache in parallel; the sequential pass below then reads from disk.
    runs = {r for t in issue_times for r in legal_runs(t)[:2]}
    with ThreadPoolExecutor(workers) as pool:
        failures = [failure for failure in pool.map(
            lambda r: _try(fetch, r), sorted(runs, key=lambda r: r.init_time)
        ) if failure is not None]
    print(f"cache pre-warm: {len(runs)} runs, {len(failures)} download failures", flush=True)
    for failure in failures:
        print(f"  {failure['run']}: {failure['reason']}", flush=True)

    frames, provenance = [], []
    for t in issue_times:
        rows, prov = build_vintage(t, fetch)
        frames.append(rows)
        provenance.append(prov)
    populated = [f for f in frames if len(f)]
    table = pd.concat(populated, ignore_index=True) if populated else pd.DataFrame(columns=COLUMNS)
    validate_table(table)
    return table, provenance


def _try(fetch: Fetcher, run: WeatherRun) -> dict | None:
    try:
        fetch(run)
    except RunUnavailable:
        pass
    except DownloadError as exc:
        return {"run": run.run_id, "reason": str(exc)}
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--start", default="2024-04-16")
    parser.add_argument("--end", default="2026-02-27")
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--out", default=str(config.PROCESSED_DIR / "weather_vintages.parquet"))
    args = parser.parse_args()

    table, provenance = build_table(daily_issue_times(args.start, args.end), workers=args.workers)
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    table.to_parquet(args.out, index=False)
    prov = pd.DataFrame(provenance)
    prov.to_json(config.PROCESSED_DIR / "weather_vintages_provenance.jsonl", orient="records", lines=True)

    print(f"rows: {len(table)}  issue times: {table.issue_time.nunique()}  -> {args.out}")
    print(prov.status.value_counts().to_string())
    fallbacks = prov[(prov.status == "ok") & (prov.skipped_runs.map(len) > 0)]
    print(f"issue times that fell back to an older run: {len(fallbacks)}")


if __name__ == "__main__":
    main()
