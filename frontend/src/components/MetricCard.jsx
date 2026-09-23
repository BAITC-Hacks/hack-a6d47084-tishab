export default function MetricCard({ label, value, hint }) {
  return (
    <article className="metric-card">
      <span className="eyebrow">{label}</span>
      <strong>{value ?? "N/A"}</strong>
      {hint && <small>{hint}</small>}
    </article>
  );
}
