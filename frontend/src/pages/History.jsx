import { Link } from "react-router-dom";
import StatusBadge from "../components/StatusBadge";
import { useForecast } from "../hooks/useForecast";

export default function History() {
  const { history, loading, error } = useForecast();
  return (
    <section>
      <div className="page-heading"><span className="eyebrow">Stored runs</span><h1>Forecast history</h1><p>Repeated historical replays persisted by the application layer.</p></div>
      <div className="panel table-panel">
        {loading && <div className="empty-state">Loading history…</div>}
        {error && <div className="empty-state">History unavailable: {error}</div>}
        {!loading && !history.length && <div className="empty-state">No stored forecasts yet.</div>}
        {!!history.length && <div className="table-scroll"><table><thead><tr><th>Forecast</th><th>Issue time</th><th>Horizon</th><th>Version</th><th>Status</th><th>Model</th><th>Integrity</th><th>Created</th></tr></thead><tbody>
          {history.map((run) => <tr key={run.forecast_id}><td><Link to={`/forecasts/${run.forecast_id}`}>{run.forecast_id}</Link></td><td>{new Date(run.issue_time).toLocaleString()}</td><td>{run.horizon_hours}h</td><td>V{run.version}</td><td><StatusBadge status={run.status} /></td><td>{run.model_name || "N/A"}</td><td><StatusBadge status={run.integrity_status} /></td><td>{new Date(run.created_at).toLocaleString()}</td></tr>)}
        </tbody></table></div>}
      </div>
    </section>
  );
}
