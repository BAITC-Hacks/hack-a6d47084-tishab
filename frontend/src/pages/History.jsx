import { useI18n } from "../i18n/LanguageProvider";
import { Link } from "react-router-dom";
import StatusBadge from "../components/StatusBadge";
import { useForecast } from "../hooks/useForecast";

export default function History() {
  const { t, date, errorText } = useI18n();
  const { history, loading, error } = useForecast();
  return (
    <section>
      <div className="page-heading"><span className="eyebrow">{t("Stored runs")}</span><h1>{t("Forecast history")}</h1><p>{t("Repeated historical replays persisted by the application layer.")}</p></div>
      <div className="panel table-panel">
        {loading && <div className="empty-state">{t("Loading history…")}</div>}
        {error && <div className="empty-state">{t("History unavailable:")} {errorText(error)}</div>}
        {!loading && !history.length && <div className="empty-state">{t("No stored forecasts yet.")}</div>}
        {!!history.length && <div className="table-scroll"><table><thead><tr><th>{t("Forecast")}</th><th>{t("Issue time")}</th><th>{t("Horizon")}</th><th>{t("Version")}</th><th>{t("Status")}</th><th>{t("Model")}</th><th>{t("Integrity")}</th><th>{t("Created")}</th></tr></thead><tbody>
          {history.map((run) => <tr key={run.forecast_id}><td><Link to={`/forecasts/${run.forecast_id}`}>{run.forecast_id}</Link></td><td>{date(run.issue_time)}</td><td>{t("{hours} hours", { hours: run.horizon_hours })}</td><td>V{run.version}</td><td><StatusBadge status={run.status} /></td><td>{run.model_name || t("N/A")}</td><td><StatusBadge status={run.integrity_status} /></td><td>{date(run.created_at)}</td></tr>)}
        </tbody></table></div>}
      </div>
    </section>
  );
}
