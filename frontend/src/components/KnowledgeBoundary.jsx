import StatusBadge from "./StatusBadge";

function formatDate(value) {
  return value ? new Date(value).toLocaleString() : "N/A";
}

export default function KnowledgeBoundary({ boundary }) {
  if (!boundary) return <div className="empty-state">Knowledge-boundary result unavailable</div>;
  const failed = boundary.status === "failed";
  return (
    <article className={`boundary-card ${failed ? "danger" : "safe"}`}>
      <div className="section-title-row">
        <div>
          <span className="eyebrow">Knowledge boundary</span>
          <h3>{failed ? "Forecast rejected" : "Evidence is time-legal"}</h3>
        </div>
        <StatusBadge status={boundary.status} />
      </div>
      <dl className="detail-list">
        <div><dt>Issue time</dt><dd>{formatDate(boundary.issue_time)}</dd></div>
        <div><dt>Weather available</dt><dd>{formatDate(boundary.weather_available_time)}</dd></div>
        <div><dt>Future information</dt><dd>{boundary.future_information_used ? "YES" : "NO"}</dd></div>
      </dl>
      {boundary.reason && <p className="warning-text">{boundary.reason}</p>}
    </article>
  );
}
