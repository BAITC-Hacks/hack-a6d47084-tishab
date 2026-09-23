import { useI18n } from "../i18n/LanguageProvider";
import StatusBadge from "./StatusBadge";


export default function KnowledgeBoundary({ boundary, isMock = false }) {
  const { t, date } = useI18n();
  if (!boundary) return <div className="empty-state">{t("Knowledge-boundary result unavailable")}</div>;
  const failed = boundary.status === "failed";
  return (
    <article className={`boundary-card ${failed ? "danger" : "safe"}`}>
      <div className="section-title-row">
        <div>
          <span className="eyebrow">{t("Knowledge boundary")}</span>
          <h3>{failed ? t(boundary.future_information_used ? "Future data blocked" : "Forecast blocked") : t("Evidence is time-legal")}</h3>
        </div>
        <StatusBadge status={boundary.status} label={failed ? t("BLOCKED") : undefined} />
      </div>
      {isMock && failed && <p className="helper-text">{t("Demo protection check: this rejection is intentional. Select ML + agent for a real forecast.")}</p>}
      <dl className="detail-list">
        <div><dt>{t("Issue time")}</dt><dd>{date(boundary.issue_time)}</dd></div>
        <div><dt>{t("Weather available")}</dt><dd>{date(boundary.weather_available_time)}</dd></div>
        <div><dt>{t("Future information")}</dt><dd>{boundary.future_information_used ? t("YES") : t("NO")}</dd></div>
      </dl>
      {boundary.reason && <p className="warning-text"><strong>{t("Safety rule triggered.")}</strong> {t(boundary.reason)}</p>}
    </article>
  );
}
