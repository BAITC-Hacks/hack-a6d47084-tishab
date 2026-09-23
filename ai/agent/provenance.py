"""Single-writer, deterministic forecast storage and publication lookup."""
import json
from pathlib import Path

import pandas as pd


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


class Store:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "forecasts.parquet"

    def log(self, issue: pd.Timestamp, step: str, status: str, details: dict) -> None:
        record = {"ts": pd.Timestamp.now(tz="UTC").isoformat(), "issue_time": issue.isoformat(),
                  "step": step, "status": status, "details": details}
        with (self.root / "agent_log.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")

    def published(self, issue: pd.Timestamp, candidate: pd.DataFrame) -> pd.DataFrame:
        if not self.path.exists():
            return pd.DataFrame()
        table = pd.read_parquet(self.path)
        table = table[table.decision.eq("PUBLISH") & table.issue_time.lt(issue)]
        matching = table.merge(candidate[["forecast_time", "turbine_id"]],
                               on=["forecast_time", "turbine_id"])
        if matching.empty:
            return pd.DataFrame()
        latest = matching.sort_values(["issue_time", "forecast_id"]).forecast_id.iloc[-1]
        return table[table.forecast_id.eq(latest)]

    def existing(self, issue: pd.Timestamp, model_version: str | None, force_run: str | None) -> dict | None:
        if model_version is None:
            return None
        for path in sorted((self.root / "receipts").glob(f"F-{issue:%Y%m%dT%H}Z-{model_version}-v*.json")):
            receipt = json.loads(path.read_text(encoding="utf-8"))
            if receipt.get("force_run") == force_run:
                return receipt
        return None

    def save(self, forecast: pd.DataFrame | None, receipt: dict) -> None:
        if forecast is not None and receipt["decision"] != "REJECT":
            rows = forecast.copy()
            for column in ("forecast_id", "version", "parent_forecast_id", "weather_run_id", "status", "decision"):
                rows[column] = receipt[column]
            rows["issue_time"] = pd.Timestamp(receipt["issue_time"])
            rows["revision_reason"] = receipt["reason"]
            columns = ["forecast_id", "version", "parent_forecast_id", "issue_time", "weather_run_id",
                       "status", "decision", "revision_reason", "forecast_time", "turbine_id", "p50", "model_version"]
            for column in set(columns) - {"version", "issue_time", "forecast_time", "p50"}:
                rows[column] = rows[column].astype("string")
            table = pd.concat([pd.read_parquet(self.path), rows], ignore_index=True) if self.path.exists() else rows
            table = table[columns].sort_values(["issue_time", "forecast_id", "turbine_id", "forecast_time"]).reset_index(drop=True)
            table["version"] = table.version.astype("int64")
            table["p50"] = table.p50.astype("float64")
            temporary = self.path.with_suffix(".tmp.parquet")
            table.to_parquet(temporary, index=False)
            temporary.replace(self.path)
        folder = "receipts/forced" if receipt.get("force_run") else "receipts"
        write_json(self.root / folder / f"{receipt['forecast_id']}.json", receipt)
        write_json(self.root / "latest.json", receipt)
