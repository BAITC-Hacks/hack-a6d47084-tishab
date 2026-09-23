# M1 + M2 → M3 Handoff

Commit:
`b24991ca8e0f8f41a11e8d7e8ba04c99bd45617f`

Branch:
`origin/feature/shihab`

## Run

```bash
python3 scripts/predict.py \
  --weather data/processed/weather_vintages.parquet \
  --issue-time 2026-02-10T07:00:00Z \
  --output predictions/forecast.csv
```
