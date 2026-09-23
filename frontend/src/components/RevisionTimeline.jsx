import StatusBadge from "./StatusBadge";

export default function RevisionTimeline({ lineage = [], revision }) {
  if (!lineage.length) return <div className="empty-state">No lineage supplied</div>;
  return (
    <article>
      <div className="section-title-row"><div><span className="eyebrow">Forecast lineage</span><h3>Compute → publish history</h3></div></div>
      <div className="version-flow">
        {lineage.map((item, index) => (
          <div className="version-node" key={`${item.forecast_id}-${item.version}`}>
            {index > 0 && <span className="version-arrow">→</span>}
            <div><strong>V{item.version}</strong><StatusBadge status={item.status} /><p>{item.revision_reason || "No reason supplied"}</p></div>
          </div>
        ))}
      </div>
      {revision && <p className="operator-message"><strong>{revision.decision}</strong> — {revision.reason || "No reason supplied"}</p>}
    </article>
  );
}
