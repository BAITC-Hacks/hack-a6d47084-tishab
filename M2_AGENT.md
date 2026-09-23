# M2 / Agent: weather, data, agent

Unzip into the repository root. Only new files; nothing of backend/, frontend/ or ai/README.md is overwritten.
Check: `pip install -r requirements.txt && python3 -m pytest -q` → 79 passed.

## Agent outputs for the backend (`outputs/`, format: docs/CONTRACTS.md §5)

| File | Content |
|---|---|
| `outputs/forecasts.parquet` | All forecast versions: forecast_id, version, parent_forecast_id, issue_time, forecast_time, turbine_id, p50, model_version, weather_run_id, decision, revision_reason |
| `outputs/receipts/{forecast_id}.json` | Receipt: weather run, available_at + basis, model cutoff, leakage check, validation, decision, operator briefing |
| `outputs/agent_log.jsonl` | Agent steps: ts, issue_time, step, status, details |
| `outputs/latest.json` | Last run (for /agent/status) |
| `outputs/leakage_demo/` | Forecast rejected because weather came from the future |

February replay: 109 issues, 24 PUBLISH, 85 SHADOW, 0 REJECT (model: power curve).

## Regenerate outputs

```bash
python3 -m ai.agent.run --replay 2026-01-31T07:00Z 2026-02-27T07:00Z --offline --llm off
python3 -m ai.agent.run --issue 2026-02-14T07:00Z --force-run 2026-02-14T06:00Z --offline --llm off --out outputs/leakage_demo
```
`--llm on` needs `.env` with OPENAI_API_KEY and OPENAI_MODEL (key not included).

Details: docs/README_M2_AGENT_DRAFT.md.
