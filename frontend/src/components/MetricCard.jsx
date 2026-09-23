import { useI18n } from "../i18n/LanguageProvider";
export default function MetricCard({ label, value, hint }) {
  const { t } = useI18n();
  return (
    <article className="metric-card">
      <span className="eyebrow">{label}</span>
      <strong>{value ?? t("N/A")}</strong>
      {hint && <small>{hint}</small>}
    </article>
  );
}
