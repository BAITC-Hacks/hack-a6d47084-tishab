"""Per-turbine isotonic baselines and January 2026 holdout evaluation.

    python3 -m ai.power_curve

Training inputs must already be restricted to times strictly before cutoff.
Evaluation uses January issue and target times, with a model frozen on January 1.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression

from ai import config
from ai.weather.vintage import LeakageError, to_utc

MODEL_VERSION = "powercurve-v1"
EVAL_CUTOFF = pd.Timestamp("2026-01-01", tz="UTC")
EVAL_END = pd.Timestamp("2026-02-01", tz="UTC")
FINAL_CUTOFF = pd.Timestamp("2026-01-31T07:00Z")


def _utc_columns(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    frame = frame.copy()
    for column in columns:
        values = frame[column]
        if not isinstance(values.dtype, pd.DatetimeTZDtype):
            raise ValueError(f"{column} must be timezone-aware")
        if values.isna().any():
            raise ValueError(f"{column} contains missing timestamps")
        frame[column] = values.dt.tz_convert("UTC")
    return frame


def _weather(frame: pd.DataFrame) -> pd.DataFrame:
    frame = _utc_columns(frame, ["forecast_time", "issue_time", "available_at"])
    if frame.available_at.gt(frame.issue_time).any():
        raise LeakageError("weather available_at > issue_time")
    return frame


@dataclass
class PowerCurveModel:
    curves: dict
    cutoff: pd.Timestamp
    fitted_at: pd.Timestamp
    training_counts: dict
    model_version: str = MODEL_VERSION

    def _predict_curve(self, wind, turbine_id: str, kind: str) -> np.ndarray:
        curve = self.curves[turbine_id][kind]
        return np.interp(np.asarray(wind, dtype=float), curve["X_"], curve["y_"])

    def expected_power(self, wind, turbine_id: str) -> np.ndarray:
        """Physics curve; values outside the fitted wind range clip to endpoints."""
        return self._predict_curve(wind, turbine_id, "physics")

    def predict(self, weather_rows: pd.DataFrame) -> pd.DataFrame:
        weather = _weather(weather_rows).reset_index(drop=True)
        if not weather.turbine_id.isin(self.curves).all():
            raise ValueError("unknown turbine_id")
        result = weather[["forecast_time", "turbine_id"]].copy()
        result["p50"] = np.nan
        for turbine_id in self.curves:
            mask = weather.turbine_id.eq(turbine_id)
            result.loc[mask, "p50"] = self._predict_curve(
                weather.loc[mask, "wind_speed_100m"], turbine_id, "forecast")
        result["model_version"] = self.model_version
        return result

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {"model_version": self.model_version, "cutoff": self.cutoff.isoformat(),
                  "fitted_at": self.fitted_at.isoformat(), "curves": self.curves,
                  "training_counts": self.training_counts}
        path.write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")

    @classmethod
    def load(cls, path: str | Path) -> "PowerCurveModel":
        record = json.loads(Path(path).read_text())
        if record["model_version"] != MODEL_VERSION:
            raise ValueError("unsupported model version")
        return cls(record["curves"], to_utc(record["cutoff"]),
                   to_utc(record["fitted_at"]), record["training_counts"])


def _fit_curve(x: pd.Series, y: pd.Series) -> dict:
    if len(x) == 0 or not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("curve training requires nonempty finite valid samples")
    curve = IsotonicRegression(increasing=True, y_min=0, y_max=1, out_of_bounds="clip").fit(x, y)
    return {"X_": curve.X_thresholds_.tolist(), "y_": curve.y_thresholds_.tolist()}


def fit(weather: pd.DataFrame, scada: pd.DataFrame, cutoff: pd.Timestamp) -> PowerCurveModel:
    cutoff = to_utc(cutoff)
    if cutoff > FINAL_CUTOFF:
        raise ValueError(f"cutoff cannot extend past {FINAL_CUTOFF.isoformat()}")
    weather = _weather(weather)
    scada = _utc_columns(scada, ["timestamp"])
    if weather.forecast_time.ge(cutoff).any():
        raise ValueError("forecast_time >= cutoff in training input")
    if scada.timestamp.ge(cutoff).any() or (scada.timestamp + pd.Timedelta(hours=1)).gt(cutoff).any():
        raise ValueError("SCADA hour is not fully observed before cutoff")
    valid = scada.loc[scada.is_valid].copy()
    pairs = weather.merge(valid, left_on=["forecast_time", "turbine_id"],
                          right_on=["timestamp", "turbine_id"], validate="many_to_one")
    curves, counts = {}, {}
    for turbine_id in config.TURBINES:
        observed = valid[valid.turbine_id.eq(turbine_id)]
        forecast = pairs[pairs.turbine_id.eq(turbine_id)]
        curves[turbine_id] = {
            "physics": _fit_curve(observed.wind_speed, observed.power),
            "forecast": _fit_curve(forecast.wind_speed_100m, forecast.power),
        }
        counts[turbine_id] = {"physics": len(observed), "forecast": len(forecast)}
    return PowerCurveModel(curves, cutoff, pd.Timestamp.now(tz="UTC"), counts)


def persistence(weather: pd.DataFrame, scada: pd.DataFrame) -> np.ndarray:
    """Last nonmissing observed power, including flagged hours, fully completed by issue."""
    weather = _weather(weather).reset_index(drop=True)
    scada = _utc_columns(scada, ["timestamp"])
    result = np.full(len(weather), np.nan)
    for turbine_id, rows in weather.groupby("turbine_id"):
        observed = scada[scada.turbine_id.eq(turbine_id) & np.isfinite(scada.power)].copy()
        observed["observed_at"] = observed.timestamp + pd.Timedelta(hours=1)
        left = rows[["issue_time"]].assign(position=rows.index).sort_values("issue_time")
        joined = pd.merge_asof(left, observed[["observed_at", "power"]].sort_values("observed_at"),
                               left_on="issue_time", right_on="observed_at", direction="backward")
        result[joined.position.to_numpy()] = joined.power.to_numpy()
    return result


def evaluate(model: PowerCurveModel, weather: pd.DataFrame, scada: pd.DataFrame) -> dict:
    weather = _weather(weather)
    scada = _utc_columns(scada, ["timestamp"])
    if model.cutoff != EVAL_CUTOFF:
        raise ValueError("January evaluation requires a January 1 training cutoff")
    selected = weather[weather.issue_time.ge(EVAL_CUTOFF) & weather.forecast_time.ge(EVAL_CUTOFF)
                       & weather.forecast_time.lt(EVAL_END)].copy()
    targets = scada[scada.timestamp.lt(EVAL_END) & scada.is_valid]
    pairs = selected.merge(targets[["timestamp", "turbine_id", "power"]],
                           left_on=["forecast_time", "turbine_id"],
                           right_on=["timestamp", "turbine_id"], validate="many_to_one")
    pairs["power_curve"] = model.predict(pairs).p50.to_numpy()
    pairs["persistence"] = persistence(pairs, scada[scada.timestamp.lt(EVAL_END)])
    pairs["lead_bucket"] = np.where(pairs.lead_time_h.le(24), "1-24", "25-48")
    metrics = []
    for (turbine_id, bucket), group in pairs.groupby(["turbine_id", "lead_bucket"]):
        # Both baselines are scored on the same available targets.
        usable = group[["power", "power_curve", "persistence"]].notna().all(axis=1)
        for method in ("power_curve", "persistence"):
            error = group.loc[usable, method] - group.loc[usable, "power"]
            metrics.append({"turbine_id": turbine_id, "lead_bucket_h": bucket, "method": method,
                            "n": len(error), "excluded": int((~usable).sum()),
                            "mae": float(error.abs().mean()) if len(error) else None,
                            "rmse": float(np.sqrt((error ** 2).mean())) if len(error) else None})
    return {"label": "holdout Jan 2026, not the organizer metric", "cutoff": model.cutoff.isoformat(),
            "evaluation": "January issue times and January target hours only; is_valid targets",
            "persistence": "Last finite observed power with timestamp + 1h <= issue_time; flagged observations retained",
            "training_counts": model.training_counts, "metrics": metrics}


def main() -> None:
    weather = pd.read_parquet(config.PROCESSED_DIR / "weather_vintages.parquet")
    scada = pd.read_parquet(config.PROCESSED_DIR / "scada_hourly.parquet")
    model = fit(weather[weather.forecast_time.lt(EVAL_CUTOFF)],
                scada[scada.timestamp.lt(EVAL_CUTOFF)], EVAL_CUTOFF)
    report = evaluate(model, weather, scada)
    path = config.PROCESSED_DIR / "power_curve_eval.json"
    path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(report["label"])
    print(pd.DataFrame(report["metrics"]).to_string(index=False, float_format=lambda x: f"{x:.6f}"))
    final = fit(weather[weather.forecast_time.lt(FINAL_CUTOFF)],
                scada[(scada.timestamp + pd.Timedelta(hours=1)).le(FINAL_CUTOFF)], FINAL_CUTOFF)
    model_path = config.ROOT / "models" / "power_curve_v1.json"
    final.save(model_path)
    print(f"final training counts: {final.training_counts}")
    print(f"evaluation: {path}\nfinal model: {model_path}")


if __name__ == "__main__":
    main()
