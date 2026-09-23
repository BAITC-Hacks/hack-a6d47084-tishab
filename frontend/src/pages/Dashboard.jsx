import { useState } from "react";
import { ForecastWorkspace } from "./ForecastDetails";
import { useForecast } from "../hooks/useForecast";

const SCENARIOS = [
  ["normal", "A · Normal"],
  ["baselines", "B · Baselines"],
  ["revision", "C · Revision V1→V2"],
  ["leakage", "D · Leakage rejected"],
  ["agent_off", "E · Agent unavailable"],
  ["optional_models", "F · Optional models"],
];

export default function Dashboard() {
  const { forecast, loading, error, run } = useForecast();
  const [scenario, setScenario] = useState("normal");
  const [horizon, setHorizon] = useState(48);
  const [issueTime, setIssueTime] = useState("2026-02-10T06:00");

  const submit = async (event) => {
    event.preventDefault();
    try {
      await run({ issue_time: new Date(issueTime).toISOString(), horizon_hours: Number(horizon), scenario });
    } catch {
      // The hook exposes the backend error as a visible page state.
    }
  };

  return (
    <>
      <section className="hero">
        <div><span className="eyebrow light">Vintage-aware operations</span><h1>Forecast the future.<br />Prove the evidence.</h1><p>One operational view for uncertainty, weather provenance, agent decisions and forecast lineage.</p></div>
        <form className="run-card" onSubmit={submit}>
          <div><span className="eyebrow">Run demo forecast</span><h2>Historical replay</h2></div>
          <label>Issue time<input type="datetime-local" value={issueTime} onChange={(event) => setIssueTime(event.target.value)} required /></label>
          <div className="form-row">
            <label>Horizon<select value={horizon} onChange={(event) => setHorizon(event.target.value)}><option value="24">24 hours</option><option value="48">48 hours</option></select></label>
            <label>Scenario<select value={scenario} onChange={(event) => setScenario(event.target.value)}>{SCENARIOS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
          </div>
          <button className="primary-button" type="submit" disabled={loading}>{loading ? "Running…" : "Run mock pipeline"}</button>
          <small>All generated values are marked as demo data.</small>
        </form>
      </section>
      {error && <div className="alert error"><strong>Backend unavailable</strong><span>{error}</span></div>}
      {!loading && !forecast && !error && <div className="state-page"><h2>No forecast available</h2><p>Run one of the mock scenarios to validate the integration flow.</p></div>}
      {forecast && <ForecastWorkspace forecast={forecast} />}
    </>
  );
}
