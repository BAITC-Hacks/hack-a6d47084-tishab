# Project overview: vintage-aware wind power forecasting

## Objective and current state

Build a hackathon MVP that forecasts **hourly normalized active power for two wind turbines over a 24–48 hour horizon**. It must replay historical forecast issues for the closed **February 2026** test period using only information available at each issue time. The deliverable is a working, explainable end-to-end flow with a FastAPI backend and React dashboard; production infrastructure is outside the MVP.

This document is the system-level technical specification. The M1 workstream is now implemented: SCADA aggregation, model-side feature construction, shared LightGBM, persistence/climatology baselines, evaluation, saved artifacts, and prediction commands. The repository still has no weather archive, February observations, FastAPI/React application, or M2/M3 implementation.

## Case constraints and source data

| Requirement or evidence | Specification |
| --- | --- |
| Historical knowledge boundary | For issue time `T`, a weather forecast is eligible only when its **verified availability time is at or before `T`**. A model run timestamp alone does not prove availability. If availability cannot be established, reject or flag the run; never silently accept it. |
| Future observations | Future actual weather and SCADA after `T` must never enter forecast features, fitted transforms, or model selection for that replay issue. |
| Numerical predictions | Forecasting code produces all numeric power values. The LLM may orchestrate and explain, but must not invent or modify predictions. An LLM-off path must yield identical numeric forecasts for the same issue, inputs, vintage, model, and configuration. |
| Replay | February 2026 is the closed historical test period. Exact issue schedule, scoring metric, and availability of February targets are TBD. Do not tune on the closed test period. |
| Provenance | Retain the selected weather vintage and its availability evidence, input/data version, feature version, model version, issue time, and forecast lineage for every computed forecast. |

The two supplied CSVs are separate turbine files, so turbine identity comes from the filename rather than a column. Both have columns `ID`, naive `Статистическое время` (timestamp), mean wind speed (m/s), normalized active power, and mean ambient temperature (°C). The timestamps run from **2023-03-11 00:00** through **2026-01-31 23:50**. Turbine 1 has **142,360** records and **9,992** absent 10-minute slots; turbine 2 has **149,499** records and **2,853** absent slots within that range. No duplicate timestamps, empty cells, or out-of-range power values were found in a basic scan. There are large gaps, so hourly aggregation must record coverage and must not silently fill long gaps. The timestamp timezone is **TBD** and must be verified before weather alignment.

The existing draft mentions turbine coordinates, a UTC+5 timezone, and a specific daily replay sequence, but no case document or data metadata in this repository verifies those details. Treat them as **TBD**, not implementation constants.

## Architecture and data flow

```text
Issue time T
  -> retrieve/cache historical weather forecast runs
  -> select a vintage with proven availability <= T
  -> align with historical SCADA available by T
  -> clean/aggregate SCADA and build leakage-safe hourly features
  -> deterministic baselines + LightGBM [optional TFT]
  -> ensemble and P10/P50/P90 estimates
  -> validate candidate forecast
  -> compare with current published version
  -> publish a revision only when the deterministic policy calls for it
  -> serve forecast, provenance, decisions, and report via FastAPI/React
```

Keep computation and publication separate. A new eligible weather run or corrected input may trigger a **new candidate computation**. A version is **published** only after validation and a documented material-change policy (thresholds TBD). Preserve candidates, rejected runs, and the reason for each publication decision so the LLM Supervisor and LLM-off workflow can explain the same outcome.

## Module responsibilities and interfaces

| Module | Responsibility and required boundary |
| --- | --- |
| Weather retrieval and vintage selector | Obtain historical forecast runs for both turbine locations; cache raw responses and source metadata; establish `forecast_available_time`; select only legal vintages covering each target hour. Weather provider, variables, run cadence, and availability evidence are TBD. |
| Knowledge-boundary guard | Enforce `available_time <= issue_time` for weather and `observation_time <= issue_time` for observed inputs. Reject unknown or illegal provenance before feature generation. Apply the same rule during training and replay. |
| SCADA and features | Load each turbine CSV, parse timestamps once the timezone is verified, check duplicates/gaps/invalid values, aggregate to hourly targets with coverage flags, align weather by valid time, and create reproducible features. Fitted preprocessing uses only the allowed training history. |
| Forecasting | Train/load LightGBM and baseline models; emit per-turbine hourly predictions through a common interface. Record model and feature versions. All numeric outputs are deterministic for fixed artifacts and inputs. |
| Ensemble and uncertainty | Compare model outputs on validation data, choose any ensemble weights from evidence, and generate ordered P10/P50/P90 within `[0,1]`. An unvalidated ensemble must not be assumed better than LightGBM. Calibration method is TBD. |
| Validator and revision policy | Check input provenance, target-hour coverage, numeric bounds, quantile order, missing inputs, and suspicious power/weather combinations. Return explicit errors/warnings; compare valid candidates with the current publication using a configurable materiality rule. |
| Forecast store | Persist candidate and published runs, hourly rows, weather/model/feature lineage, validation results, parent version, and recomputation/publication decisions. For the MVP, a simple local store is sufficient; format is TBD. |
| LLM Supervisor | Call the above tools, interpret validation, request justified recomputation, and produce human-readable status/reports. It cannot supply numerical forecasts, bypass the guard, or change the deterministic publication policy. LLM failure must leave the numeric pipeline usable. |

Weather-to-model data must carry at least turbine ID, issue time, target time, weather run ID, forecast availability time, source, and the selected weather values. Model-to-backend output must carry turbine ID, target time, point/quantile predictions, and model version. Define these interfaces centrally when implementation begins.

## Forecast record schema

Use one logical **run** for a computation and one **hourly row** per turbine and target hour. Exact storage format and API serialization are TBD.

| Scope | Required fields |
| --- | --- |
| Run/version | `forecast_id`, `parent_forecast_id` (nullable), `issue_time`, `created_at`, `state` (`candidate`, `published`, or `rejected`), `revision_reason`, validation status/warnings, recomputation/publication decision. |
| Provenance | `weather_source`, `weather_run_id`, `forecast_run_time`, **`forecast_available_time` and evidence**, input data reference/version, `feature_version`, `model_name`, `model_version`, configuration/version reference. Use per-hour weather provenance if a run combines vintages. |
| Hourly row | `forecast_id`, `turbine_id`, `target_time`, `lead_hours`, `p10`, `p50`, `p90` for normalized active power; optional model-specific predictions for comparison. Enforce `0 <= p10 <= p50 <= p90 <= 1`. |

Times need an explicit timezone/UTC convention after the CSV timezone is established. Forecast IDs and versions must make a published revision traceable to its predecessor and to the candidate that produced it.

## Model hierarchy and evaluation

1. **Persistence and climatology (P0):** simple reference forecasts, evaluated using the same legal issue-time information and target hours as the other models.
2. **Power Curve (P0):** empirical wind-speed-to-power baseline fitted from historical training data; do not assume undocumented turbine specifications.
3. **LightGBM (P0):** primary ML model using eligible weather forecast variables, lead time, time features, turbine identity, and only observed lags available by the issue time. Exact feature set and training split are TBD.
4. **Ensemble and uncertainty (P0 minimal):** retain LightGBM as the primary forecast unless validation supports a combination; provide P10/P50/P90 with a documented, tested method.
5. **TFT (P2):** optional secondary model only after the end-to-end path works; include it in the ensemble only if replay validation demonstrates value.

Evaluate by turbine and lead time against the case metric once confirmed, with all models using the same historical issue schedule and allowed information. Keep training, validation, and the February 2026 closed replay separated in time. February observations needed for scoring are not in the supplied CSVs; their source is TBD.

## FastAPI, React, and agent behavior

FastAPI owns forecast/replay invocation, read APIs for current and prior forecasts, validation/agent status, weather provenance, and revision lineage. React displays the two turbine hourly forecasts and uncertainty bands, weather vintage and issue time, model/baseline comparison, validation warnings, and candidate-versus-published decisions. Exact routes and UI layout are TBD. React consumes backend records and contains no forecasting logic.

The LLM Supervisor can summarize why a run was rejected or revised and can request another deterministic computation when inputs change. The deterministic pipeline decides eligibility, numerical output, validation gates, and publication under the configured policy. Run the same scenario with the LLM disabled to verify numeric parity.

## Delivery priorities

| Priority | Scope |
| --- | --- |
| **P0: end-to-end MVP** | CSV loading/hourly aggregation; legal historical weather retrieval and vintage selection; leakage guard; persistence, climatology, Power Curve, and LightGBM; minimal uncertainty; forecast validation; candidate/published separation and lineage; February replay; LLM Supervisor with LLM-off numeric parity; FastAPI and React showing real outputs. |
| **P1: improve after P0 works** | Weather bias correction, validated adaptive ensemble and uncertainty calibration, richer plant-state warnings, clearer revision thresholds/reporting, stronger per-horizon diagnostics. |
| **P2: optional** | TFT, multiple weather sources, advanced anomaly detection or explainability, and production deployment infrastructure. |

## Technical risks and open decisions

- **Weather-vintage availability:** no weather source/archive or publication-time evidence is present. This is the principal blocker to a valid historical replay. Provider, access method, historical coverage, variables, and run-availability semantics are TBD.
- **Timezone alignment:** SCADA timestamps have no offset. Their timezone and the canonical timezone for weather/API/output are TBD.
- **Missing SCADA intervals:** especially the large turbine 1 gap; define hourly coverage rules and treatment of incomplete targets before training.
- **Closed-test scoring:** exact issue schedule, February ground truth, metric, and organizer evaluation protocol are TBD.
- **Model validity:** training/validation split, available weather variables, baseline definitions, uncertainty calibration, and materiality threshold require evidence; no measured accuracy exists yet.
- **Operational choices:** turbine coordinates/specifications, weather and LLM providers, storage format, API routes, and deployment target are TBD. The earlier draft lists some location/timezone values, but they need source confirmation.

## Proposed team ownership boundaries

The existing draft proposes three workstreams; actual people/assignments are **TBD**.

| Workstream | Owns | Handoff |
| --- | --- | --- |
| ML / forecasting | LightGBM, persistence/climatology, model training/evaluation, saved artifacts, prediction interface | Receives legal hourly feature table; returns versioned numeric predictions. |
| Weather / data / ML engineering | SCADA quality and aggregation, weather retrieval/cache, historical-vintage proof, leakage guard, feature pipeline, Power Curve; optional TFT/ensemble support | Supplies eligibility-checked features and provenance to ML/backend. |
| Backend / frontend / agent integration | FastAPI, forecast store/versioning, validation and revision orchestration, LLM Supervisor and LLM-off path, React, end-to-end replay/demo | Consumes stable weather/ML interfaces; exposes actual outputs and decision history. |

Agree on timestamp semantics, shared record schema, and failure behavior before parallel implementation. Favor the simplest local architecture that can demonstrate a legal, reproducible forecast loop.
