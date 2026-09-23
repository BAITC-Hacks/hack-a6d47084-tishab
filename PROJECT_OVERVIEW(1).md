# PROJECT OVERVIEW

## 1. Project

**Working title:** Agentic AI for Vintage-Aware Wind Power Forecasting

This project is a hackathon PoC for forecasting hourly wind power generation for two turbines over a **24–48 hour horizon** using weather forecasts that were actually available at the historical forecast issue time.

The system combines:

- Historical turbine/SCADA data
- Historical weather forecast vintages
- Machine-learning forecasting
- Physics/statistical baselines
- Uncertainty estimation
- Forecast validation
- LLM-based supervision/orchestration
- Automatic forecast revision
- Forecast provenance and versioning
- FastAPI backend
- React frontend

The numerical forecast is produced by deterministic/ML models. The LLM acts as a **Supervisor Agent**, not as the numerical predictor.

---

## 2. Hackathon Case

### Objective

Forecast hourly normalized active power for two wind turbines for the next **24–48 hours**.

### Turbines

- **T1:** 43.645150, 78.535604
- **T2:** 43.643198, 78.538828
- Location: Almaty Region, Kazakhstan, Shelek area
- Approximate elevation: 555 m
- Timezone: UTC+5
- Turbines are approximately 350 m apart

### Historical data

SCADA data is recorded at **10-minute intervals** and contains:

- turbine ID
- timestamp
- average wind speed
- normalized active power `[0, 1]`
- average ambient temperature

The historical dataset extends through **31 January 2026**.

### Closed test period

**February 2026** is the closed historical test period.

Historical replay follows the case protocol:

```text
31.01.2026 → forecast 01–02.02
01.02.2026 → forecast 02–03.02
...
27.02.2026 → forecast 28.02
```

At each historical issue time, the system must only use information that would have been available at that time.

---

## 3. Core Requirement: No Future Information Leakage

This is a hard system invariant.

For a historical issue time `T`:

> Only weather forecast information that was available by `T` may be used.

Future actual weather must never be used as a forecasting feature.

The weather pipeline must therefore select a legal historical forecast **vintage/run** and retain provenance.

Conceptually:

```text
Historical issue time
        ↓
Available weather runs
        ↓
Vintage / run selector
        ↓
Knowledge-boundary check
        ↓
Feature generation
        ↓
Forecast
```

The core validation rule is:

```python
forecast_available_time <= issue_time
```

If this condition cannot be established, the run must not be silently accepted. It should be rejected or explicitly marked as unresolved/TBD.

### Important

Do not invent:

- weather publication times
- forecast availability times
- missing historical weather
- future observations
- model results

When an availability semantic is uncertain, preserve the uncertainty explicitly.

---

## 4. Weather Strategy

The weather layer is responsible for obtaining historical forecast information and selecting a valid forecast vintage.

Potential weather variables include:

- wind speed at relevant heights
- wind gusts
- wind direction
- temperature
- pressure
- other variables available from the selected weather source

The exact weather source and vintage-selection semantics must be documented and verified.

### Weather provenance

Every weather run used by the forecasting pipeline should retain metadata such as:

```text
weather_run_id
forecast_run_time
forecast_available_time
weather_source
issue_time
```

The system should cache raw weather responses where practical so historical replay is reproducible.

---

## 5. Data Processing

### SCADA processing

Raw 10-minute SCADA data is aggregated to hourly resolution.

The pipeline should:

- preserve turbine identity
- detect duplicate timestamps
- detect missing intervals
- identify large gaps
- avoid blindly interpolating long gaps
- detect suspicious/stuck sensor values
- preserve timestamps consistently
- align SCADA and weather timestamps correctly

Large historical gaps should not be silently filled.

### Timezone

All timestamp handling must be explicit.

The system should use one canonical internal representation, preferably UTC, while preserving the original/local timestamp information when required for reporting.

Do not assume timezone alignment is correct without checking the actual data convention.

---

## 6. Forecasting Architecture

The forecasting engine has several layers.

```text
SCADA + Legal Weather Vintage
            ↓
      Feature Engineering
            ↓
 ┌──────────┼─────────────┐
 ↓          ↓             ↓
LightGBM    TFT      Power Curve
 ↓          ↓             ↓
 └──────────┼─────────────┘
            ↓
         Ensemble
            ↓
      P10 / P50 / P90
            ↓
        Validation
            ↓
    Publish / Recompute
```

---

## 7. Primary Models

### 7.1 LightGBM — P0

LightGBM is the primary ML forecasting model.

Potential features include:

- forecast wind speed at relevant heights
- wind direction encoded as sine/cosine
- wind gusts
- temperature
- pressure
- air-density-related features where justified
- hour/day/month/season
- forecast lead time
- turbine ID
- recent observed power/wind where legally available
- weather-model spread where available

The final feature set must be determined from the available data and validated empirically.

The model must support both turbines.

A clean model interface should expose operations conceptually equivalent to:

```python
train(...)
predict(...)
save(...)
load(...)
evaluate(...)
```

The exact implementation is left to the ML owner.

---

### 7.2 Power Curve — P0

Use an empirical/monotonic power curve as:

- physics/statistical baseline
- sanity check
- additional ensemble signal if validated

Possible implementation:

- isotonic regression
- monotonic spline
- another justified monotonic approach

The implementation should respect the observed turbine behavior rather than relying on invented turbine specifications.

---

### 7.3 Persistence — P0

Persistence is a mandatory baseline.

It should be evaluated against the ML and other forecasting approaches.

---

### 7.4 Climatology — P0

A simple historical climatology baseline should also be evaluated.

---

### 7.5 TFT — P1

A Temporal Fusion Transformer or similar sequence model may be added if the core system is already stable.

TFT must not block the P0 system.

If TFT is included, its contribution must be evaluated rather than assumed to improve the final forecast.

---

## 8. Ensemble

The system may combine:

- LightGBM
- TFT
- Power Curve
- other validated baselines/models

Do **not** hard-code arbitrary ensemble weights without validation.

Possible approach:

```text
Model predictions
        ↓
Validation period
        ↓
Learn/select weights
        ↓
Final ensemble
```

If time is limited, LightGBM can remain the primary prediction while other models provide baselines or additional signals.

---

## 9. Uncertainty

The system should produce:

```text
P10
P50
P90
```

as the initial uncertainty representation.

Initial uncertainty can use:

- model disagreement
- weather uncertainty/spread
- forecast validation information

More advanced calibration, such as conformal prediction, is optional P2 work.

Do not over-engineer uncertainty before the deterministic forecast pipeline works.

---

## 10. Forecast Validation

Every forecast should pass validation before publication.

Validation should consider:

- predicted power within `[0, 1]`
- physically implausible power/wind combinations
- high power under weak wind
- low power under strong wind
- model disagreement
- missing/invalid weather
- anomalous weather inputs
- abnormal plant-state patterns

Validation should produce explicit status/warnings rather than silently modifying predictions.

---

## 11. Plant-State / Anomaly Detection

The system may detect suspicious plant behavior.

Examples:

```text
High wind + near-zero power
→ possible outage/curtailment

Normal wind + abnormal power
→ possible plant anomaly

Stuck wind measurement
→ possible sensor issue
```

These should be described as **possible** conditions unless the data provides sufficient evidence to establish the cause.

Complex anomaly models such as Isolation Forest or Autoencoder are optional.

---

## 12. Agentic AI Architecture

The LLM is the **Supervisor Agent**.

It is responsible for:

- orchestrating tools/modules
- checking weather/data quality
- selecting or requesting appropriate processing
- interpreting validation results
- deciding whether recomputation is necessary
- deciding whether a forecast revision is material
- generating human-readable reports
- handling recoverable errors

The LLM is **not** responsible for directly generating numerical power forecasts.

### Conceptual workflow

```text
LLM Supervisor
      ↓
Weather Tool
      ↓
Data / Feature Tool
      ↓
Forecasting Engine
      ↓
Validation
      ↓
Revision Decision
      ↓
Save / Publish
      ↓
Report
```

---

## 13. LLM-Off Requirement

The numerical forecasting system must support an LLM-off mode.

Conceptually:

```bash
python forecast.py --llm off
```

The LLM-off path must produce the same numerical forecast for the same inputs and model version.

This ensures that the LLM is an orchestration layer rather than a hidden numerical predictor.

---

## 14. Compute ≠ Publish

A new weather forecast should trigger **recalculation**, but recalculation does not automatically require publication of a new forecast version.

Conceptually:

```text
New weather run
      ↓
Recalculate
      ↓
Compare with previous forecast
      ↓
Is change material?
   ↙          ↘
 YES          NO
 ↓             ↓
Publish      Keep current
revision
```

The exact materiality threshold should be configurable and validated rather than arbitrarily fixed.

Possible revision signals:

- change in predicted energy
- hourly power change
- uncertainty change
- model/weather disagreement

---

## 15. Forecast Versioning and Provenance

Every published forecast should retain lineage.

Example:

```text
F001
 ↓
weather update
 ↓
F002
 ↓
weather update
 ↓
F003
```

Suggested metadata:

```text
forecast_id
parent_forecast_id
issue_time
forecast_time
turbine_id
weather_run_id
model_version
feature_version
forecast_version
status
revision_reason
```

The system should be able to explain:

- what weather vintage was used
- which model version generated the forecast
- when it was issued
- whether it replaced an earlier forecast
- why a revision occurred

---

## 16. Forecast Output Schema

A forecast record should conceptually contain:

```json
{
  "forecast_id": "F002",
  "issue_time": "...",
  "forecast_time": "...",
  "turbine_id": "T1",
  "p10": 0.21,
  "p50": 0.34,
  "p90": 0.48,
  "weather_run_id": "...",
  "model_version": "lgbm-v1",
  "status": "validated"
}
```

The exact schema should be defined centrally and shared by:

- ML
- weather/data
- backend
- frontend

---

## 17. Backend

Use a lightweight **FastAPI** backend.

The backend should expose only the functionality required by the hackathon.

Potential endpoints:

```text
GET  /forecast
GET  /weather
GET  /agent/status
GET  /forecast/{id}/lineage
POST /forecast/run
POST /forecast/recompute
```

Do not build unnecessary production infrastructure.

Avoid unless required:

- microservices
- Redis
- Celery
- Kubernetes
- authentication
- complex distributed databases

Simple local persistence such as JSON, SQLite, or Parquet is acceptable for the PoC.

---

## 18. Frontend

Use **React** for the hackathon dashboard.

The dashboard should prioritize:

### Forecast

- T1/T2
- 24–48h forecast
- P10/P50/P90

### Weather

- wind
- temperature
- direction
- selected weather vintage/run
- issue time

### Model comparison

- LightGBM
- TFT if available
- Power Curve
- Ensemble

### Agent decision

- weather validation
- forecast validation
- recomputation decision
- publication/revision decision

### Provenance

- issue time
- weather vintage
- model version
- forecast version
- revision lineage

The frontend should visualize real system outputs and must not contain independent forecasting logic.

---

## 19. Team Ownership

### Member 1 — ML / Forecasting

Primary responsibility:

- LightGBM
- model training/inference
- forecasting features required by the model
- baseline evaluation
- model persistence
- prediction interface

### Member 2 — ML Engineering / Weather / Data

Primary responsibility:

- SCADA preprocessing
- weather retrieval
- weather caching
- historical vintage selection
- knowledge-boundary/leakage protection
- feature pipeline
- Power Curve
- TFT if time permits
- ensemble/uncertainty as appropriate

### Member 3 — Backend / Frontend / Agent Integration

Primary responsibility:

- FastAPI
- agent orchestration
- recomputation/revision logic
- provenance/versioning
- React dashboard
- integration of ML/weather modules
- final demo flow

---

## 20. Interface Boundaries

Team members should work through stable interfaces.

### Weather → ML

Conceptual fields:

```text
issue_time
forecast_time
turbine_id
weather_run_id
wind_10m
wind_80m
wind_100m
wind_120m
wind_direction
temperature
pressure
lead_time
```

### ML → Backend/Agent

Conceptual output:

```text
forecast_time
turbine_id
p10
p50
p90
model_name
model_version
```

### Backend → Frontend

The frontend consumes standardized forecast/agent/provenance objects.

The frontend should not know how LightGBM or weather retrieval works internally.

---

## 21. Priority Levels

### P0 — Must Work

- Historical SCADA loading
- Hourly aggregation
- Weather retrieval
- Legal weather-vintage selection
- Leakage/knowledge-boundary guard
- Feature pipeline
- LightGBM
- Power Curve
- Persistence
- Climatology
- 24–48h forecasting
- Forecast validation
- P10/P50/P90
- February replay
- LLM Supervisor
- Forecast provenance
- FastAPI
- React dashboard
- End-to-end execution

### P1 — Add If Core Is Stable

- TFT
- Weather bias correction
- Adaptive ensemble
- Plant-state detection
- Compute-vs-publish revision policy
- More sophisticated uncertainty

### P2 — Optional

- Multiple weather sources
- Conformal calibration
- Isolation Forest/Autoencoder
- Advanced explainability
- Production deployment infrastructure
- FastAPI/Docker expansion beyond what the PoC requires

---

## 22. Evaluation

The system should compare:

```text
Persistence
Climatology
Power Curve
LightGBM
TFT (if available)
Ensemble
```

Evaluation should be performed using the hackathon's historical replay protocol.

Do not change methodology simply to improve February results.

Report:

- forecast accuracy metrics
- per-turbine results
- horizon-dependent results where useful
- uncertainty coverage where available
- model comparison
- revision statistics
- leakage-test results
- failed/rejected forecast runs

The exact competition metric is TBD if not specified by the organizers. Do not invent a competition metric.

---

## 23. Reproducibility

The repository should support a clean workflow such as:

```bash
# install dependencies
pip install -r requirements.txt

# train
python scripts/train.py

# run a forecast
python scripts/forecast.py

# run backtest
python scripts/backtest.py

# replay February
python scripts/replay_february.py

# run backend
uvicorn src.api.main:app --reload

# run frontend
cd frontend/react-app
npm install
npm run dev
```

Exact commands may change with implementation.

The README must be updated to match the actual working commands.

---

## 24. Failure Handling

The system must fail explicitly rather than silently producing questionable results.

Examples:

```text
Weather unavailable
→ use documented fallback or stop

Weather vintage cannot be verified
→ reject/flag run

Feature missing
→ explicit validation error

Model unavailable
→ documented fallback

Forecast invalid
→ do not publish silently

LLM unavailable
→ numerical forecast should still be possible
```

The deterministic forecasting core should remain usable without the LLM.

---

## 25. Non-Goals for the Hackathon

Do not prioritize:

- multi-agent swarm architectures
- RAG
- chatbot functionality
- unnecessary microservices
- online model retraining
- complex cloud infrastructure
- fancy maps
- excessive UI decoration
- unnecessary deep-learning models
- architectural complexity without measurable benefit

The primary goal is a **working, reproducible, leakage-free end-to-end forecasting system**.

---

## 26. Definition of Done

The project is considered MVP-complete when:

1. Historical SCADA data can be processed.
2. A legal historical weather vintage can be selected.
3. The knowledge-boundary check prevents future-weather leakage.
4. Features can be generated consistently.
5. LightGBM can produce 24–48h forecasts.
6. Power Curve and baseline forecasts are available.
7. Uncertainty is produced.
8. Forecasts pass validation.
9. February 2026 replay can run end-to-end.
10. Forecast provenance is retained.
11. Forecast revisions can be represented.
12. LLM-off mode works.
13. FastAPI exposes the forecast system.
14. React displays the real forecast results.
15. A clean README allows another person to reproduce the workflow.

---

## 27. Core Engineering Principle

> **Build the simplest system that can prove the complete forecasting loop.**

The project should prioritize:

```text
Correctness
   >
Leakage Prevention
   >
Reproducibility
   >
End-to-End Functionality
   >
Agentic Behavior
   >
UI Polish
   >
Extra Complexity
```

The final system should demonstrate:

> **Forecast the future. Prove what information you used. Validate the result. Recompute when the evidence changes.**
