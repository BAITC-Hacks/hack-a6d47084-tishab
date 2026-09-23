import { useI18n } from "../i18n/LanguageProvider";
import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import AgentTimeline from "../components/AgentTimeline";
import ForecastChart from "../components/ForecastChart";
import ForecastReceipt from "../components/ForecastReceipt";
import KnowledgeBoundary from "../components/KnowledgeBoundary";
import MetricCard from "../components/MetricCard";
import ModelComparison from "../components/ModelComparison";
import ProvenancePanel from "../components/ProvenancePanel";
import RevisionTimeline from "../components/RevisionTimeline";
import StatusBadge from "../components/StatusBadge";
import WeatherPanel from "../components/WeatherPanel";
import { useForecast } from "../hooks/useForecast";


export function ForecastWorkspace({ forecast }) {
  const { t, date, number } = useI18n();
  const turbines = useMemo(() => Array.from(new Set(forecast.points.map((point) => point.turbine_id))), [forecast]);
  const [selected, setSelected] = useState(turbines.includes("PLANT") ? "PLANT" : turbines[0]);
  const points = forecast.points.filter((point) => point.turbine_id === selected);
  const latestPoint = points[0];
  const rejected = forecast.status === "rejected";

  return (
    <div className="forecast-workspace">
      {forecast.is_mock && <div className="demo-banner"><span>{t("MOCK MODE")}</span> {t("Synthetic data for integration and UI testing only.")}</div>}
      {rejected && <div className="integrity-banner"><strong>{t("Protection worked as designed")}</strong><span>{t("This demo run intentionally contains weather unavailable at issue time. Publication was blocked before future information could be used.")}</span></div>}
      <section className="page-heading compact-heading">
        <div><span className="eyebrow">{t("Current run")}</span><h1>{t("Wind power forecast")}</h1><p>{t("Vintage-aware output with uncertainty, provenance and decisions.")}</p></div>
        <StatusBadge status={forecast.status} />
      </section>
      <section className="metrics-grid">
        <MetricCard label={t("Issue time")} value={date(forecast.issue_time)} />
        <MetricCard label={t("Horizon")} value={t("{hours} hours", { hours: forecast.horizon_hours })} />
        <MetricCard label={t("First-hour P50")} value={number(latestPoint?.p50)} hint={t(selected)} />
        <MetricCard label={t("Integrity")} value={rejected ? t("BLOCKED") : t(forecast.integrity_status.toUpperCase())} />
        <MetricCard label={t("Agent")} value={t(forecast.agent.status.toUpperCase())} />
      </section>
      <section className={`panel chart-panel ${rejected ? "diagnostic-output" : ""}`}>
        <div className="section-title-row">
          <div><span className="eyebrow">{rejected ? t("Blocked diagnostic output") : t("Power outlook")}</span><h2>{t("{hours}-hour forecast", { hours: forecast.horizon_hours })}</h2></div>
          <div className="segmented-control">
            {turbines.map((turbine) => <button key={turbine} className={selected === turbine ? "active" : ""} onClick={() => setSelected(turbine)}>{t(turbine)}</button>)}
          </div>
        </div>
        <ForecastChart points={points} />
      </section>
      <section className="two-column">
        <KnowledgeBoundary boundary={forecast.knowledge_boundary} />
        <ForecastReceipt forecast={forecast} />
      </section>
      <section className="panel">
        <div className="section-title-row"><div><span className="eyebrow">{t("Signals")}</span><h2>{t("Model comparison")}</h2></div><span className="muted">{t("Dynamic provider output")}</span></div>
        <ModelComparison points={points} />
      </section>
      <section className="two-column">
        <div className="panel"><WeatherPanel weather={forecast.weather} /></div>
        <div className="panel"><AgentTimeline agent={forecast.agent} events={forecast.events} /></div>
      </section>
      <section className="two-column">
        <div className="panel"><RevisionTimeline lineage={forecast.lineage} revision={forecast.revision} /></div>
        <div className="panel"><ProvenancePanel provenance={forecast.provenance} /></div>
      </section>
    </div>
  );
}

export default function ForecastDetails() {
  const { t, errorText } = useI18n();
  const { id } = useParams();
  const { forecast, loading, error } = useForecast(id);
  if (loading) return <div className="state-page">{t("Loading forecast…")}</div>;
  if (error) return <div className="state-page error-state"><h2>{t("Forecast unavailable")}</h2><p>{errorText(error)}</p></div>;
  if (!forecast) return <div className="state-page">{t("No forecast available.")}</div>;
  return <ForecastWorkspace forecast={forecast} />;
}
