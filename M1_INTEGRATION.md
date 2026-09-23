# M1 integration contract

## M2 → M1 `data/processed/weather_vintages.parquet`

M2 owns weather retrieval, historical-vintage selection, availability semantics, caching, and weather leakage validation. M1 validates the handoff schema and types, adds model-side feature aliases, and never decides whether a row was legally available.

The v1 file has exactly one row per `(issue_time, forecast_time, turbine_id)` and these columns:

| Column | M1 validation/use |
| --- | --- |
| `issue_time`, `forecast_time` | Required timezone-aware timestamps, normalized to UTC without changing their instants. `forecast_time` must equal `issue_time + lead_time_h`. |
| `turbine_id` | Required string, `T1` or `T2`. |
| `lead_time_h` | Required integer 1–48; retained and copied internally to `lead_time`. |
| `weather_run_id` | Required non-null string, retained in predictions. |
| `run_init_time` | Required timezone-aware timestamp, normalized to UTC and retained. |
| `available_at` | Required timezone-aware timestamp, normalized to UTC and retained unchanged otherwise. M1 does not compare it with `issue_time`. |
| `availability_basis` | Required non-null string, retained. M1 does not interpret it. |
| `nwp_lead_h` | Required non-negative numeric value, retained and used as a model feature. |
| `wind_speed_10m`, `wind_speed_80m`, `wind_speed_100m`, `wind_speed_120m` | Numeric, nullable forecast features. |
| `wind_direction_100m` | Numeric, nullable; transformed to sine/cosine features. |
| `wind_gusts_10m` | Numeric, nullable forecast feature. |
| `temperature_2m` | Numeric, nullable forecast feature. |
| `surface_pressure` | Numeric, nullable forecast feature. |
| `relative_humidity_2m` | Numeric, nullable forecast feature. |

The strict adapter rejects missing/extra columns, duplicate keys, naive timestamps, invalid turbine IDs, nonnumeric weather values, and inconsistent lead/forecast times. It does not fill missing weather values. Public M2 fields remain in the normalized table; internal `wx_` copies prevent forecast weather from being confused with observed SCADA.

Raw SCADA timestamps are naive. Weather-enabled commands therefore require an explicit `--scada-timezone`. M1 localizes SCADA with that declared timezone and converts it to UTC; it does not infer the timezone.

```powershell
python scripts/train.py `
  --weather data/processed/weather_vintages.parquet `
  --scada-timezone <verified-SCADA-timezone>

python scripts/evaluate.py --weather data/processed/weather_vintages.parquet

python scripts/predict.py `
  --weather data/processed/weather_vintages.parquet `
  --issue-time 2026-01-29T23:00:00Z
```

Weather runs use `models/lightgbm_weather` and `reports/evaluation_weather.csv`. The validation boundary is stored in the model artifact. The history-only fallback remains at `models/lightgbm`.

## M1 → M3 predictions

The flat output contains:

| Column | Meaning |
| --- | --- |
| `issue_time`, `forecast_time`, `turbine_id`, `lead_time` | Forecast identity and horizon. |
| `prediction` | Normalized active power clipped to `[0,1]`. |
| `model_name`, `model_version` | `lightgbm`, `persistence`, or `climatology` and its version. |
| `raw_prediction`, `was_clipped` | Unbounded model output and clipping indicator. |
| `lead_time_h`, `weather_run_id`, `run_init_time`, `available_at`, `availability_basis`, `nwp_lead_h` | M2 provenance when weather is used. |

M1 does not return ensembles or final uncertainty quantiles.

## SCADA rules

- Hourly power, wind, and temperature are means of six 10-minute samples by default.
- `observed_count` and `coverage` are retained; incomplete hours stay missing and are not interpolated.
- At issue time `T`, recent and rolling features end at hour `T-1h`; the current issue hour and all future hours are excluded.
- Latest observations older than six hours are suppressed. Rolling features retain their documented minimum sample rules.
