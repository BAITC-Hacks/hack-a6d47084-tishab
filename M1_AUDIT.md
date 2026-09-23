# M1 integration and leakage audit

## Ownership result

M1 reads an already selected M2 row and performs schema/type normalization plus model feature transformations. It contains no weather client, vintage selector, publication-time rule, `available_at <= issue_time` decision, weather cache, or weather fallback. `available_at` and `availability_basis` pass through as provenance. This matches the M2 v1 ownership boundary.

A contract test deliberately includes an `available_at` later than `issue_time` and verifies that M1 preserves it without accepting/rejecting it on legal-availability grounds; that decision remains M2's responsibility.

## Feature-by-feature temporal audit

For an issue at `T`, SCADA lookup is fixed at `T-1h`, the most recent complete hourly bin. Training and inference both call `build_examples` and `_history_at_issues`.

| LightGBM feature | Source and time range | Available at `T` / leakage result |
| --- | --- | --- |
| `recent_power` | Latest non-missing hourly power at or before `T-1h`; suppressed when older than six hours. | Historical only. The issue hour and target hours cannot enter. |
| `recent_wind` | Latest non-missing observed hourly wind at or before `T-1h`; same staleness rule. | Historical only. |
| `recent_temperature` | Latest non-missing observed hourly temperature at or before `T-1h`; same staleness rule. | Historical only. |
| `power_mean_24h` | Rolling mean ending at `T-1h`, minimum six observed hours. | Historical only; no target value enters. |
| `wind_mean_24h` | Rolling mean ending at `T-1h`, minimum six observed hours. | Historical only. |
| `temperature_mean_24h` | Rolling mean ending at `T-1h`, minimum six observed hours. | Historical only. |
| `power_mean_168h` | Rolling mean ending at `T-1h`, minimum 24 observed hours. | Historical only. |
| `power_age_hours` | Whole hours between `T` and the end of the latest valid completed power hour. | Derived solely from historical timestamps. |
| `observed_hours_24h` | Count of non-missing completed power hours in the window ending at `T-1h`. | Historical coverage only. |
| `target_hour`, `target_month`, `target_dayofweek` | Calendar values derived from `forecast_time`. | Known at issue time; contains no observed target value. |
| `lead_time` | `forecast_time - issue_time`, 1–48. | Known at issue time. |
| `turbine_code` | Stable mapping `T1=1`, `T2=2`. | Static identifier. |
| `wx_*` forecast features | Values in M2's already selected row for the issue, target hour, and turbine. Direction becomes sine/cosine. Missing values remain missing. | M2 certifies legal availability. M1 neither substitutes actual weather nor evaluates availability. |

Regression coverage mutates SCADA from `T` through the forecast horizon and verifies that every feature is unchanged while targets change. It also verifies `recent_power` equals the value from `T-1h`.

## Train/validation audit

- Existing validation start remains **2025-12-01 00:00** for the checked 48-hour, 60-day configuration.
- Training issues satisfy `issue_time < validation_start - 48h`; therefore the final training target is strictly before the validation boundary.
- Validation issues start at or after the boundary. A regression test builds both target timestamp sets and proves they are disjoint.
- Training feature history is calculated independently at each training issue and ends at `T-1h`.
- Climatology is fitted only from hourly history before the validation boundary.
- The supplied SCADA ends on 2026-01-31. The regression test confirms the reserved validation targets end before February 2026; February is not used for training or tuning.

## Synthetic M2 v1 test

The test fixture is generated in a temporary directory and contains four UTC issue times, both turbines, and 48 forecast hours per issue, with every required v1 field. It is not retained as data and is never used to report model performance.

The executed test covers:

```text
M2 v1 Parquet → strict adapter → M1 features → LightGBM train → 48h prediction
```

It asserts 96 LightGBM rows for one issue, both turbine IDs, leads 1–48, exact forecast timestamps, required provenance, output schema, and predictions within `[0,1]`.
