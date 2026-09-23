"""Deterministic forecast loop, receipts and optional Russian operator briefing.

    python3 -m ai.agent.run --issue 2026-02-14T07:00Z --offline --llm off
    python3 -m ai.agent.run --replay 2026-01-31T07:00Z 2026-02-27T07:00Z --offline --llm off

Revisions add 6, 12 and 18 hours to daily issues, capped at the replay's last issue.
The saved model's training cutoff must not be later than the issue time.
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import sys
from typing import Callable

import numpy as np
import pandas as pd

from ai import config
from ai.agent.llm import PRECISION, brief
from ai.agent.policy import decide
from ai.agent.predictors import Predictor, failure_message, load_predictor
from ai.agent.provenance import Store
from ai.power_curve import PowerCurveModel
from ai.weather.build import _rows
from ai.weather.client import DownloadError, RunUnavailable, fetch_run
from ai.weather.vintage import LeakageError, WeatherRun, assert_legal, legal_runs, to_utc

PHYSICS_TOLERANCE = 0.4
FORECAST_COLUMNS = ["forecast_time", "turbine_id", "p50", "model_version"]


def horizon(issue: pd.Timestamp) -> pd.DatetimeIndex:
    return pd.date_range(issue + pd.Timedelta(hours=1), periods=config.HORIZON_HOURS, freq="h")


def validate_weather(window: pd.DataFrame, issue: pd.Timestamp) -> dict:
    errors, warnings = [], []
    if window.index.tz is None:
        errors.append("naive_weather_time")
    if not window.index.equals(horizon(issue)):
        errors.append("weather_horizon_mismatch")
    for variable in config.WEATHER_VARIABLES:
        if variable not in window:
            errors.append(f"missing_variable:{variable}")
            continue
        values = window[variable]
        if variable not in config.NULLABLE_WEATHER_VARIABLES and not np.isfinite(values).all():
            errors.append(f"missing_or_nonfinite:{variable}")
        if variable.startswith("wind_speed") or variable == "wind_gusts_10m":
            bounds = (0, 60)
        elif variable == "temperature_2m":
            bounds = (-60, 60)
        elif variable == "surface_pressure":
            bounds = (800, 1100)
        else:
            continue
        if (values.notna() & ~values.between(*bounds)).any():
            warnings.append(f"out_of_range:{variable}")
    return {"errors": errors, "warnings": warnings}


def validate_forecast(forecast: pd.DataFrame, weather: pd.DataFrame, issue: pd.Timestamp,
                      physics=None, tolerance: float = PHYSICS_TOLERANCE) -> dict:
    errors, warnings = [], []
    if not set(FORECAST_COLUMNS) <= set(forecast.columns):
        return {"errors": ["missing_forecast_columns"], "warnings": []}
    if not isinstance(forecast.forecast_time.dtype, pd.DatetimeTZDtype):
        errors.append("naive_forecast_time")
    if forecast[FORECAST_COLUMNS].isna().any().any():
        errors.append("missing_forecast_values")
    if not pd.api.types.is_numeric_dtype(forecast.p50) or not forecast.p50.between(0, 1).all():
        errors.append("power_out_of_bounds")
    if forecast.model_version.nunique() != 1:
        errors.append("model_version_mismatch")
    if set(forecast.turbine_id) != set(config.TURBINES):
        errors.append("turbines_mismatch")
    for turbine in config.TURBINES:
        times = pd.DatetimeIndex(forecast.loc[forecast.turbine_id.eq(turbine), "forecast_time"]).sort_values()
        if not times.equals(horizon(issue)):
            errors.append(f"forecast_horizon_mismatch:{turbine}")
    if not errors and physics is not None:
        paired = forecast.merge(weather, on=["forecast_time", "turbine_id"], validate="one_to_one")
        for turbine, group in paired.groupby("turbine_id"):
            expected = physics.expected_power(group.wind_speed_100m.to_numpy(), turbine)
            if (np.abs(group.p50.to_numpy() - expected) > tolerance).any():
                warnings.append(f"physics_deviation:{turbine}")
    return {"errors": errors, "warnings": warnings}


def facts_for(receipt: dict, forecast: pd.DataFrame | None) -> dict:
    facts = {key: receipt.get(key) for key in (
        "issue_time", "weather_run_id", "available_at", "availability_basis", "decision", "reason")}
    change = receipt.get("energy_change_pct")
    facts["energy_change_pct"] = round(change, PRECISION) if change is not None else None
    facts["warnings"] = receipt["validation"]["weather"]["warnings"] + receipt["validation"]["forecast"]["warnings"]
    facts["power"] = {}
    if forecast is not None and receipt["decision"] != "REJECT":
        for turbine, rows in forecast.groupby("turbine_id"):
            facts["power"][turbine] = {key: round(float(value), PRECISION) for key, value in
                                       rows.p50.agg(["min", "max", "mean"]).items()}
    return facts


def run_issue(issue_time, predictor: Predictor, store: Store, *, offline: bool = False,
              llm_mode: str = "off", force_run=None, fetch: Callable | None = None,
              physics_tolerance: float = PHYSICS_TOLERANCE) -> dict:
    issue = to_utc(issue_time)
    if pd.isna(issue) or issue != issue.floor("h"):
        raise ValueError("issue_time must be an exact UTC hour")
    if callable(getattr(predictor, "prepare", None)):
        predictor.prepare(issue)
    forced = WeatherRun.from_init(to_utc(force_run)) if force_run is not None else None
    model_version = getattr(predictor, "model_version", None)
    try:
        raw_cutoff = getattr(predictor, "cutoff", None)
        cutoff = to_utc(raw_cutoff) if raw_cutoff is not None else None
        if pd.isna(cutoff):
            cutoff = None
    except (ValueError, TypeError):
        cutoff = None
    existing = (store.existing(issue, model_version, forced.run_id if forced else None)
                if cutoff is not None and cutoff <= issue else None)
    if existing and existing.get("model_cutoff") != cutoff.isoformat():
        existing = None
    if existing and not forced:
        # Replaying into the same directory is idempotent.
        store.log(issue, "store", "reused", {"forecast_id": existing["forecast_id"]})
        return existing
    receipt = {"issue_time": issue.isoformat(), "weather_run_id": None, "run_init_time": None,
               "available_at": None, "availability_basis": None, "model_version": model_version or "unknown",
               "model_cutoff": None, "offline": offline, "force_run": forced.run_id if forced else None,
               "leakage_check": "not_checked", "skipped_runs": [],
               "validation": {"weather": {"errors": [], "warnings": []},
                              "forecast": {"errors": [], "warnings": []}}}
    forecast, weather_rows, chosen = None, None, None
    errors = []
    runs = [forced] if forced else legal_runs(issue)
    for run in runs:
        metadata = {"weather_run_id": run.run_id, "run_init_time": run.init_time.isoformat(),
                    "available_at": run.available_at.isoformat(), "availability_basis": run.availability_basis}
        receipt.update(metadata)
        store.log(issue, "select_weather", "candidate", {**metadata, "skipped_runs": receipt["skipped_runs"]})
        try:
            assert_legal(run, issue)
        except LeakageError:
            receipt["leakage_check"] = "rejected"
            errors.append("future_weather")
            store.log(issue, "leakage_check", "rejected", metadata)
            print("FORECAST REJECTED — future information")
            break
        receipt["leakage_check"] = "pass"
        store.log(issue, "leakage_check", "pass", metadata)
        try:
            raw = fetch(run) if fetch is not None else fetch_run(run, offline=offline)
        except (RunUnavailable, DownloadError) as exc:
            reason = f"download_error: {exc}" if isinstance(exc, DownloadError) else str(exc)
            receipt["skipped_runs"].append({"run": run.run_id, "reason": reason})
            store.log(issue, "fetch_weather", "unavailable", {"run": run.run_id, "reason": reason})
            continue
        store.log(issue, "fetch_weather", "ok", {"run": run.run_id, "offline": offline})
        if not isinstance(raw.index, pd.DatetimeIndex) or raw.index.tz is None or raw.index.has_duplicates:
            validation = {"errors": ["invalid_weather_index"], "warnings": []}
        else:
            raw = raw.copy()
            raw.index = raw.index.tz_convert("UTC")
            window = raw.reindex(horizon(issue))
            validation = validate_weather(window, issue)
        receipt["validation"]["weather"] = validation
        store.log(issue, "validate_weather", "rejected" if validation["errors"] else "ok", validation)
        if validation["errors"]:
            receipt["skipped_runs"].append({"run": run.run_id, "reason": ";".join(validation["errors"])})
            continue
        chosen = run
        weather_rows = _rows(issue, run, window)
        store.log(issue, "select_weather", "selected", {**metadata, "skipped_runs": receipt["skipped_runs"]})
        break
    if chosen is None and not errors:
        errors.append("no_legal_weather")
        receipt["weather_run_id"] = None
        receipt["validation"]["weather"]["errors"].append("no_legal_weather")
    if chosen is not None:
        if cutoff is None:
            errors.append("cutoff_unknown")
            receipt["leakage_check"] = "rejected"
            store.log(issue, "leakage_check", "rejected", {"reason": "cutoff_unknown"})
        else:
            receipt["model_cutoff"] = cutoff.isoformat()
            if cutoff > issue:
                errors.append("model_cutoff_after_issue")
                receipt["leakage_check"] = "rejected"
                store.log(issue, "leakage_check", "rejected", {"reason": errors[-1], "model_cutoff": cutoff.isoformat()})
        if not errors:
            try:
                assert_legal(chosen, issue)
                forecast = predictor.predict(weather_rows.copy())
                store.log(issue, "predict", "ok", {"rows": len(forecast)})
                physics = PowerCurveModel.load(config.ROOT / "models" / "power_curve_v1.json")
                validation = validate_forecast(forecast, weather_rows, issue, physics, physics_tolerance)
                receipt["validation"]["forecast"] = validation
                errors.extend(validation["errors"])
                store.log(issue, "validate_forecast", "rejected" if errors else "ok", validation)
                if not errors:
                    receipt["model_version"] = str(forecast.model_version.iloc[0])
                    forecast = forecast[FORECAST_COLUMNS].copy()
                    if model_version is None and not forced:
                        existing = store.existing(issue, receipt["model_version"], None)
                        if existing:
                            store.log(issue, "store", "reused", {"forecast_id": existing["forecast_id"]})
                            return existing
            except Exception as exc:
                errors.append(f"predictor_failed: {failure_message(exc)}")
                store.log(issue, "predict", "rejected", {"reason": errors[-1]})
    receipt["errors"] = errors
    published = store.published(issue, forecast) if not errors and forecast is not None else pd.DataFrame()
    decision = decide(forecast, published, errors)
    if errors:
        decision["reason"] = errors[0]
    receipt.update(decision)
    receipt["status"] = {"PUBLISH": "published", "SHADOW": "shadow", "REJECT": "rejected"}[receipt["decision"]]
    receipt["forecast_id"] = f"F-{issue:%Y%m%dT%H}Z-{receipt['model_version']}-v{receipt['version']}"
    store.log(issue, "decide", receipt["decision"], decision)
    store.save(forecast, receipt)
    store.log(issue, "store", "ok", {"forecast_id": receipt["forecast_id"], "decision": receipt["decision"]})
    facts = facts_for(receipt, forecast)
    briefing = brief(facts, llm_mode)
    receipt["facts"], receipt["briefing"] = facts, briefing
    store.save(None, receipt)
    store.log(issue, "brief", "ok", {"llm_used": briefing["llm_used"], "reason": briefing["reason"]})
    return receipt


def issue_schedule(start, end, revisions: bool = True) -> list[pd.Timestamp]:
    start, end = to_utc(start), to_utc(end)
    if start.hour != config.ISSUE_HOUR_UTC or end.hour != config.ISSUE_HOUR_UTC or start > end:
        raise ValueError("replay endpoints must be ordered daily 07:00 UTC issues")
    if start != start.floor("h") or end != end.floor("h"):
        raise ValueError("replay endpoints must be exact hours")
    return [day + pd.Timedelta(hours=delta) for day in pd.date_range(start, end, freq="D")
            for delta in ((0, 6, 12, 18) if revisions else (0,))
            if day + pd.Timedelta(hours=delta) <= end]


def main(argv=None) -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--issue")
    mode.add_argument("--replay", nargs=2)
    parser.add_argument("--llm", choices=["on", "off"], default="off")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--revisions", choices=["on", "off"], default="on")
    parser.add_argument("--force-run")
    parser.add_argument("--out", type=Path, default=config.ROOT / "outputs")
    parser.add_argument("--model", type=Path, default=config.ROOT / "models" / "power_curve_v1.json")
    parser.add_argument("--predictor", choices=["powercurve", "m1"], default="powercurve")
    parser.add_argument("--physics-tolerance", type=float, default=PHYSICS_TOLERANCE)
    args = parser.parse_args(argv)
    if args.force_run and not args.issue:
        parser.error("--force-run requires --issue")
    if not np.isfinite(args.physics_tolerance) or args.physics_tolerance < 0:
        parser.error("--physics-tolerance must be finite and nonnegative")
    predictor = load_predictor(args.model, predictor=args.predictor)
    store = Store(args.out)
    if args.replay:
        issues = issue_schedule(*args.replay, revisions=args.revisions == "on")
    else:
        issue = to_utc(args.issue)
        issues = ([issue + pd.Timedelta(hours=h) for h in (0, 6, 12, 18)]
                  if args.revisions == "on" and not args.force_run
                  and issue.hour == config.ISSUE_HOUR_UTC else [issue])
    results = []
    for issue in issues:
        receipt = run_issue(issue, predictor, store, offline=args.offline, llm_mode=args.llm,
                            force_run=args.force_run, physics_tolerance=args.physics_tolerance)
        results.append(receipt)
        print(f"{issue.isoformat()} {receipt['decision']} {receipt['reason']} {receipt['forecast_id']}", flush=True)
        if not args.replay:
            print(receipt["briefing"]["text"])
    print(f"issues: {len(results)} decisions: {dict(Counter(r['decision'] for r in results))}")


if __name__ == "__main__":
    main()
