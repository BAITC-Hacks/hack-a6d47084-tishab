import { useI18n } from "../i18n/LanguageProvider";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";


export default function ForecastChart({ points }) {
  const { t, date, number } = useI18n();
  const data = points.map((point) => ({ ...point, label: date(point.forecast_time, { day: "2-digit", month: "short", hour: "2-digit" }) }));
  if (!data.length) return <div className="empty-state">{t("Forecast unavailable")}</div>;

  return (
    <div className="chart-wrap" aria-label={t("Forecast uncertainty chart")}>
      <ResponsiveContainer width="100%" height={360}>
        <ComposedChart data={data} margin={{ top: 14, right: 8, left: -18, bottom: 4 }}>
          <defs>
            <linearGradient id="uncertainty" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--chart-primary)" stopOpacity={0.35} />
              <stop offset="100%" stopColor="var(--chart-secondary)" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 7" vertical={false} />
          <XAxis dataKey="label" tick={{ fill: "var(--chart-label)", fontSize: 11 }} axisLine={false} tickLine={false} interval="preserveStartEnd" />
          <YAxis tickFormatter={number} domain={[0, "auto"]} tick={{ fill: "var(--chart-label)", fontSize: 11 }} axisLine={false} tickLine={false} />
          <Tooltip formatter={(value) => number(value)} contentStyle={{ borderRadius: 12, border: "1px solid var(--chart-border)", background: "var(--chart-tooltip)", color: "var(--chart-text)" }} />
          <Legend />
          <Area type="monotone" dataKey="p90" name="P90" stroke="none" fill="url(#uncertainty)" />
          <Area type="monotone" dataKey="p10" name="P10" stroke="var(--chart-muted)" fill="var(--chart-area)" fillOpacity={0.82} />
          <Line type="monotone" dataKey="p50" name="P50" stroke="var(--chart-primary)" strokeWidth={3} dot={false} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
