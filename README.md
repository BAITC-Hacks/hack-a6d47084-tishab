# TISHAB wind forecasting — M1 core model

This repository currently contains the M1 forecasting workstream: reusable SCADA preprocessing, a shared two-turbine LightGBM model, persistence and climatology baselines, time-ordered evaluation, model persistence, and a 1–48 hour prediction interface.

Weather retrieval/vintage validation, Power Curve, TFT, ensembles, uncertainty, FastAPI, React, and LLM orchestration belong to M2/M3 and are intentionally absent.

## Setup

```powershell
python -m pip install -r requirements.txt
```

The two supplied turbine CSVs remain in the repository root. Their timestamps are timezone-naive. History-only runs retain that convention. Weather-enabled runs require an explicit `--scada-timezone`, then convert SCADA to UTC to match M2 without inferring the source timezone.

## Commands

```powershell
# Train the history-only fallback and reserve the final 60 issue days
python scripts/train.py

# Evaluate LightGBM, persistence, and climatology on the reserved period
python scripts/evaluate.py

# Generate 48 hours for both turbines and all three predictors
python scripts/predict.py --issue-time 2026-01-29T23:00:00

# Run focused tests
python -m pytest -q
```

Outputs are written to:

- `models/lightgbm/model.joblib` and `metadata.json`
- `reports/evaluation.csv`
- `predictions/m1_forecast.csv`

When M2 supplies the prepared table, run:

```powershell
python scripts/train.py --weather data/processed/weather_vintages.parquet --scada-timezone <verified-SCADA-timezone>
python scripts/evaluate.py --weather data/processed/weather_vintages.parquet
```

This writes a separate `models/lightgbm_weather` artifact and `reports/evaluation_weather.csv`, preserving the history-only fallback. A model trained with weather also requires `--weather` during prediction. See the strict schema-only [integration contract](M1_INTEGRATION.md) and [leakage audit](M1_AUDIT.md).

## Current evaluation

The checked artifact is a history-only fallback because no legal historical forecast-weather table is present. For this engineering validation, the configurable issue hour is set to 23:00 and the split reserves issue dates from 1 December 2025 onward; training targets end before that boundary. February 2026 is not used because its target observations are absent.

| Model | MAE | RMSE |
| --- | ---: | ---: |
| LightGBM | 0.32244 | 0.36471 |
| Climatology | 0.32930 | 0.36383 |
| Persistence | 0.35193 | 0.46541 |

These metrics measure normalized active power on 5,732 complete hourly targets. They are engineering metrics, not an invented competition score. Retrain and re-evaluate after M2 supplies legal weather forecasts.
