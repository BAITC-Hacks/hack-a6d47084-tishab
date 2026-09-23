export default function ConfidenceBadge({ value }) {
  return <span className="confidence-badge">{value ? value.toUpperCase() : "N/A"}</span>;
}
