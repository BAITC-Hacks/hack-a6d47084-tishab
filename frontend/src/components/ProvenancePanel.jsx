import { useI18n } from "../i18n/LanguageProvider";
export default function ProvenancePanel({ provenance }) {
  const { t } = useI18n();
  if (!provenance) return null;
  return (
    <article>
      <span className="eyebrow">{t("Provenance")}</span>
      <h3>{t("Traceable forecast inputs")}</h3>
      <dl className="detail-list compact">
        <div><dt>{t("Forecast ID")}</dt><dd>{provenance.forecast_id}</dd></div>
        <div><dt>{t("Version")}</dt><dd>V{provenance.forecast_version}</dd></div>
        <div><dt>{t("Weather run")}</dt><dd>{provenance.weather_run_id || t("N/A")}</dd></div>
        <div><dt>{t("Weather source")}</dt><dd>{t(provenance.weather_source || "N/A")}</dd></div>
        <div><dt>{t("Model")}</dt><dd>{provenance.model_name || t("N/A")}</dd></div>
        <div><dt>{t("Model version")}</dt><dd>{provenance.model_version || t("N/A")}</dd></div>
        <div><dt>{t("Feature version")}</dt><dd>{provenance.feature_version || t("N/A")}</dd></div>
      </dl>
    </article>
  );
}
