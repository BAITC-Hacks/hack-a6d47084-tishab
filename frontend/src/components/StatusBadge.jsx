import { useI18n } from "../i18n/LanguageProvider";
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

export default function StatusBadge({ status = "unknown", label }) {
  const { t } = useI18n();
  const normalized = String(status).toLowerCase();
  return <span className={`status-badge status-${normalized}`}>{label || t(LABELS[normalized] || normalized.toUpperCase())}</span>;
}
