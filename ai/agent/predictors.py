"""Model-independent predictors, including the external M1 command-line adapter."""
import json
import os
import subprocess
import sys
import tempfile
from typing import Protocol
from pathlib import Path

import pandas as pd

from ai import config
from ai.power_curve import PowerCurveModel
from ai.weather.vintage import to_utc


class Predictor(Protocol):
    def predict(self, weather_rows: pd.DataFrame) -> pd.DataFrame:
        """Return forecast_time, turbine_id, p50, model_version."""
        ...


class PredictorError(RuntimeError):
    """An external predictor failed to produce a usable result."""


def failure_message(exc: Exception) -> str:
    message = str(exc)
    for name, value in os.environ.items():
        if value and any(word in name.upper() for word in ("KEY", "TOKEN", "SECRET", "PASSWORD")):
            message = message.replace(value, "[redacted]")
    return " ".join(message.split())[:500] or type(exc).__name__


class M1Predictor:
    def __init__(self, directory: Path | None = None, timeout: float = 120):
        configured = directory or os.getenv("M1_DIR")
        self.directory = Path(configured).expanduser().resolve() if configured else None
        self.timeout = timeout
        self.cutoff = None
        self.model_version = "m1-lgbm-v1"
        try:
            if self.directory is None:
                return
            metadata = json.loads((self.directory / "models/lightgbm_weather/metadata.json").read_text())
            self.model_version = metadata.get("model_version") or self.model_version
            if "cutoff" in metadata:
                cutoff = to_utc(metadata["cutoff"])
            else:
                cutoff = to_utc(metadata["training_target_end"]) + pd.Timedelta(hours=1)
            if not pd.isna(cutoff):
                self.cutoff = cutoff
        except (OSError, ValueError, TypeError, KeyError):
            # Missing/invalid metadata is rejected by the loop as cutoff_unknown.
            self.cutoff = None

    def predict(self, weather_rows: pd.DataFrame) -> pd.DataFrame:
        try:
            if self.directory is None:
                raise PredictorError("M1_DIR is not configured")
            if weather_rows.issue_time.nunique() != 1:
                raise PredictorError("M1 requires exactly one issue time")
            issue = to_utc(weather_rows.issue_time.iloc[0])
            with tempfile.TemporaryDirectory(prefix="m1-predict-") as temporary:
                weather = Path(temporary) / "weather_vintages.parquet"
                output = Path(temporary) / "predictions.csv"
                weather_rows.to_parquet(weather, index=False)
                process = subprocess.run(
                    [sys.executable, "scripts/predict.py", "--weather", str(weather),
                     "--issue-time", issue.isoformat(), "--output", str(output)],
                    cwd=self.directory, capture_output=True, text=True, timeout=self.timeout,
                )
                if process.returncode:
                    detail = process.stderr.strip().splitlines()
                    message = detail[-1] if detail else "no error details"
                    raise PredictorError(f"M1 predict.py exited {process.returncode}: {message}")
                predictions = pd.read_csv(output)
            predictions = predictions.loc[predictions.model_name.eq("lightgbm")].copy()
            if predictions.empty:
                raise PredictorError("M1 output has no lightgbm rows")
            result = predictions.rename(columns={"prediction": "p50"})[
                ["forecast_time", "turbine_id", "p50", "model_version"]].copy()
            # Reject naive output timestamps rather than silently assuming a zone.
            result["forecast_time"] = pd.to_datetime([to_utc(value) for value in result.forecast_time], utc=True)
            result["p50"] = pd.to_numeric(result.p50, errors="raise")
            return result
        except subprocess.TimeoutExpired as exc:
            raise PredictorError(f"M1 predict.py timed out after {self.timeout:g}s") from exc
        except Exception as exc:
            raise PredictorError(failure_message(exc)) from exc


def load_predictor(path: Path | None = None, predictor: str = "powercurve") -> Predictor:
    if predictor == "m1":
        return M1Predictor()
    if predictor != "powercurve":
        raise ValueError(f"unknown predictor: {predictor}")
    return PowerCurveModel.load(path or config.ROOT / "models" / "power_curve_v1.json")
