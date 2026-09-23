import { useI18n } from "../i18n/LanguageProvider";
export default function ConfidenceBadge({ value }) {
  const { t } = useI18n();
  return <span className="confidence-badge">{value ? t(value.toUpperCase()) : t("N/A")}</span>;
}
