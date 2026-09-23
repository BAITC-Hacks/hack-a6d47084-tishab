import { useI18n } from "../i18n/LanguageProvider";
import { useState } from "react";
import { ForecastWorkspace } from "./ForecastDetails";
import { useForecast } from "../hooks/useForecast";
import WindFarmScene from "../components/WindFarmScene";

const SCENARIOS = [
  ["normal", "A · Normal"],
  ["baselines", "B · Baselines"],
  ["revision", "C · Revision V1→V2"],
  ["leakage", "D · Leakage rejected"],
  ["agent_off", "E · Agent unavailable"],
  ["optional_models", "F · Optional models"],
];

export default function Dashboard() {
  const { t, errorText } = useI18n();
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
        <div className="hero-copy">
          <span className="eyebrow light"><i className="live-dot" /> {t("Vintage-aware operations")}</span>
          <h1>{t("See the wind")}<br /><em>{t("before it arrives.")}</em></h1>
          <p>{t("One living view of generation, uncertainty, weather provenance and every decision behind the forecast.")}</p>
          <div className="hero-stats">
            <div><strong>{t("24–48h")}</strong><span>{t("Forecast horizon")}</span></div>
            <div><strong>T1 + T2</strong><span>{t("Live topology")}</span></div>
            <div><strong>{t("No leak")}</strong><span>{t("Vintage boundary")}</span></div>
          </div>
        </div>
        <WindFarmScene />
        <form className="run-card" onSubmit={submit}>
          <div className="run-card-head"><div><span className="eyebrow">{t("Forecast console")}</span><h2>{t("Historical replay")}</h2></div><span className="console-light" /></div>
          <label>{t("Issue time")}<input type="datetime-local" value={issueTime} onChange={(event) => setIssueTime(event.target.value)} required /></label>
          <div className="form-row">
            <label>{t("Horizon")}<select value={horizon} onChange={(event) => setHorizon(event.target.value)}><option value="24">{t("24 hours")}</option><option value="48">{t("48 hours")}</option></select></label>
            <label>{t("Scenario")}<select value={scenario} onChange={(event) => setScenario(event.target.value)}>{SCENARIOS.map(([value, label]) => <option key={value} value={value}>{t(label)}</option>)}</select></label>
          </div>
          <button className="primary-button" type="submit" disabled={loading}><span>{loading ? t("Running pipeline…") : t("Launch forecast")}</span><b>→</b></button>
          <small>{t("All generated values are marked as demo data.")}</small>
        </form>
      </section>
      {error && <div className="alert error"><strong>{t("Backend unavailable")}</strong><span>{errorText(error)}</span></div>}
      {!loading && !forecast && !error && <div className="state-page"><h2>{t("No forecast available")}</h2><p>{t("Run one of the mock scenarios to validate the integration flow.")}</p></div>}
      {forecast && <ForecastWorkspace forecast={forecast} />}
    </>
  );
}
