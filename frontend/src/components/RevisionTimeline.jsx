import { useI18n } from "../i18n/LanguageProvider";
import StatusBadge from "./StatusBadge";

export default function RevisionTimeline({ lineage = [], revision }) {
  const { t } = useI18n();
  if (!lineage.length) return <div className="empty-state">{t("No lineage supplied")}</div>;
  return (
    <article>
      <div className="section-title-row"><div><span className="eyebrow">{t("Forecast lineage")}</span><h3>{t("Compute → publish history")}</h3></div></div>
      <div className="version-flow">
        {lineage.map((item, index) => (
          <div className="version-node" key={`${item.forecast_id}-${item.version}`}>
            {index > 0 && <span className="version-arrow">→</span>}
            <div><strong>V{item.version}</strong><StatusBadge status={item.status} /><p>{t(item.revision_reason || "No reason supplied")}</p></div>
          </div>
        ))}
      </div>
      {revision && <p className="operator-message"><strong>{t(revision.decision)}</strong> — {t(revision.reason || "No reason supplied")}</p>}
    </article>
  );
}
