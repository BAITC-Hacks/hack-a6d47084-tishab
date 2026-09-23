# VANE — Final Hackathon MVP Specification

## Vintage-Aware Net-Energy Agent

> **Core pitch:** A wind-power forecasting agent that proves what it knew, when it knew it, and why it changed its forecast.

---

# 1. Executive Decision

Build **VANE** as the final MVP. Combine strict publication-aware forecast-vintage replay, uncertainty-aware LightGBM forecasting, visible agent behavior, automatic forecast revision, complete provenance, and offline reproducibility.

No hackathon result can be guaranteed. The goal is to maximize the solution's strength across task compliance, technical implementation, reproducibility, value, and originality.

---

# 2. Product

**Name:** VANE — Vintage-Aware Net-Energy Agent

**One-sentence value proposition:**

> VANE is an autonomous wind-power forecasting agent that only uses weather information legitimately available at forecast time, produces uncertainty-banded forecasts, automatically decides when updated weather warrants a forecast revision, and keeps a complete audit receipt for every prediction.

Do not pitch it as merely an “AI agent for wind forecasting.” Pitch it as:

> **“We built a forecasting agent that cannot see the future.”**

Every forecast has a **knowledge boundary** and a **forecast receipt**.

---

# 3. Core Strategy

The ML model is not the entire product. The product is:

> **Forecast + uncertainty + operational decision + proof.**

Four pillars:

1. Leakage-proof forecasting
2. Uncertainty-aware prediction
3. Visible autonomous behavior
4. Complete provenance and reproducibility

---

# 4. Final Architecture

```text
                         ┌───────────────────────┐
                         │      VANE AGENT       │
                         │ deterministic policy  │
                         │ + constrained LLM     │
                         └───────────┬───────────┘
                                     │
             ┌───────────────────────┼──────────────────────┐
             ▼                       ▼                      ▼
      Weather Layer            Plant State            Forecast State
             │                       │                      │
             ▼                       ▼                      ▼
      Vintage Selection       Turbine/Plant         Previous Forecast
      Weather Fetch           Conditions             Version
             └───────────────────────┼──────────────────────┘
                                     ▼
                           Feature Engineering
                                     │
                                     ▼
                         Shared LightGBM Model
                            + turbine_id
                            + horizon_hours
                                     │
                          ┌──────────┼──────────┐
                          ▼          ▼          ▼
                         P10        P50        P90
                          └──────────┼──────────┘
                                     ▼
                         Forecast Validation
                                     │
                ┌────────────────────┼────────────────────┐
                ▼                    ▼                    ▼
          Physics Guard        Weather Spread       Plant State
                                  Analysis            Detection
                └────────────────────┼────────────────────┘
                                     ▼
                         Revision Decision
                       ┌─────────────┼─────────────┐
                       ▼             ▼             ▼
                    ACCEPT        SHADOW       PUBLISH V2
                                     │
                                     ▼
                         Provenance / Audit Store
                                     │
                                     ▼
                            Streamlit Dashboard
```

---

# 5. Non-Negotiable Principle: Deterministic Correctness

Deterministic code owns:

- weather-vintage selection
- API parsing
- timestamp handling
- leakage checks
- feature construction
- forecasting numbers
- validation
- metrics
- revision thresholds
- provenance

The LLM may:

- summarize structured facts
- explain why a forecast changed
- explain validation failures
- triage constrained exceptions
- write operator-facing briefings

The LLM must **never** generate numeric forecast values or decide whether future information is legal.

The system must support:

```bash
python -m vane replay --llm off
```

and produce identical numerical forecasts and metrics.

---

# 6. Weather Strategy

## Primary

**ECMWF IFS via Open-Meteo Single Runs API.**

Use Single Runs for exact historical forecast-vintage reconstruction.

Critical distinction:

```text
run initialization time
        !=
forecast availability time
```

Never select a run merely because its initialization time is before the issue time.

## Secondary

GFS/ICON only after verifying that the required archived runs and variables are actually available for the relevant period.

The project must remain fully functional with ECMWF alone.

## Previous Runs API

Use Previous Runs for cross-checks, supplementary training, or validation of the vintage logic. Do not blindly treat `_previous_day1` as equivalent to “what was available exactly 24 hours before issue time”; initialization and publication delay must be respected.

---

# 7. Publication-Aware Vintage Selection

This is the most important deterministic component.

```python
def select_legal_run(model, issue_time):
    runs = get_archived_runs(model)

    legal = [
        r for r in runs
        if r.available_at <= issue_time
    ]

    return max(legal, key=lambda r: r.init_time)
```

Every run must carry:

```text
model
init_time
available_at
issue_time
```

Mandatory assertion:

```python
assert selected_run.available_at <= issue_time
```

---

# 8. Knowledge-Boundary Guard

Every feature should carry availability provenance.

Example:

```text
feature                  available_at
--------------------------------------
wind_100m_forecast       05:xx
temperature_forecast    05:xx
latest_power_observed    05:50
```

For issue time `06:00 UTC`:

```python
assert max(feature.available_at) <= issue_time
```

If violated:

```text
LeakageError
```

The system refuses to produce the forecast.

---

# 9. Signature Demo: Prove Leakage Protection

Set:

```text
AS OF = 06:00 UTC
```

Attempt to use a weather run available at 12:00.

Display:

```text
FORECAST REJECTED

Reason:
weather vintage available_at = 12:00
issue_time = 06:00

Future information detected.

Leakage prevented.
```

This converts an invisible engineering property into a memorable product feature.

---

# 10. Offline-First Weather Cache

Cache every weather response.

Suggested structure:

```text
data/
└── cache/
    └── raw/
        ├── ecmwf/
        ├── gfs/
        └── icon/
```

Cache keys must include:

- API
- model
- run initialization
- latitude
- longitude
- variables

Also store retrieval metadata and hashes.

The February replay must run from cache without requiring live network access.

---

# 11. Data Pipeline

```text
10-minute observations
        ↓
timezone normalization
        ↓
quality checks
        ↓
hourly aggregation
        ↓
feature table
```

Keep:

- T1 power
- T2 power
- plant mean power
- turbine_id

Use a shared model rather than two separate deep models.

---

# 12. Timezone Handling

Do not assume the timestamp convention.

Create one explicit timezone conversion function and convert everything to UTC after ingestion.

Run a short forensic check:

- compare measured wind with NWP analysis wind
- test lags from -3h to +3h
- inspect the best correlation
- check whether the relationship changes around the Kazakhstan time-zone transition

Document the detected convention.

---

# 13. Forecasting Stack

## Baseline 1 — Persistence

```text
P(t+h) = P(t)
```

## Baseline 2 — Empirical Power Curve

Fit a clean-hours relationship:

```text
wind speed → normalized power
```

Apply the forecast wind to the curve.

## Main Model — LightGBM

Use one shared LightGBM model with:

- `turbine_id`
- `horizon_hours`

as features.

Do not build LSTM/Transformer/TFT models within the MVP.

---

# 14. Quantile Forecasting

Produce:

```text
P10
P50
P90
```

Display the P50 forecast with a P10–P90 uncertainty band.

If time permits, add conformal calibration. P10/P50/P90 is core; CQR is optional.

---

# 15. Features

## NWP

- wind speed at available levels around hub height
- wind speed at 10m
- wind direction
- wind direction sin/cos
- gust
- temperature
- pressure

## Known at issue time

- latest observed power
- recent power lag(s)
- recent rolling mean
- turbine_id

## Context

- hour of day
- month
- horizon_hours
- weather-model spread, if a second model is available

All future weather features must come from the legal forecast vintage.

---

# 16. Strict Feature Rule

For issue time `T`, legal observations satisfy:

```text
timestamp < T
```

Never use:

- future actual power
- future measured wind
- future measured temperature
- future weather observations disguised as forecasts

No interpolation or backfill operation may pull future values into the feature window.

---

# 17. Forecast Validation

Minimum deterministic checks:

```text
0 <= power <= capacity
P10 <= P50 <= P90
no NaN
complete forecast horizon
```

Also compare P50 against the empirical power curve for sanity.

Do not invent unsupported cut-out or icing thresholds.

---

# 18. Weather Disagreement

If a second weather model is available:

```text
ECMWF wind
      +
GFS/ICON wind
      ↓
power-curve transformation
      ↓
power-space disagreement
```

Use disagreement to:

- flag low confidence
- widen uncertainty
- trigger review/revision

Power-space disagreement is preferred because the same wind disagreement can have very different power consequences at different parts of the turbine curve.

---

# 19. Agentic Loop

```text
NEW ISSUE TIME
      ↓
check weather freshness
      ↓
select legal vintage
      ↓
fetch weather
      ↓
validate weather
      ↓
build features
      ↓
forecast P10/P50/P90
      ↓
validate forecast
      ↓
analyze weather disagreement
      ↓
compare with previous forecast
      ↓
DECISION
      │
      ├── ACCEPT
      ├── SHADOW
      └── PUBLISH REVISION
      ↓
store provenance
      ↓
generate operator briefing
```

The agent genuinely:

- perceives new information
- decides under policy
- acts through tools
- validates itself
- revises forecasts
- maintains forecast memory

---

# 20. Compute ≠ Publish

When a new weather run arrives:

1. Always recompute internally.
2. Compare against the published forecast.
3. Publish a revision only when the change is material.

Example:

```text
Forecast v1
Expected energy = 42.1

New weather run
Expected energy = 42.7

Change = 1.4%

→ SHADOW
```

Large change:

```text
Forecast v1
Expected energy = 42.1

New weather run
Expected energy = 48.9

Change = 16.2%

→ PUBLISH V2
```

Thresholds must be calibrated using historical replay and documented.

---

# 21. Forecast Versioning

Store at least:

```text
forecast_id
version
issue_time
valid_time
lead_hours
q10
q50
q90
weather_run
available_at
model_version
feature_hash
supersedes
decision
reason
```

Revision chain:

```text
v1
 ↓
new weather
 ↓
v2
```

Dashboard should visibly show the lineage.

---

# 22. Revision Gain

Measure whether revisions actually help.

For the same target hours compare:

```text
first-issued forecast MAE
vs
latest valid revision MAE
```

Report revision gain as an empirical improvement measure.

This proves that recalculation is useful rather than merely decorative.

---

# 23. Plant-State Detection

Add a lightweight detector for:

- turbine divergence
- possible outage
- possible curtailment

Example:

```text
T1 = 0.72
T2 = 0.03
similar wind conditions
```

Flag:

> Possible turbine-specific operational constraint.

Do not claim certainty unless the evidence supports it.

Icing is optional and not core because the supplied data does not directly establish all variables needed for a strong icing diagnosis.

---

# 24. LLM Role

The LLM receives structured facts, for example:

```json
{
  "issue_time": "...",
  "weather_run": "...",
  "weather_available_at": "...",
  "p50_change": 0.16,
  "weather_disagreement": "high",
  "validation": "pass",
  "decision": "publish_revision"
}
```

It returns a grounded operator explanation.

The LLM must not invent numbers. Prefer schema validation and template fallback.

---

# 25. LLM Failure Safety

If the LLM is unavailable or invalid:

```text
deterministic policy
+
template briefing
```

The forecast continues.

Required command:

```bash
python -m vane replay --llm off
```

---

# 26. Forecast Receipt

Every forecast should have a visible receipt.

```text
FORECAST RECEIPT
─────────────────────────────
Issue time:
2026-02-14 06:00 UTC

Weather:
ECMWF IFS

Run initialized:
2026-02-14 00:00 UTC

Available at:
[verified timestamp]

Lead:
24–48h

Observed data cutoff:
< issue time

Future observations used:
NO

Integrity:
✓ PASS
```

Use actual verified timestamps in the final system; never hardcode illustrative values.

---

# 27. Dashboard

Keep it minimal.

## Main page

### Forecast

- 48h P10/P50/P90
- current issue time
- previous-version ghost line

### Forecast Receipt

- issue time
- weather source
- run
- available_at
- lead time
- integrity

### Agent Activity

```text
✓ freshness checked
✓ legal vintage selected
✓ weather fetched
✓ features validated
✓ forecast generated
⚠ disagreement detected
→ revision published
✓ provenance stored
```

### Weather

- NWP wind
- disagreement
- freshness

### Health

- stale input
- validation status
- turbine alerts
- confidence

---

# 28. Backtest Tab

Show:

```text
                    24h       48h

Persistence          X         X
Power Curve          X         X
VANE                 X         X
```

Metrics:

- MAE
- RMSE
- pinball loss
- P10–P90 coverage
- revision gain

Report both all-hours and clean-hours metrics where relevant.

Never fabricate results.

---

# 29. February 2026 Replay

February 2026 is the closed test period.

Internal quantitative validation should come from a blind historical replay before February 2026, preferably January 2026 or a comparable pre-test period.

Then:

```text
Refit through January 31
        ↓
February 2026 vintage replay
        ↓
forecast outputs
        ↓
organizer evaluation
```

Label February explicitly:

> **Closed organizer-evaluated replay — no internal ground-truth score claimed.**

Do not use February observations for model selection, tuning, or calibration.

---

# 30. Backtest Rules

The replay must be:

- chronological
- vintage-strict
- cached
- deterministic
- reproducible

Never use:

- random K-fold CV for the temporal evaluation
- future observations
- future weather
- ERA5/reanalysis as future forecast features
- Historical Forecast API as the future forecast vintage
- interpolation/backfill that introduces future values
- post-test tuning

---

# 31. Key Failure Modes

## Vintage leakage

Highest priority. Prevent with automated availability assertions.

## Timezone mismatch

Prevent with explicit UTC normalization and forensic testing.

## Wrong hourly aggregation

Document the aggregation convention precisely.

## Future observed features

Enforce feature availability.

## Cache contamination

Include run initialization in cache keys.

## LLM failure

Keep LLM out of the numerical hot path.

## API failure

Cache-first architecture.

## Overengineering

Freeze P0 before adding P1/P2.

---

# 32. Five-Hour Execution Plan

## 0:00–0:20 — API and data verification

- verify case data
- verify coordinates
- verify timezone convention
- verify ECMWF Single Runs
- verify required variables
- begin caching

**Exit:** one real historical vintage successfully fetched and mapped.

## 0:20–0:45 — Data audit

- 10-minute → hourly
- missingness
- turbine divergence
- timezone forensics
- empirical power curve

**Exit:** clean hourly dataset.

## 0:45–1:30 — Forecast core

Build:

- legal vintage selection
- leakage guard
- feature builder
- persistence
- power curve
- LightGBM q50

**Exit:** blind historical replay produces metrics.

## 1:30–2:15 — Quantiles + February replay

Add:

- P10
- P50
- P90
- February replay
- provenance

**Exit:** submission forecast files exist.

## 2:15–3:00 — Agent

Implement:

- freshness
- legal vintage
- forecast
- validation
- revision policy
- versioning
- JSONL audit log

**Exit:** agent can replay multiple issue times autonomously.

## 3:00–3:45 — Dashboard

Build:

- forecast chart
- receipt
- activity log
- backtest
- health

**Exit:** complete demo path works.

## 3:45–4:15 — Winning features

Priority:

1. compute vs publish
2. revision gain
3. weather disagreement
4. physics validation

CQR only if ahead.

## 4:15–4:30 — LLM

Add:

- grounded briefing
- constrained exception handling
- `--llm off`

## 4:30–5:00 — Freeze

Do not add features.

Run:

```bash
make replay
pytest
```

Verify:

- leakage tests pass
- forecasts reproduce
- cache works offline
- README works
- demo rehearsed twice

---

# 33. Drop Order If Time Runs Out

Drop first:

1. fancy UI
2. CQR
3. third weather source
4. icing
5. advanced plant-state detection
6. complex LLM behavior

Never drop:

- legal vintage selection
- leakage guard
- main model
- uncertainty
- provenance
- February replay
- reproducibility

---

# 34. Final Demo Script

## 0:00–0:20 — Problem

Show:

```text
AS OF:
2026-02-14 06:00 UTC

KNOWLEDGE BOUNDARY:
06:00 UTC
```

Say:

> “Our agent cannot see the future. Every forecast is generated only from information that was actually available at that moment.”

## 0:20–0:50 — Generate Forecast

Show:

```text
✓ checked freshness
✓ selected legal weather vintage
✓ fetched weather
✓ generated P10/P50/P90
✓ validated
✓ published v1
```

## 0:50–1:10 — Prove Leakage Protection

Attempt to use a future run.

Show:

```text
REJECTED

available_at > issue_time

Future information detected.
```

## 1:10–1:35 — Forecast Revision

Show:

```text
v1
↓
new weather
↓
recompute
↓
Δ exceeds threshold
↓
publish v2
```

## 1:35–1:55 — Explain Why

Open the forecast receipt and grounded LLM explanation.

## 1:55–2:15 — Backtest

Show actual:

- Persistence
- Power Curve
- VANE
- 24h/48h metrics
- interval coverage
- revision gain

## 2:15–2:30 — Closing

> **“Every forecast has a receipt: what was known, what was used, what changed, and why the agent acted.”**

---

# 35. README Structure

```text
# VANE

## Problem
## Why Forecast Vintage Matters
## Architecture
## Knowledge Boundary
## Weather Data
## Forecasting Model
## Uncertainty
## Agent Loop
## Revision Policy
## Leakage Prevention
## Backtesting Protocol
## Results
## Reproducibility
## Demo
## Limitations
## Future Work
```

Include:

- architecture diagram
- leakage invariant
- sample forecast receipt
- actual metrics
- reproduction command
- known limitations

---

# 36. Reproducibility Commands

Target interface:

```bash
pip install -r requirements.txt
pytest
python -m vane replay --month 2026-02
streamlit run app.py
python -m vane replay --llm off
```

A judge should be able to reproduce the core system without manually inspecting the implementation.

---

# 37. Final Scope Freeze

## P0 — Submission Backbone

1. hourly data pipeline
2. UTC normalization
3. ECMWF IFS Single Runs
4. publication-aware `select_run()`
5. `available_at` leakage guard
6. LightGBM
7. P10/P50/P90
8. persistence baseline
9. power-curve baseline
10. blind historical backtest
11. February replay
12. provenance
13. offline cache

## P1 — Winning Layer

14. agent activity log
15. compute-vs-publish
16. forecast revisions
17. revision gain
18. weather disagreement
19. physics validation
20. Streamlit dashboard
21. grounded LLM briefing

## P2 — Bonus

22. CQR
23. GFS/ICON
24. curtailment detector
25. turbine-down detector
26. reliability diagram
27. additional UI polish

---

# 38. Final Architecture in One Diagram

```text
                    ┌──────────────────────┐
                    │     VANE AGENT       │
                    │ deterministic policy │
                    │ + constrained LLM    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ KNOWLEDGE BOUNDARY   │
                    │ available_at <= T    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ ECMWF IFS VINTAGE   │
                    │ Single Runs          │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ FEATURE ENGINEERING  │
                    │ + turbine_id         │
                    │ + horizon_hours      │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ LIGHTGBM QUANTILES   │
                    │ P10 / P50 / P90      │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
        Physics Guard     Weather Spread   Plant State
              └────────────────┼────────────────┘
                               ▼
                    ┌──────────────────────┐
                    │ REVISION POLICY      │
                    │ ACCEPT / SHADOW /    │
                    │ PUBLISH V2           │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ PROVENANCE STORE     │
                    │ + VERSION HISTORY    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ STREAMLIT DASHBOARD  │
                    │ Forecast / Receipt   │
                    │ Agent / Backtest     │
                    │ Health               │
                    └──────────────────────┘
```

---

# 39. Final Recommendation

**BUILD THIS.**

Do not continue architectural brainstorming unless implementation proves a load-bearing assumption impossible.

The core product is:

> **VANE — a vintage-aware, uncertainty-aware, provenance-first autonomous wind forecasting agent.**

The most important technical feature is:

> **Publication-aware historical forecast replay with an enforced knowledge boundary.**

The most important agent feature is:

> **Compute every update, but publish a revision only when the change is material.**

The most important trust feature is:

> **Every forecast has a receipt.**

The most important demo feature is:

> **Attempt to use future weather → VANE rejects it.**

The most important evaluation feature is:

> **Show actual blind backtest results and revision gain, never fabricated February scores.**

The most important engineering rule is:

> **If the core forecast + leakage guard + provenance + replay are not working, stop adding features.**

---

# 40. Final Tagline

> ## VANE
> ### *Forecast the future. Prove you didn't see it.*
