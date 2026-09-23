"""Time-ordered holdout metrics for the three M1 predictors."""

import numpy as np
import pandas as pd


def evaluate(examples: pd.DataFrame, predictions: pd.DataFrame) -> pd.DataFrame:
    actual = examples[["issue_time", "forecast_time", "turbine_id", "lead_time", "target"]].dropna(subset=["target"])
    joined = predictions.merge(actual, on=["issue_time", "forecast_time", "turbine_id", "lead_time"], how="inner", validate="many_to_one")
    rows = []
    for (model, turbine, horizon), group in joined.groupby(["model_name", "turbine_id", "lead_time"]):
        error = group["prediction"].to_numpy() - group["target"].to_numpy()
        rows.append({"model_name": model, "turbine_id": turbine, "lead_time": int(horizon),
                     "count": len(group), "mae": float(np.abs(error).mean()),
                     "rmse": float(np.sqrt(np.square(error).mean()))})
    for (model, turbine), group in joined.groupby(["model_name", "turbine_id"]):
        error = group["prediction"].to_numpy() - group["target"].to_numpy()
        rows.append({"model_name": model, "turbine_id": turbine, "lead_time": "all",
                     "count": len(group), "mae": float(np.abs(error).mean()),
                     "rmse": float(np.sqrt(np.square(error).mean()))})
    for model, group in joined.groupby("model_name"):
        error = group["prediction"].to_numpy() - group["target"].to_numpy()
        rows.append({"model_name": model, "turbine_id": "all", "lead_time": "all",
                     "count": len(group), "mae": float(np.abs(error).mean()),
                     "rmse": float(np.sqrt(np.square(error).mean()))})
    return pd.DataFrame(rows)
