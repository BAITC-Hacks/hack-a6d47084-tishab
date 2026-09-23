import StatusBadge from "./StatusBadge";

export default function AgentTimeline({ agent, events = [] }) {
  return (
    <article>
      <div className="section-title-row">
        <div><span className="eyebrow">Supervisor activity</span><h3>{agent?.summary || "Agent result"}</h3></div>
        <StatusBadge status={agent?.status || "unavailable"} />
      </div>
      {agent?.operator_message && <p className="operator-message">{agent.operator_message}</p>}
      {events.length ? (
        <ol className="timeline">
          {events.map((event, index) => (
            <li key={`${event.timestamp}-${index}`} className={`event-${event.status}`}>
              <span className="timeline-dot" />
              <div><strong>{event.type.replaceAll("_", " ")}</strong><p>{event.message}</p><time>{new Date(event.timestamp).toLocaleTimeString()}</time></div>
            </li>
          ))}
        </ol>
      ) : <div className="empty-state">No agent events. Deterministic forecast remains available.</div>}
    </article>
  );
}
