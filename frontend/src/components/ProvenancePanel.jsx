export default function ProvenancePanel({ provenance }) {
  if (!provenance) return null;
  return (
    <article>
      <span className="eyebrow">Provenance</span>
      <h3>Traceable forecast inputs</h3>
      <dl className="detail-list compact">
        <div><dt>Forecast ID</dt><dd>{provenance.forecast_id}</dd></div>
        <div><dt>Version</dt><dd>V{provenance.forecast_version}</dd></div>
        <div><dt>Weather run</dt><dd>{provenance.weather_run_id || "N/A"}</dd></div>
        <div><dt>Weather source</dt><dd>{provenance.weather_source || "N/A"}</dd></div>
        <div><dt>Model</dt><dd>{provenance.model_name || "N/A"}</dd></div>
        <div><dt>Model version</dt><dd>{provenance.model_version || "N/A"}</dd></div>
        <div><dt>Feature version</dt><dd>{provenance.feature_version || "N/A"}</dd></div>
      </dl>
    </article>
  );
}
