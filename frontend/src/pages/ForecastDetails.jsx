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

const formatDate = (value) => value ? new Date(value).toLocaleString() : "N/A";

export function ForecastWorkspace({ forecast }) {
  const turbines = useMemo(() => Array.from(new Set(forecast.points.map((point) => point.turbine_id))), [forecast]);
  const [selected, setSelected] = useState(turbines.includes("PLANT") ? "PLANT" : turbines[0]);
  const points = forecast.points.filter((point) => point.turbine_id === selected);
  const latestPoint = points[0];

  return (
    <div className="forecast-workspace">
      {forecast.is_mock && <div className="demo-banner"><span>MOCK MODE</span> Synthetic data for integration and UI testing only.</div>}
      <section className="page-heading compact-heading">
        <div><span className="eyebrow">Current run</span><h1>Forecast {forecast.forecast_id}</h1><p>Vintage-aware output with uncertainty, provenance and decisions.</p></div>
        <StatusBadge status={forecast.status} />
      </section>
      <section className="metrics-grid">
        <MetricCard label="Issue time" value={formatDate(forecast.issue_time)} />
        <MetricCard label="Horizon" value={`${forecast.horizon_hours} hours`} />
        <MetricCard label="First-hour P50" value={latestPoint?.p50 ?? "N/A"} hint={selected} />
        <MetricCard label="Integrity" value={forecast.integrity_status.toUpperCase()} />
        <MetricCard label="Agent" value={forecast.agent.status.toUpperCase()} />
      </section>
      <section className="panel chart-panel">
        <div className="section-title-row">
          <div><span className="eyebrow">Power outlook</span><h2>{forecast.horizon_hours}-hour forecast</h2></div>
          <div className="segmented-control">
            {turbines.map((turbine) => <button key={turbine} className={selected === turbine ? "active" : ""} onClick={() => setSelected(turbine)}>{turbine}</button>)}
          </div>
        </div>
        <ForecastChart points={points} />
      </section>
      <section className="two-column">
        <KnowledgeBoundary boundary={forecast.knowledge_boundary} />
        <ForecastReceipt forecast={forecast} />
      </section>
      <section className="panel">
        <div className="section-title-row"><div><span className="eyebrow">Signals</span><h2>Model comparison</h2></div><span className="muted">Dynamic provider output</span></div>
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
  const { id } = useParams();
  const { forecast, loading, error } = useForecast(id);
  if (loading) return <div className="state-page">Loading forecast…</div>;
  if (error) return <div className="state-page error-state"><h2>Forecast unavailable</h2><p>{error}</p></div>;
  if (!forecast) return <div className="state-page">No forecast available.</div>;
  return <ForecastWorkspace forecast={forecast} />;
}
