const LABELS = {
  pass: "PASS",
  failed: "FAILED",
  published: "PUBLISHED",
  rejected: "REJECTED",
  completed: "COMPLETED",
  unavailable: "UNAVAILABLE",
  computed: "COMPUTED",
  shadow: "SHADOW",
};

export default function StatusBadge({ status = "unknown" }) {
  const normalized = String(status).toLowerCase();
  return <span className={`status-badge status-${normalized}`}>{LABELS[normalized] || normalized.toUpperCase()}</span>;
}
