import StatusBadge from "./StatusBadge";

const show = (value) => value ?? "N/A";
const date = (value) => (value ? new Date(value).toLocaleString() : "N/A");

export default function ForecastReceipt({ forecast }) {
  const p = forecast.provenance;
  return (
    <article className="receipt-card">
      <div className="receipt-head">
        <div><span className="eyebrow">Forecast receipt</span><h3>{forecast.forecast_id} · V{forecast.version}</h3></div>
        <StatusBadge status={p.integrity_status} />
      </div>
      <dl className="detail-list compact">
        <div><dt>Issue time</dt><dd>{date(p.issue_time)}</dd></div>
        <div><dt>Horizon</dt><dd>{forecast.horizon_hours} hours</dd></div>
        <div><dt>Weather source</dt><dd>{show(p.weather_source)}</dd></div>
        <div><dt>Weather run</dt><dd>{show(p.weather_run_id)}</dd></div>
        <div><dt>Available at</dt><dd>{date(p.forecast_available_time)}</dd></div>
        <div><dt>Model</dt><dd>{show(p.model_name)}</dd></div>
        <div><dt>Model version</dt><dd>{show(p.model_version)}</dd></div>
        <div><dt>Feature version</dt><dd>{show(p.feature_version)}</dd></div>
        <div><dt>Future observations</dt><dd>{p.future_information_used ? "YES" : "NO"}</dd></div>
      </dl>
    </article>
  );
}
