import { useI18n } from "../i18n/LanguageProvider";
import StatusBadge from "./StatusBadge";

export default function AgentTimeline({ agent, events = [] }) {
  const { t, date } = useI18n();
  return (
    <article>
      <div className="section-title-row">
        <div><span className="eyebrow">{t("Supervisor activity")}</span><h3>{t(agent?.summary || "Agent result")}</h3></div>
        <StatusBadge status={agent?.status || "unavailable"} />
      </div>
      {agent?.operator_message && <p className="operator-message">{t(agent.operator_message)}</p>}
      {events.length ? (
        <ol className="timeline">
          {events.map((event, index) => (
            <li key={`${event.timestamp}-${index}`} className={`event-${event.status}`}>
              <span className="timeline-dot" />
              <div><strong>{t(event.type.replaceAll("_", " "))}</strong><p>{t(event.message)}</p><time>{date(event.timestamp, { hour: "2-digit", minute: "2-digit", second: "2-digit" })}</time></div>
            </li>
          ))}
        </ol>
      ) : <div className="empty-state">{t("No agent events. Deterministic forecast remains available.")}</div>}
    </article>
  );
}
