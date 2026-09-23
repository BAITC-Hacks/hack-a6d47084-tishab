"""Shared LightGBM model plus persistence and climatology baselines."""

import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor

from .features import KEYS, OPTIONAL_PROVENANCE, PROVENANCE, feature_columns

MODEL_CONFIG = {
    "n_estimators": 350,
    "learning_rate": 0.05,
    "num_leaves": 31,
    "min_child_samples": 100,
    "colsample_bytree": 0.9,
    "subsample": 0.9,
    "subsample_freq": 1,
    "random_state": 42,
    "n_jobs": 4,
    "deterministic": True,
    "force_col_wise": True,
    "verbosity": -1,
}
FEATURE_VERSION = "m1-v1"
OUTPUT_COLUMNS = KEYS + ["prediction", "model_name", "model_version"]


class M1Forecaster:
    def __init__(self, version: str = "m1-lgbm-v1") -> None:
        self.version = version
        self.model: LGBMRegressor | None = None
        self.columns: list[str] = []
        self.climatology: dict[tuple[str, int, int], float] = {}
        self.turbine_mean: dict[str, float] = {}
        self.global_mean: float = float("nan")
        self.metadata: dict = {}

    def train(self, examples: pd.DataFrame, hourly_history: pd.DataFrame) -> "M1Forecaster":
        training = examples.loc[examples["target"].notna()].copy()
        if training.empty:
            raise ValueError("No observed training targets")
        self.columns = feature_columns(training)
        if training[self.columns].isna().all().any():
            empty = training[self.columns].columns[training[self.columns].isna().all()].tolist()
            raise ValueError(f"Features wholly missing: {empty}")
        self.model = LGBMRegressor(**MODEL_CONFIG)
        self.model.fit(training[self.columns], training["target"])
        history = hourly_history.loc[hourly_history["power"].notna()].copy()
        if history.empty:
            raise ValueError("No observed history for climatology")
        history["month"] = history["hour_start"].dt.month
        history["hour"] = history["hour_start"].dt.hour
        means = history.groupby(["turbine_id", "month", "hour"])["power"].mean()
        self.climatology = {tuple(k): float(v) for k, v in means.items()}
        self.turbine_mean = {str(k): float(v) for k, v in history.groupby("turbine_id")["power"].mean().items()}
        self.global_mean = float(history["power"].mean())
        self.metadata = {
            "model_name": "lightgbm",
            "model_version": self.version,
            "feature_version": FEATURE_VERSION,
            "feature_columns": self.columns,
            "target": "hourly mean normalized active power [0,1] from complete 10-minute bins",
            "training_issue_start": str(training["issue_time"].min()),
            "training_issue_end": str(training["issue_time"].max()),
            "training_target_end": str(training["forecast_time"].max()),
            "training_rows": len(training),
            "turbines": sorted(training["turbine_id"].unique().tolist()),
            "config": MODEL_CONFIG,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "weather_features": [c for c in self.columns if c.startswith("wx_")],
            "timestamp_convention": "naive; SCADA source timezone TBD; issue and M2 weather must match",
        }
        return self

    def _check_features(self, examples: pd.DataFrame) -> None:
        if self.model is None:
            raise ValueError("Model is not trained")
        missing = set(self.columns) - set(examples.columns)
        if missing:
            raise ValueError(f"Missing model features: {sorted(missing)}")
        current = feature_columns(examples)
        if current != self.columns:
            raise ValueError(f"Feature schema mismatch: artifact={self.columns}, input={current}")
        if examples[KEYS].isna().any().any() or examples.duplicated(KEYS).any():
            raise ValueError("Prediction keys must be non-null and unique")

    def _climatology(self, examples: pd.DataFrame) -> np.ndarray:
        values = []
        for row in examples.itertuples(index=False):
            turbine = str(row.turbine_id)
            value = self.climatology.get((turbine, int(row.target_month), int(row.target_hour)))
            values.append(value if value is not None else self.turbine_mean.get(turbine, self.global_mean))
        return np.asarray(values, dtype=float)

    def predict(self, examples: pd.DataFrame, models: tuple[str, ...] = ("lightgbm", "persistence", "climatology")) -> pd.DataFrame:
        self._check_features(examples)
        provenance = [c for c in PROVENANCE + OPTIONAL_PROVENANCE if c in examples.columns]
        base = examples[KEYS + provenance].copy()
        climo = self._climatology(examples)
        outputs = []
        for name in models:
            if name == "lightgbm":
                raw = self.model.predict(examples[self.columns])
                prediction = np.clip(raw, 0.0, 1.0)
                version = self.version
            elif name == "persistence":
                if "recent_power" not in examples:
                    raise ValueError("Persistence requires recent_power")
                prediction = np.where(examples["recent_power"].notna(), examples["recent_power"], climo)
                raw = prediction
                version = "persistence-v1"
            elif name == "climatology":
                prediction = climo
                raw = prediction
                version = "climatology-v1"
            else:
                raise ValueError(f"Unknown model: {name}")
            result = base.copy()
            result["prediction"] = prediction.astype(float)
            result["model_name"] = name
            result["model_version"] = version
            if name == "lightgbm":
                result["raw_prediction"] = raw.astype(float)
                result["was_clipped"] = ~np.isclose(raw, prediction)
            else:
                result["raw_prediction"] = prediction.astype(float)
                result["was_clipped"] = False
            outputs.append(result)
        combined = pd.concat(outputs, ignore_index=True)
        if combined["prediction"].isna().any() or not combined["prediction"].between(0, 1).all():
            raise ValueError("Non-finite or out-of-range forecast")
        return combined.sort_values(["model_name", *KEYS]).reset_index(drop=True)

    def save(self, artifact_dir: str | Path) -> None:
        if self.model is None:
            raise ValueError("Model is not trained")
        root = Path(artifact_dir)
        root.mkdir(parents=True, exist_ok=True)
        joblib.dump({
            "model": self.model, "columns": self.columns, "climatology": self.climatology,
            "turbine_mean": self.turbine_mean, "global_mean": self.global_mean,
            "metadata": self.metadata,
        }, root / "model.joblib")
        (root / "metadata.json").write_text(json.dumps(self.metadata, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, artifact_dir: str | Path) -> "M1Forecaster":
        payload = joblib.load(Path(artifact_dir) / "model.joblib")
        result = cls(payload["metadata"]["model_version"])
        result.model = payload["model"]
        result.columns = payload["columns"]
        result.climatology = payload["climatology"]
        result.turbine_mean = payload["turbine_mean"]
        result.global_mean = payload["global_mean"]
        result.metadata = payload["metadata"]
        return result
