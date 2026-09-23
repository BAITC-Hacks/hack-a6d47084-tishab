import { useI18n } from "../i18n/LanguageProvider";
import StatusBadge from "./StatusBadge";


export default function ForecastReceipt({ forecast }) {
  const { t, date } = useI18n();
  const show = (value) => value ?? t("N/A");
  const p = forecast.provenance;
  return (
    <article className="receipt-card">
      <div className="receipt-head">
        <div><span className="eyebrow">{t("Forecast receipt")}</span><h3>{forecast.forecast_id} · V{forecast.version}</h3></div>
        <StatusBadge status={p.integrity_status} label={p.integrity_status === "failed" ? t("BLOCKED") : undefined} />
      </div>
      <dl className="detail-list compact">
        <div><dt>{t("Issue time")}</dt><dd>{date(p.issue_time)}</dd></div>
        <div><dt>{t("Horizon")}</dt><dd>{t("{hours} hours", { hours: forecast.horizon_hours })}</dd></div>
        <div><dt>{t("Weather source")}</dt><dd>{t(show(p.weather_source))}</dd></div>
        <div><dt>{t("Weather run")}</dt><dd>{show(p.weather_run_id)}</dd></div>
        <div><dt>{t("Available at")}</dt><dd>{date(p.forecast_available_time)}</dd></div>
        <div><dt>{t("Model")}</dt><dd>{show(p.model_name)}</dd></div>
        <div><dt>{t("Model version")}</dt><dd>{show(p.model_version)}</dd></div>
        <div><dt>{t("Feature version")}</dt><dd>{show(p.feature_version)}</dd></div>
        <div><dt>{t("Future observations")}</dt><dd>{p.future_information_used ? t("YES") : t("NO")}</dd></div>
      </dl>
    </article>
  );
}
