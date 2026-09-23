"""Compare energy on identical target hours against the latest publication."""
import pandas as pd

ENERGY_CHANGE_THRESHOLD = 0.10


def decide(candidate: pd.DataFrame, published: pd.DataFrame, errors: list[str]) -> dict:
    result = {"decision": "REJECT", "reason": "validation_errors", "version": 1,
              "parent_forecast_id": None, "energy_change_pct": None, "overlap_rows": 0}
    if errors:
        return result
    if published.empty:
        return {**result, "decision": "PUBLISH", "reason": "first_publication"}
    overlap = candidate.merge(published, on=["forecast_time", "turbine_id"],
                              suffixes=("_new", "_old"), validate="one_to_one")
    if overlap.empty:
        return {**result, "decision": "PUBLISH", "reason": "no_published_overlap"}
    old, new = float(overlap.p50_old.sum()), float(overlap.p50_new.sum())
    # A positive candidate against zero published energy is always material.
    change = abs(new - old) / old if old > 0 else (0.0 if new == 0 else None)
    material = change is None or change >= ENERGY_CHANGE_THRESHOLD
    version = int(published.version.iloc[0])
    return {**result, "decision": "PUBLISH" if material else "SHADOW",
            "reason": "energy_change_ge_threshold" if material else "energy_change_below_threshold",
            "version": version + 1 if material else version,
            "parent_forecast_id": str(published.forecast_id.iloc[0]),
            "energy_change_pct": None if change is None else change * 100,
            "zero_reference_energy": old == 0, "overlap_rows": len(overlap)}
